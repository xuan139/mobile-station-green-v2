# 舊綠能遙測與命令鏈盤點

日期：2026-09-05
執行方式：唯讀 Agent
範圍：只涵蓋 Green Power 與 Station Agent，排除 BXSJ

## 遙測鏈路

```text
Modbus FC2／FC3／FC4
→ Station Agent SQLite outbox
→ TCP JSON Line
→ Ingress
→ ms.raw.telemetry
→ Parser Worker
→ ms.parsed.telemetry
→ DB Writer
→ raw_message + telemetry_history + telemetry_current + station_runtime_status
```

Agent 依 YAML 輪詢，先寫入 SQLite outbox；Cloud 回覆 `status=ok` 後才刪除本地訊息。

## 命令鏈路

```text
API／mode schedule worker
→ station_command(pending, v2)
→ 下一筆 heartbeat／telemetry
→ Ingress claim 並放入 ACK
→ Agent FC6／FC16 寫入及 FC3 立即回讀
→ command_result 經 raw／parsed MQ
→ DB Writer 更新 station_command
→ mode worker 等待正常遙測回讀後完成模式目標
```

## 必須凍結的消息契約

- 上行 envelope：`message_id`、`station_id`、`station_name`、`device_id`、`protocol_type`、`protocol_version`、`message_type`、`group_name`、`sequence`、`collected_at`、`payload`。
- Green Power 遙測 payload：`function_code`、`address`、`count`；FC2 使用 `bits`，FC3／FC4 使用 `registers`。
- parsed MQ：`raw_message`、`parsed_payload`、`parse_status`、`parse_error`、`attempt`。
- ACK：`message_type=ack`、`status=ok`、`received_at`、`message_id`、`station_id`、`sequence` 及可選 `pending_command`。
- `pending_command`：command／station／device ID、command type、payload、expire、attempt、delivery version、lease。
- 上行 `command_result.protocol_version=v1` 與命令投遞 V2 是不同版本軸，不得混用。
- `WRITE_OK` 只代表 Modbus 寫入回應與立即 FC3 回讀吻合；模式切換還需後續正常遙測一致。

## 現行可靠性邊界

- Publisher 使用 durable queue 與 persistent message，但沒有 publisher confirm；Cloud ACK 不能嚴格證明 broker 已持久確認。
- Parser 發布 parsed 後 ACK raw；DB Writer commit 後 ACK parsed，整體為 at-least-once。
- Agent 未核對 Cloud ACK 的 message／station／sequence correlation。
- Agent 達 drop 次數後把訊息標記為 dead，資料可能不再補傳。
- V2 命令租約預設 60 秒、最多三次；已有 journal 時會重送原結果，不再寫設備。
- 設備寫成功與 journal 寫入之間仍有崩潰窗口，現況不能宣稱 crash-safe exactly-once。
- Cloud 套用 command result 時只按 command ID 更新，未充分驗證 station／device／command type 所屬關係。
- Ingress 是未認證明文 TCP，屬 V2 必須重建的信任邊界。
- 解析失敗流向 failed queue／alert notify，不一定寫入 raw_message failed 狀態。

## V2 模組邊界

- `contracts`：唯一 envelope、ACK、pending command、command result schema。
- `station_agent`：profile／codec、Modbus gateway、telemetry poller、durable outbox、command journal／executor、uplink client。
- `ingestion`：認證連線與 raw publish。
- `parser`：純函式解析，不負責 DB 與設備 I/O。
- `application/commands`：create／claim／result ownership、信任驗證與冪等規則。
- `workers/db_writer`：只做單一交易編排。
- `workers/command_lifecycle`：租約、重投、過期與終態治理。

## 模擬器最低能力

1. 支援可變 holding register、FC3、FC6、FC16、立即與延遲回讀。
2. 持久記錄設備寫入次數，可斷言同一 command 只造成一次設備寫入。
3. 可注入 raw publish 後丟 ACK、claim 後斷線、設備寫後崩潰、result publish 後丟 ACK。
4. 可控時鐘，避免實際等待 lease、TTL 與退避。
5. 以真 PostgreSQL／RabbitMQ 跑整合鏈，不使用舊 local bypass。

## 第一條縱向鏈路驗收

1. FC4 `0x1E0` 上行後，raw、history、current 與來源 message ID 正確。
2. 丟失第一次 ACK 後重送相同訊息，不新增重複 raw/history。
3. 建立具冪等鍵、期限及 V2 標記的 `FC3 0x001=1` 命令並取得同一 command ID。
4. 模擬器 FC6 寫入次數為一，Cloud 終態與時間欄位一致。
5. 丟失 command-result ACK 及租約重投時只重送結果，不再次寫設備。
6. 後續 control schedule 遙測為模式 1 後，模式 target 才完成。
7. 偽造跨站結果、錯誤 ACK correlation 與過期命令均應拒絕並可稽核。
8. 設備寫後、journal 前崩潰測試必須先失敗再修正，通過後才能標記可靠投遞完成。

## 主要證據

- Agent 主循環：`implementation_examples/station_modbus_bridge_simulator.py:1905`
- Agent 命令：同檔 `:1563`、`:1625`
- Ingress：`cloud/services/ingress/main.py:91`、`:104`
- Parser：`cloud/common/parser.py:19`、`:626`
- DB Writer：`cloud/services/db_writer/main.py:37`
- 命令 claim：`cloud/common/db.py:926`

