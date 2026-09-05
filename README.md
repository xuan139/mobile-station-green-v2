# 綠能 V2

本專案是與現有綠能系統完全隔離的重寫基礎。現階段只建立可執行骨架、
健康契約、環境隔離、測試與多 Agent 治理，不包含正式業務功能。

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

