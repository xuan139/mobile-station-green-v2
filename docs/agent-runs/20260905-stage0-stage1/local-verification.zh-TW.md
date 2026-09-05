# Green V2 本機驗證記錄

日期：2026-09-05
專案：`/Users/lijiaxi/Documents/mobile-station-green-v2`
分支：`dev`
基準提交：`3cf8c84`

## 環境

- OS：Darwin 25.2.0 arm64
- Python：3.14.2
- venv：專案內 `.venv`，已由 `.gitignore` 排除
- API：`127.0.0.1:28000`

## 安裝版本

主要直接依賴：

- FastAPI 0.141.1
- Uvicorn 0.52.4
- Pika 1.4.4
- Psycopg 3.3.5
- Psycopg Pool 3.3.1
- HTTPX 0.28.1
- Pytest 8.4.2

完整可重現版本可由隔離 venv 執行 `.venv/bin/python -m pip freeze` 取得。正式部署前
須另建立經 Linux／Python 3.12 驗證的 lock，不得把本次 macOS 測試環境直接當成正式部署 lock。

## 測試結果

```text
8 passed, 2 warnings in 3.72s
```

兩個 warning 來自 FastAPI／Starlette TestClient 對 HTTPX 與 AnyIO 舊介面的棄用提示；
本階段健康契約測試均通過。升級或正式鎖版前須再次確認相容組合。

## Smoke Test

```text
GET /health
{"service":"green-v2-api","status":"ok","version":"0.1.0"}

GET /ready
{"status":"ready"}

GET /api/v1/ping
{"message":"pong","service":"green-v2-api"}
```

## 未執行項目

- 這台 Mac 找不到 `docker` 命令，因此未執行 Compose config 或啟動容器。
- 未建立或連接 PostgreSQL。
- 未建立或連接 RabbitMQ。
- 未啟動 Ingress、Parser、DB Writer、Lifecycle 或 Station Agent。
- 未連線 AWS、正式服務、WPF 或真實設備。
- 未執行舊系統與 V2 的功能／資料一致性驗收。

