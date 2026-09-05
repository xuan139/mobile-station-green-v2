# 舊綠能至 Green V2 模組化搬移計畫

日期：2026-09-05  
狀態：第一階段執行基準

## 目標

在不改變舊綠能對外功能、資料庫、MQ、Worker、API、cron 與 AWS 部署方式的前提下，
將大型檔案依業務責任拆開，並建立能證明新舊結果一致的自動化測試。

## 模組邊界

| 領域 | 主要責任 | 禁止混入 |
|---|---|---|
| telemetry | raw、parse、history、current、runtime | API 格式、權限、命令 |
| stations | 站台主檔、設備 endpoint、目錄與狀態 | 告警規則、能源計算 |
| alarms | 規則、active state、event、notification、需量事件 | HTTP、MQ Consumer Loop |
| commands | 建立、claim、結果、租約、過期與狀態機 | Modbus 實作、UI 字串 |
| schedules | 模式規則、execution、target、回讀完成 | SQL 連線管理 |
| energy | 累加器、電價、效益與每日結果 | API 驗證、Station Agent |
| identity | 登入、Session、使用者、角色、權限與 scope | 站台遙測 SQL |
| audit | Audit、System Log、Log Center | 登入密碼驗證 |
| history | 5m、15m、1h、watermark、查詢來源選擇 | API 路由分派 |

## 大型檔案拆分對照

### `cloud/common/db.py`

不複製成新的大型 facade。依序搬到下列模組：

- `data_access/telemetry_repository.py`
- `data_access/station_repository.py`
- `data_access/station_runtime_repository.py`
- `data_access/overview_queries.py`
- `data_access/history_repository.py`
- `data_access/alarm_repository.py`
- `data_access/demand_event_repository.py`
- `data_access/command_repository.py`
- `data_access/schedule_repository.py`
- `data_access/energy_repository.py`

交易流程放在 `application` Use Case，Repository 只負責 SQL 與資料映射。

### `cloud/data_access/access_control.py`

拆為 `identity/authentication.py`、`identity/session_repository.py`、
`identity/user_repository.py`、`identity/role_repository.py`、
`identity/permission_policy.py`、`audit/audit_repository.py` 與
`audit/system_log_repository.py`。

### `cloud/services/api/main.py`

拆為 `api/v1` 下的 auth、stations、telemetry、overview、alarms、commands、
schedules、energy、history、identity、audit 與 operations Router。Router 不含 SQL，
不自行處理跨表交易，也不保存大型業務規則。

### Station Agent

拆為設定載入、Modbus Client、遙測 Poller、SQLite Outbox、Uplink Client、
Command Journal、Command Executor 與程序入口。YAML、TCP envelope、sequence、
ACK 與命令行為保持相容。

### 歷史彙總 cron

保留既有命令名稱與 mode 參數。Shell 只負責環境、鎖與呼叫；5m、15m、1h、
prune SQL 分檔保存，由同一個小型 Runner 執行。

## 垂直搬移順序

1. 凍結來源 Commit、DB Schema、MQ Topology、API、systemd 與 cron 契約。
2. 建立設定、連線池、MQ Client、Logging、Health 與 Unit of Work。
3. 搬移 Ingress、Parser、DB Writer 的遙測最小鏈路。
4. 搬移站台主檔、runtime、snapshot 與總覽查詢。
5. 搬移告警規則、告警事件、需量事件與通知。
6. 搬移使用者、角色、權限、Session、Audit 與 System Log。
7. 搬移命令建立、claim、result 與 lifecycle 狀態機。
8. 搬移模式排程、execution、target 與遙測回讀。
9. 搬移能源累加、電價與效益。
10. 搬移歷史查詢及 5m、15m、1h、prune cron。
11. 完成 Station Agent 模組化及故障注入測試。
12. 完成隔離回放、AWS 演練、切換與回退驗證。

每一步至少分成「純搬移」與「行為改善」兩個提交。前一步未通過新舊比較，
不得開始下一個領域。

## DB Writer 批次改善

批次改善排在遙測鏈路完全相容之後：

1. Consumer 在 `batch_seconds` 內最多收集 `batch_size` 筆訊息。
2. Repository 使用一個 Unit of Work 寫入整批資料。
3. 全批 commit 成功後才逐筆 ACK，不能使用跨未知 delivery gap 的盲目 multiple ACK。
4. 可重試錯誤整批 NACK／重送；資料錯誤以二分定位或逐筆隔離，保留 DLQ 行為。
5. 以 message ID 與 `(station_id, sequence)` 驗證重送不產生重複資料。
6. 壓測比較每秒入庫量、交易次數、Queue 深度、延遲及資料庫連線占用。

第一版不加入非必要的非同步資料庫驅動，避免同時改變 Worker 模型與批次語意。

## 完成定義

- 所有硬性程式碼限制測試通過。
- 相同輸入的新舊 API、DB、MQ 與 Worker 結果一致。
- 動態時間、UUID 等欄位正規化後，golden response 無非預期差異。
- 空庫 migration 與既有 schema 升級結果具有相同 fingerprint。
- MQ 重送、Worker 中止、DB commit 失敗及 Agent 重啟不造成重複業務資料。
- cron 重跑結果相同，摘要筆數與 `sample_count` 守恆。
- 每個部署包對應乾淨 Git Commit、SHA-256、備份及回退紀錄。
