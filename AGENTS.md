# 綠能 V2 Agent 規則

## 專案邊界

- 本倉庫只實作綠能 V2，不包含 BXSJ／鈉鹽。
- 舊綠能 `/Users/lijiaxi/Documents/mobile station` 只能唯讀參考。
- 禁止修改、提交、推送或部署舊綠能倉庫。
- 禁止連線舊 PostgreSQL、舊 RabbitMQ、AWS `unigo` 或真實設備。
- 第一階段只使用 `mobile_station_green_v2`、RabbitMQ `/green-v2` 與模擬資料。

## 工作規則

開始修改、提交、推送或部署前，必須執行並報告：

```text
pwd
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
```

- 寫入型 Agent 必須使用獨立 Git worktree 與 `codex/` 分支。
- 每個 Agent 只能修改任務明確分配的檔案。
- `dev` 只由總協調 Agent 整合。
- GitHub 建立、push、AWS 部署及任何外部寫入必須取得使用者明確確認。
- 行為修改必須附契約測試或整合測試。
- Migration 必須獨立、可追蹤，並說明向前與回退策略。
- 已確認方法、測試結果及部署結果必須記錄於 `docs/`。

## 架構規則

允許依賴方向：

```text
api / ingestion / workers / station_agent
                  |
                  v
             application
                  |
                  v
               domain

data_access / messaging 僅由 application 或組合根呼叫。
```

- `domain` 不得 import FastAPI、PostgreSQL、RabbitMQ 或設備驅動。
- API 路由不得直接撰寫 SQL。
- Worker 不得直接包含大型業務規則。
- 不建立大型通用 `db.py`、`main.py`、`helpers.py` 或 `misc.py`。
- 綠能與 BXSJ 不得互相 import、共享資料庫或共享 MQ vhost。

