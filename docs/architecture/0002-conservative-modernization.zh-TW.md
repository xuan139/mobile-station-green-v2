# ADR-0002：保守技術棧與相容優化原則

日期：2026-09-05  
狀態：已接受

## 背景

Green V2 的目標是完整復刻並改善舊綠能系統，而不是以新技術重新定義產品。
舊系統的主要風險來自責任混合、檔案與函式過大、執行期 DDL、部署清單漂移，
以及缺乏足以證明新舊行為一致的契約測試。

## 決策

1. 保留 Python 3.12、PostgreSQL、RabbitMQ、`psycopg`、`pika`、systemd、
   cron、Shell、YAML、Modbus 及 Station Agent SQLite Outbox。
2. 不導入新的資料庫、ORM、Celery、Kafka、Kubernetes、事件溯源或分散式交易框架。
3. 保留既有 API、MQ、資料庫、Worker、cron 與部署契約；內部只做模組化、
   責任切分、型別化及測試補強。
4. 採模組化單體與多程序入口。每個 systemd 服務維持獨立程序，但共用經過明確
   邊界管理的 domain、application、data access 與 messaging 模組。
5. 目前 V2 骨架已使用 FastAPI。FastAPI 暫時只作 HTTP Adapter，不得進入
   application 或 domain。正式搬移 V1 路由前必須通過 golden contract tests；
   若無法維持舊契約，可只替換 HTTP Adapter，不影響核心模組。
6. 不在結構搬移的同一提交改變業務行為。功能修正與效能改善必須獨立提交、
   獨立測試及獨立回退。

## DB Writer 決策

舊版已有 `DB_WRITER_BATCH_SIZE` 與 `DB_WRITER_BATCH_SECONDS`，但執行時仍逐筆
呼叫批次寫入函式。V2 將分兩步處理：

1. 先完整復刻逐筆消費、資料庫 commit 後 ACK、重試與 DLQ 語意。
2. 再以獨立變更實作真正批次消費，批次 commit 成功後才 ACK；發生失敗時必須
   能定位失敗訊息，並保持至少一次投遞與既有去重結果。

批次化不得與資料模型搬移、Parser 改寫或 MQ Topology 調整混在同一提交。

## 程式碼限制

- 一般 Python 模組目標不超過 500 行，硬性上限 600 行。
- 一般函式目標不超過 40 行，超過 60 行必須審查，硬性上限 80 行。
- 類別硬性上限 300 行。
- 程序入口只負責設定、組合依賴、啟停與健康檢查。
- 不建立新的 `db.py`、`utils.py`、`helpers.py` 或 `misc.py` 通用集中檔案。
- domain 不得依賴 FastAPI、PostgreSQL、RabbitMQ、設備驅動或外部 I/O。
- API、Worker、Ingress 與 Station Agent 不得越過 application 直接存取資料庫或 MQ。

上述硬性限制由 `tests/test_code_structure.py` 自動檢查。純宣告資料若確實無法拆分，
必須先建立 ADR 說明理由，再加入明確檔案級例外，不允許使用全域排除。

## 回退

本決策只影響 Green V2。每一批結構搬移與行為修正均使用獨立提交；若驗證失敗，
以 `git revert` 回退該批次。舊綠能程式與正式環境不因本決策而變更。
