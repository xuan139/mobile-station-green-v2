# Green V2 第一階段相容優化執行紀錄

日期：2026-09-05  
分支：`codex/green-v2-contract-baseline`  
Worktree：`/tmp/mobile-station-green-v2-contract-baseline`

## 本階段目標

在不搬移業務程式、不改變外部系統及不引入新技術棧的前提下，先固定 Green V2
的保守優化方向、舊版相容基準與可執行程式碼結構限制。

## 完成項目

1. 新增 ADR-0002，確認保留 Python、PostgreSQL、RabbitMQ、systemd、cron、
   Shell、YAML、Modbus 及 SQLite Outbox。
2. 建立舊版相容基準，記錄 API、MQ、資料庫、九個綠能 systemd 服務及 cron
   的最低相容要求。
3. 建立大型檔案拆分對照與十二階段垂直搬移順序。
4. 新增 AST 結構測試，限制模組、函式與類別大小，並驗證架構依賴方向。
5. 將專案說明中的「隔離重寫」修正為「相容優化」，避免誤解專案目標。

## DB Writer 決議

第一個遙測版本先保持舊版逐筆消費與 commit 後 ACK 語意。真正批次消費列為
後續獨立提交，必須通過重送、去重、交易失敗、DLQ 與壓力測試後才能啟用。

## 驗證結果

執行命令：

```bash
/Users/lijiaxi/Documents/mobile-station-green-v2/.venv/bin/python -m pytest
/Users/lijiaxi/Documents/mobile-station-green-v2/.venv/bin/python -m compileall -q src tests
git diff --check
```

結果：

- Pytest：`13 passed`
- 既有相依套件警告：2 項，不是本次變更造成
- Python compileall：通過
- Git whitespace check：通過

## 未執行事項

- 未修改舊綠能程式。
- 未連線正式資料庫、RabbitMQ、AWS 或真實設備。
- 未搬移任何正式業務功能。
- 未實作 DB Writer 真正批次化。
- 尚未確認 AWS 實際部署 Commit 與資料庫 Schema fingerprint。

## 回退

本階段尚未合併至 `dev`。需要放棄時可移除本 worktree 與
`codex/green-v2-contract-baseline` 分支；舊綠能及 Green V2 `dev` 均不受影響。
