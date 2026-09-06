# 綠能 V2

本專案是與現有綠能系統完全隔離的相容優化版本。目標是在維持既有功能、
資料庫、MQ、Worker、API、cron 與部署方式的前提下，改善程式結構、可讀性、
可測試性與維護性。現階段只建立可執行骨架、相容契約、環境隔離、測試與
多 Agent 治理。現階段已完成綠能遙測的 Ingress、Parser 與逐筆 DB Writer
相容鏈路；其他業務領域仍依搬移計畫逐階段實作。

## 安全邊界

- 舊綠能只讀參考，不修改既有程式、GitHub、AWS、資料庫、MQ 或設備。
- 本地資料庫固定使用 `mobile_station_green_v2`。
- RabbitMQ vhost 固定使用 `/green-v2`。
- API 與 Ingress 預設使用 `28000` 與 `29000`。
- BXSJ／鈉鹽位於另一個獨立倉庫，本專案不包含其程式碼。

## 本地啟動

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/uvicorn green_v2.api.app:app --app-dir src --host 127.0.0.1 --port 28000
```

健康檢查：

```bash
curl http://127.0.0.1:28000/health
curl http://127.0.0.1:28000/ready
curl http://127.0.0.1:28000/api/v1/ping
```

執行測試：

```bash
.venv/bin/python -m pytest
```

啟動隔離 PostgreSQL 與 RabbitMQ：

```bash
docker compose up -d postgres rabbitmq
```

首次啟動或 migration 變更後，先套用 V2 migration：

```bash
PYTHONPATH=src .venv/bin/python -m green_v2.data_access.migration_main
```

分別啟動遙測鏈路的三個程序：

```bash
PYTHONPATH=src .venv/bin/python -m green_v2.ingestion.main
PYTHONPATH=src .venv/bin/python -m green_v2.workers.parser.main
PYTHONPATH=src .venv/bin/python -m green_v2.workers.db_writer.main
```

預設 health port 依序為 `28081`、`28082`、`28083`。DB Writer 現階段刻意
維持逐筆交易；真正批次消費必須在相容測試穩定後另作行為改善提交。
