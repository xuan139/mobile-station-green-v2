# 契約目錄

本目錄保存新舊系統一致性所需的可版本化契約：

- `openapi/`：WPF 與外部呼叫的 HTTP 契約。
- `mq/`：上行、解析、失敗及命令訊息 JSON Schema。
- `telemetry/`：點位、單位、資料型別及狀態語意。
- `database/`：資料表、欄位、約束、索引及相容性清單。
- `deployment/`：systemd 與 cron 的離線來源清單。
- `source/`：參與相容性比對的舊版來源檔 SHA-256。

契約在業務編碼前由總協調 Agent 凍結。現階段尚未聲稱與舊系統完全一致。

第三階段的來源指紋可用下列命令重建；`legacy-root` 必須是已固定 commit
的離線唯讀快照，不得直接使用正式主機：

```bash
python tools/capture_legacy_source_contracts.py \
  --legacy-root /path/to/legacy-snapshot \
  --output-root . \
  --source-commit <commit> \
  --archive-sha256 <sha256>
```

`source-schema-manifest.json` 只描述來源 DDL。它不能取代 AWS PostgreSQL
實際 schema fingerprint，也不能作為已完成資料庫相容驗收的證明。
