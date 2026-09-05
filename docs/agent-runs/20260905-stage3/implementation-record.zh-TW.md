# Green V2 第三階段：舊版來源契約擷取紀錄

## 執行範圍

- 日期：2026-09-05
- V2 工作樹：`/private/tmp/mobile-station-green-v2-contract-capture`
- V2 分支：`codex/green-v2-contract-capture`
- 舊版來源：`origin/dev`
- 舊版 commit：`23b8274a2a708f9b8d4de2a8c46df2dc541bca6d`
- 舊版離線 archive SHA-256：
  `0acfc9eeca10efb09eff70bb8e3731107afd96eb34a8ccda6e2ba8bc5a6bb91d`

本階段只讀取由 `git archive` 建立的離線舊版快照。沒有修改舊綠能、沒有處理
其他系統程式、沒有連線 AWS、PostgreSQL、RabbitMQ 或站臺設備，也沒有部署。

## 本階段產物

1. 建立 API v1 路由清單，保留 `/api/v1` 與 `/v1` 雙前綴。
2. 建立綠能遙測 raw、parsed，以及 ingress ACK／命令租約範例。
3. 建立可重複執行的舊版來源擷取工具。
4. 產生靜態 SQL、Python runtime DDL、systemd、cron 與關鍵來源檔 SHA-256 清單。
5. 新增契約完整性測試，避免後續模組化時無意改變外部行為。

## 已知限制

- API 路由清單是依固定 commit 程式碼整理的來源契約，尚未對 AWS 實際 API 回應做 replay。
- 資料庫清單只反映來源 DDL，尚未取得 AWS PostgreSQL 的唯讀 schema fingerprint。
- systemd 清單保留兩套來源範本及其差異；尚未把任一範本宣稱為正式主機現況。
- RabbitMQ queue、durability 與 ACK 語意來自固定來源，尚未讀取正式 broker topology。
- 此階段沒有改寫 API、DB、MQ、Worker、cron 或 DB Writer 執行邏輯。

## 本機驗證結果

- 全部測試：`19 passed`
- Python 編譯檢查：通過
- `git diff --check`：通過
- 來源擷取工具連續執行兩次，產物整體 SHA-256 相同
- 合約目錄未包含非綠能服務來源
- FastAPI／Starlette 測試相依套件出現 2 個棄用警告；屬既有相依版本警告，
  不影響本階段測試結果，亦未在本階段升級套件

## 回退方式

本階段會以單一 Git commit 整合到 V2 `dev`。需要回退時只 revert 該 commit；
舊綠能與正式環境未被修改，不需執行伺服器或資料庫回復。
