# 綠能 V2 階段 0／1 實作記錄

日期：2026-09-05
狀態：本機隔離骨架已建立並通過健康契約測試

## 目標

以多 Agent 唯讀盤點舊綠能，建立完全隔離、可刪除回退的綠能 V2 可執行骨架，
並建立獨立 BXSJ V2 空倉庫與隔離規則。

## 已確認舊環境

- 舊倉庫：`/Users/lijiaxi/Documents/mobile station`
- 舊分支：`dev`
- 舊工作區原本已有未提交內容，本次不修改、不整理、不提交。
- 舊 `dev` 相對 `origin/dev` 為 ahead 1、behind 2，本次不處理該分歧。
- 已完整閱讀目前確認狀態、最新需求索引及 DB 拆分部署與開發規範。

## 新環境邊界

- Green V2：`/Users/lijiaxi/Documents/mobile-station-green-v2`
- BXSJ V2：`/Users/lijiaxi/Documents/mobile-station-bxsj-v2`
- Green V2 DB：`mobile_station_green_v2`
- Green V2 MQ vhost：`/green-v2`
- Green V2 API／Ingress：`28000`／`29000`
- 不連線 AWS、生產資料庫、生產 MQ 或真實設備。
- 建立 GitHub repository 前先報告登入帳號、名稱、可見性及命令並等待確認。

## 本階段不代表

- 不代表已完成舊系統功能相容。
- 不代表已完成資料庫 schema 相容。
- 不代表已完成 WPF 驗收。
- 不代表已部署或完成生產業務驗證。

## 多 Agent 唯讀盤點

已完成四個互不重疊的舊系統盤點，原始結論整理於同目錄：

- `api-contract-analysis.zh-TW.md`
- `database-analysis.zh-TW.md`
- `telemetry-command-analysis.zh-TW.md`
- `test-deployment-analysis.zh-TW.md`

盤點確認 V2 第一個業務批次前必須先建立：V1 golden API 契約、可重播 migration
ledger、具可控故障點的 Modbus／MQ 模擬器、命令 correlation 與冪等測試，以及
完全隔離的一次性整合測試環境。

## 已建立骨架

- FastAPI application factory 及 `/health`、`/ready`、`/api/v1/ping` 三項健康契約。
- domain、application、api、data access、messaging、ingestion、parser、station agent 與五類 worker 邊界。
- DB、MQ、API、Ingress 隔離設定及舊資源拒絕檢查。
- PostgreSQL 16 與 RabbitMQ 3.13 的本地隔離 Compose 定義。
- 七個專用 Agent 設定、契約目錄、migration 目錄、模擬器目錄及初始測試。
- 獨立 BXSJ V2 空骨架與禁止相互 import 的測試。

## 目前驗證

- Green V2 `src/` 與 `tests/` Python compile：通過。
- BXSJ V2 隔離測試：2／2 通過。
- Green V2 FastAPI／設定／隔離測試：8／8 通過，另有兩個第三方棄用警告。
- Green V2 `/health`、`/ready`、`/api/v1/ping` smoke test：3／3 通過。
- 本機 FastAPI 開發服務使用 `127.0.0.1:28000`，未占用舊系統埠。
- 這台 Mac 未安裝 Docker，因此 Compose 尚未做語法驗證或啟動。
- 未啟動 Docker、未連接任何舊或正式資料資源。

詳細環境、套件版本、輸出及未執行項目見 `local-verification.zh-TW.md`。
