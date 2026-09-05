# 舊綠能測試、部署與回退盤點

日期：2026-09-05
執行方式：唯讀 Agent

## 結論

目前只適合繼續隔離開發與測試，不適合直接擴大部署。既有紀錄只證明 Cloud 與
單站 Agent 技術部署，尚未完成真實斷線重投的受控業務驗收。

## 部署風險

1. 通用 AWS systemd 腳本會涉及 BXSJ worker，卻未完整包含 mode schedule 與 command lifecycle worker，不適合 V2。
2. 通用打包腳本直接複製整個 `cloud/`，不符合 V2 白名單部署原則。
3. 現有本地啟停腳本會重設 DB／MQ，且未啟動 lifecycle worker，不能用於完全隔離 V2 驗證。
4. 舊 Modbus mock 僅支援 FC2／FC3／FC4，無法驗證 FC6／FC16 與單次設備寫入。
5. Parser 接受 `executing`，lifecycle 掃描包含它，但重投 SQL 只 claim `sent`；未耗盡 attempt 的 `executing` 可能卡死。
6. 沒有獨立 V2 投遞 kill switch；擴大部署前必須能停止建立新 V2 命令並回退至既有投遞方式。

## 測試金字塔

1. 靜態：compile/import、migration 重複執行、部署白名單、systemd 一致性、禁止正式 DSN。
2. 單元：TTL／時區、v1 duplicate ignore、v2 duplicate replay、過期拒寫、SQLite 重啟後 replay。
3. PostgreSQL 整合：舊 schema 升級、並行 claim、三次租約、`executing`、遲到結果、Log 同交易、錯誤 station result。
4. 元件：Ingress、MQ、Parser、DB Writer、Lifecycle Worker 與可控 fault proxy。
5. 端到端：可寫／可計數 Modbus fake，驗證 ACK／result 丟失、Agent／Cloud 重啟、租約耗盡與過期拒寫。

## 完全隔離的本地拓樸

| 資源 | 本階段固定值／規則 |
|---|---|
| PostgreSQL | `mobile_station_green_v2`，host port `55432` |
| RabbitMQ | vhost `/green-v2`，host port `55672` |
| API／Ingress | `28000`／`29000` |
| 執行環境 | 不得使用舊 `cloud/config/local.env` 或舊啟停腳本 |
| Agent／設備 | 本階段不連真實 Agent 或 Modbus；後續使用獨立 simulator |

整合測試階段再以 run ID 建立一次性 database、vhost、queue、port、station ID 與 SQLite 路徑，
並使用 `APP_ENV=v2_integration`，避免繞過 Parser。

## 提交與 Tag 原則

- 每個可驗證批次單獨提交，結構搬移與行為修正分開。
- 候選版本使用不可移動的 annotated tag。
- 打包只能來自乾淨 working tree 的明確 commit，記錄 package SHA-256。
- 本階段新倉庫可使用 `green-v2-skeleton-r1`；尚未部署，不可命名為 production tag。

## 回退順序

1. 停止建立新命令，停用模式規則及 lifecycle，盤點活動命令。
2. 單站 Agent 問題先回退試點 Agent，保留 SQLite journal。
3. Cloud 以日期化備份及 revert commit 回退，不使用 destructive reset。
4. 已過期命令不得恢復 pending，設備核對後建立新命令。
5. 穩定觀察後才移除 unit、程式與無效設定；migration 欄位及索引先保留。
6. Schema 實體刪除須另排維護窗口、異機備份與反向 migration，不以全庫 restore 當一般回退。

## 主要證據

- 通用部署腳本：`cloud/scripts/deploy_aws_systemd.sh:9`、`:197`
- 打包腳本：`deploy/cloud/aws/scripts/package_cloud_aws_bundle.sh:19`
- 本地啟停：`cloud/scripts/run_local_cloud.sh:16`
- Mock Modbus：`implementation_examples/mock_modbus_tcp_device.py:521`
- lifecycle／claim：`cloud/common/db.py:926`、`:948`
- lifecycle 設定：`cloud/common/config.py:190`
- 既有整合測試：`tests/test_db_integration.py:1075`

