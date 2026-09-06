# Green V2 第六階段：Ingress 與 Parser Runtime

## 範圍

- 前置 commit：`6454e17`
- 執行入口：
  - `python -m green_v2.ingestion.main`
  - `python -m green_v2.workers.parser.main`

本階段建立 TCP JSON Line ingress、RabbitMQ publisher／consumer、Parser Worker
runner、程序 signal shutdown 與獨立 health server。程序組合集中在 `bootstrap`，
Ingress 與 Worker 入口不直接繞過 application layer。

## 保留的舊版語意

- Queue 宣告為 durable。
- JSON 訊息使用 persistent delivery mode 2。
- Consumer 使用 manual ACK 與 prefetch。
- Delivery handle 包含 connection generation，舊連線 delivery 不會誤 ACK。
- Parser 發布 parsed 或 failed envelope 成功後才 ACK。
- 發布失敗時 NACK 並 requeue，worker loop 保持運行。
- TCP ingress 保留逐行 JSON、讀取逾時、連線數、訊息大小與發布 concurrency 限制。

## V2 隔離預設值

- Ingress：`127.0.0.1:29000`
- Ingress health：`127.0.0.1:28081`
- Parser health：`127.0.0.1:28082`
- RabbitMQ：`127.0.0.1:55672`，vhost `/green-v2`

## 驗證結果

- 全部測試：`56 passed`
- loopback TCP JSON Line 與 ACK：通過
- 超大訊息 `PAYLOAD_TOO_LARGE`：通過
- health live／ready 與未啟動安全關閉：通過
- RabbitMQ durable、persistent、manual ACK、prefetch、generation guard：mock 通過
- Python 編譯及程式碼結構限制：通過

## 尚未完成

- 本機沒有 RabbitMQ Server，因此未做 `/green-v2` live broker 測試。
- 尚未建立最終 systemd unit 與部署包。
- 尚未接 PostgreSQL 或 DB Writer。
- 尚未接 pending command repository；Ingress 已保留 application 注入點。
- 未連線 AWS、舊 MQ、舊 DB 或真實設備。

## 回退

第六階段使用獨立 commit；回退該 commit 不會移除第五階段 Parser 規則。
