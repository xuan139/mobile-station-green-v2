# 舊綠能資料庫與 Data Access 盤點

日期：2026-09-05
執行方式：唯讀 Agent
舊程式基準：`/Users/lijiaxi/Documents/mobile station`，分支 `dev`，HEAD `25572ae`

## 現行資料域

- 採集與站台狀態：`raw_message`、`station_runtime_status`。
- 遙測時序：`telemetry_current`、分區 `telemetry_history`、`5m/15m/1h` 摘要與 watermark。
- 站台主檔：站台、轄區／中心階層、Excel 匯入對照、SIM 與設備 endpoint。
- 命令與排程：`station_command`、排程模板、季節模式 schedule／execution／target。
- 告警：規則、override、延遲 pending、active state、event、notification、需量超約生命週期。
- 綠能計算：電價、累加狀態、每分鐘快照與每日移轉效益。
- IAM 與 Log：使用者、角色、權限、scope、Session、Audit、System Log。
- 查詢模型：點位目錄與跨遙測、能源、效益、告警的總覽 read model。

## 現有拆分狀態

Data Access 已有 `core`、`green_energy`、`access_control`、`point_catalog`、
`station_directory`、`alarm_records`、`mode_schedule`、
`station_command_lifecycle`、`station_overview` 九個實作模組。

`core.py` 以完整 DSN 為 key 建立每程序 pool，預設 `min=1/max=15`；
`cloud/common/db.py` 仍是相容 facade，且仍含遙測寫入、告警評估、命令建立／領取、
告警設定、排程模板、歷史查詢及單站 snapshot 等大型責任。

## 最小相容範圍

完整功能相容至少涉及約 44 張作用中資料表及其 PK、FK、CHECK、唯一／部分索引、
分區與 trigger。歷史備份表不屬於 V2 執行期最小 schema。V2 不應直接複製現況，
而應先建立可重播的 migration ledger 與 schema fingerprint。

## 交易與冪等語意

- DB Writer 先 commit 再 ACK MQ，屬 at-least-once。
- `raw_message.message_id` 與 `(station_id, sequence)` 負責上行去重。
- raw、命令結果、runtime、alarm、history、current 在同一批次交易；current 拒絕較舊採集時間。
- 命令建立以 `idempotency_key` 唯一；claim 使用 `FOR UPDATE SKIP LOCKED`。
- lifecycle 的命令過期與 System Log 位於同一交易。
- rollup 以 advisory transaction lock 保護 chunk，摘要與 watermark 原子提交。
- 一般 API 業務更新與 Audit、自動模式 execution／command／target／Log 仍有跨交易中斷窗口。

## 不可共用資源

- 舊正式庫、V2 本地／測試庫不得共用 database、schema、帳號、pool、備份或憑證。
- Pool 必須每程序獨立並受總量預算約束；舊系統九個服務若皆達 max 15，理論值約 135 條連線。
- Shadow 驗證不得競爭消費正式 MQ queue，應使用事件複本或資料快照。
- 舊版與 V2 不得同時寫同一告警 state、energy accumulator 或 mode target。
- 搬遷時不得重建 message ID、sequence、alarm state key、command ID／idempotency key 或 execution 唯一鍵。

## 主要風險

1. 部分 permission、system log、outbox、station/user/benefit schema 由 Python 執行期 DDL 補建，基準 SQL 不完整。
2. 缺少正式 migration ledger；既有測試可能掩蓋 schema drift。
3. 自動模式 command 與 target 綁定、completion 與 Log 之間存在中斷窗口。
4. 多 Worker 併行可能導致告警、energy 或 mode target 競態。
5. 指南、實際 import 邊界與契約測試已有漂移。

## V2 驗收要求

- 空庫 migration 與舊版逐版 migration 的 schema fingerprint 相同。
- 使用 DML-only 帳號通過全功能測試，證明 runtime 不依賴 DDL 權限。
- 補齊多 Worker、重複 MQ、交易中斷、command-target-log 故障注入。
- 比對 raw/history/current、active alarm、需量事件、command 終態、rollup sample count 與 watermark。
- 以相同帳號、站台、時間窗比對舊版與 V2 API 結構、值、排序、權限及持續入庫。

## 主要證據

- schema：`cloud/db/cloud_schema_v1.sql:9`、`:171`、`:299`、`:319`、`:447`
- pool：`cloud/data_access/core.py:14`
- DB Writer：`cloud/services/db_writer/main.py:69`
- 交易編排：`cloud/common/db.py:1729`、`:1967`
- lifecycle：`cloud/data_access/station_command_lifecycle.py:57`
- 整合測試：`tests/test_db_integration.py:19`、`:59`、`:662`

