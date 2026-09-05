# Green V2 第四階段：遙測最小垂直流程

## 執行範圍

- 日期：2026-09-06
- 工作樹：`/private/tmp/mobile-station-green-v2-telemetry-slice`
- 分支：`codex/green-v2-telemetry-slice`
- 基準 commit：`502d1c0`
- 舊版唯讀來源：`origin/dev@23b8274a2a708f9b8d4de2a8c46df2dc541bca6d`

本階段只修改 Green V2。沒有修改舊綠能，沒有連線 AWS、PostgreSQL、
RabbitMQ 或站臺設備，也沒有 push 或部署。

## 已實作流程

```text
JSON Line
  -> IngestTelemetry 驗證與正規化
  -> publish raw telemetry
  -> 回覆 ingress ACK
  -> ParseTelemetry 解析 FC4 0x1E0
  -> publish parsed telemetry
  -> ACK raw delivery
```

失敗路徑保持舊版核心語意：

- JSON 或訊息驗證失敗：回覆 `reject`，不發布 raw 訊息。
- 解析失敗：先發布 failed envelope，成功後才 ACK 原始 delivery。
- parsed／failed 發布失敗：NACK 原始 delivery 並要求 requeue。
- raw 發布成功後才查詢待下發命令，命令查詢可由後續 command application adapter 注入。

## 模組責任

- `domain/telemetry_message.py`：綠能 telemetry envelope 正規化與驗證。
- `domain/ack_message.py`：保持 ingress ACK 欄位契約。
- `parser/register_values.py`：16／32／64 位元寄存器解碼。
- `parser/main_status.py`：FC4 `0x1E0` 主狀態點位映射。
- `parser/green_power.py`：綠能 parser 分派與 legacy output envelope。
- `application/ingest_telemetry.py`：raw 發布與待下發命令查詢順序。
- `application/parse_telemetry.py`：parsed／failed 發布及 ACK／NACK 時序。
- `ingestion/json_line.py`：JSON Line transport adapter。
- `messaging/ports.py`：application 使用的發布與確認介面。
- `messaging/memory.py`：隔離整合測試用 broker。
- `messaging/rabbitmq.py`：durable queue、persistent message 的 `pika` adapter。

## 本機驗證

- 全部測試：`30 passed`
- frozen legacy FC4 `0x1E0` parsed payload 比對：通過
- 固定輸入分別執行舊版 parser 與 V2 parser，正規化 JSON 結果完全相同
- ingress -> raw -> parser -> parsed -> ACK 完整流程：通過
- failed publish -> NACK／requeue：通過
- RabbitMQ durable queue 與 delivery mode 2：mock 驗證通過
- 程式碼結構限制：通過

## 尚未完成

- 尚未搬移其他綠能 pack、alarm bits、controller bits 與 control schedule 點位。
- 尚未建立正式 TCP server loop、RabbitMQ consumer loop、健康檢查與 systemd unit。
- RabbitMQ adapter 尚未對 V2 `/green-v2` broker 進行連線測試。
- 尚未接 DB Writer、PostgreSQL transaction 或資料去重。
- 尚未執行 AWS 或真實設備相容驗收。

## 回退

本階段以單一 commit 整合回 V2 `dev`。若驗證失敗，以 `git revert` 回退該
整合 commit；舊綠能與正式環境未被修改，不需要伺服器或資料庫回復。
