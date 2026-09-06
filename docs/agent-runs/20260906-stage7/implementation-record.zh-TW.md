# Green V2 第七階段：逐筆 DB Writer 相容鏈路

## 範圍

- 日期：2026-09-06
- 工作樹：`/private/tmp/mobile-station-green-v2-stage5-7`
- 分支：`codex/green-v2-stage5-7`
- 前置 commit：`3760cc8`
- 舊版唯讀來源：`origin/dev@23b8274a2a708f9b8d4de2a8c46df2dc541bca6d`

本階段只實作 Green V2 遙測逐筆入庫，不搬移告警、命令、模式排程、能源或
歷史彙總業務，也不進行真正批次消費。舊綠能、BXSJ、AWS、正式資料庫、正式
RabbitMQ 與設備均未連線或修改。

## 完成內容

```text
green_v2.parsed.telemetry
  -> DbWriterRunner
  -> PersistParsedTelemetry
  -> PostgresTelemetryUnitOfWork
  -> raw_message / station_runtime_status
  -> telemetry_history / telemetry_current
  -> PostgreSQL commit
  -> RabbitMQ ACK
```

- PostgreSQL pool、Unit of Work 與 telemetry repository 分檔實作。
- application layer 明確控制 raw、runtime、history、current 的同一交易。
- raw 以 `message_id` 與 `(station_id, sequence)` 保持舊版冪等語意。
- 重送訊息若 raw 已存在，不再重複寫入 history 或 current。
- current 僅允許相同或較新的 `collected_at` 覆蓋；較舊訊息仍保留 history。
- PostgreSQL commit 成功後才 ACK；入庫失敗先重發 parsed queue，超過 3 次
  改送 `green_v2.dlq`，重發失敗則 NACK 原 delivery 並 requeue。
- 新增可追蹤 migration runner，已套用版本保存 SHA-256，內容被竄改時拒絕
  繼續執行。
- DB Writer 執行入口：`python -m green_v2.workers.db_writer.main`。

## Migration

向前檔案：`migrations/0001_telemetry_core.sql`

建立與舊版相同的核心欄位、限制及綠能相關索引：

- `raw_message`
- `station_runtime_status`
- `telemetry_current`
- `telemetry_history` 與 default partition

手動回退檔案：`migrations/rollback/0001_telemetry_core.sql`。回退會刪除上述 V2
表與資料，只允許在已確認的隔離 V2 資料庫執行；正式環境若已有資料，必須先
備份並改採向前修復，不得直接執行破壞性回退。Runtime 不會自動套 migration，
部署者必須先獨立執行並核對結果。

## 驗證結果

- 全量測試：`67 passed`
- 最終測試資料庫：本機臨時 `mobile_station_green_v2_test_stage7c`
- migration 首次套用：1 筆；第二次重跑：0 筆
- 舊的 `stage7b` migration checksum 與最終檔案不同時，runner 如預期拒絕執行
- 3 個唯一 raw 訊息加 1 次重送：raw 3 筆，沒有重複資料
- 每訊息 21 個 metric：history 63 筆，current 21 筆
- 最新值保持 221.0；較舊訊息 219.0 未覆蓋 current
- runtime 保持最新 message，同時保留最大 sequence；lag 計算正確
- 負數 backlog 觸發 constraint 時，已確認 raw insert 也一併 rollback
- ACK／retry／DLQ／retry publish failure 的順序測試：全部通過
- 程式碼結構限制及 `git diff --check`：通過
- 測試完成後，臨時 PostgreSQL 已正常停止，沒有留下背景服務

本機沒有 RabbitMQ Server，因此 durable queue、persistent publish、manual
ACK/prefetch 與 generation guard 仍為 mock 測試，尚未完成 `/green-v2` live
broker 驗證。沒有建立 systemd unit、部署包或 AWS 發布。

## 回退

第七階段使用獨立 commit。程式回退使用 `git revert` 該 commit；若只在空的
隔離 V2 測試庫回退 schema，可人工執行 rollback SQL。第五、六階段各自保留
獨立 commit，不會因第七階段回退而消失。

## 下一階段

先以本階段逐筆版本作相容基準，再另開提交實作真正批次消費。批次版本必須
補上全批 commit 後 ACK、資料錯誤隔離、broker 中斷與 throughput/transaction
數量對照，不能直接修改本階段已驗證的交易語意。
