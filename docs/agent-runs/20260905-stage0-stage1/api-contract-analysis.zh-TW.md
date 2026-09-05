# 舊綠能 API 契約盤點

日期：2026-09-05
執行方式：唯讀 Agent
舊程式基準：`/Users/lijiaxi/Documents/mobile station`，分支 `dev`，HEAD `25572ae`

## 邊界

- 未修改舊程式、Git 狀態或外部環境。
- 未進入獨立 WPF repository；WPF 呼叫行為以舊倉庫既有架構與效能文件為證據。
- WPF 不直接連接 DB／MQ，而是透過 `HttpStationDataProvider` 呼叫 Cloud API。

## 現行 API 責任

- `cloud/services/api/main.py`：HTTP 路由、JSON、Bearer 認證、權限、站台 scope 及 Audit 編排，目前集中於單一 handler。
- `cloud/common/db.py`：相容 facade，仍含快照、歷史、告警設定、排程模板與命令等遺留業務。
- `cloud/data_access/access_control.py`：登入、Session、使用者、角色、權限、Audit、System Log 與站台 scope。
- `station_directory.py`、`alarm_records.py`、`green_energy.py`、`mode_schedule.py`、`station_overview.py` 已按資料域拆分部分責任。

## WPF 必須保留的 V1 契約

1. 切換完成前保留 `/api/v1` 與 `/v1` 相容別名。
2. 保留 `pageSize/page_size` 及 camelCase／snake_case 的舊欄位別名；新核心模型應由 adapter 轉換。
3. 保留總覽 33 個摘要欄位、`snapshot=null`，以及單站完整 `summary`、`powerFlow`、`batterySystem`、`controlView`、`batteryModules`、`statusGroups`。
4. 保留告警排序及 `OPEN/ACKED/RESOLVED` 原始狀態；繁體顯示文字留在 presentation adapter 或 UI。
5. 舊 WPF 已依賴部分格式化字串、空字串與 `--`，不可直接以理想化純數值契約取代。
6. `/home/alarms/latest` 與 `/home/alarm-sound-state` 仍是提案，不能列為既有契約。

## 主要 API 群組

- Health/Auth：`/ping`、`/auth/login`、`/auth/logout`、`/auth/me`、`/auth/me/permissions`。
- 站台與總覽：`/stations`、`/station-directory`、`/overview/stations`、`/stations/{id}/snapshot/latest`。
- 遙測：站台 overview、battery、protocol、status、points 與單一 metric 歷史。
- 告警：全域／單站告警、標記、確認、刪除、數值與 bit 告警設定。
- 命令：`GET/POST /stations/{id}/commands`。
- 電價與效益：電價 CRUD 及每日轉供效益。
- 排程：排程模板 CRUD、套用、自動模式規則與 execution／target。
- 歷史：點位、群組及複合歷史查詢。
- 維運：站台主檔、SIM、Agent 設定、provision、啟停與重啟。
- Log/IAM：Audit、System Log、Log Center、政策、使用者、角色、權限與解鎖。

## 高風險缺口

1. `/global-alarms/latest` 未按登入者可見站台過濾，存在 scope 洩漏風險。
2. `0x042` 仍可能落入一般寄存器寫入權限，且 admin 可繞過，與最新工程模式需求不符。
3. `userId/loginId == admin` 的特殊判定及硬編碼預設帳密 seed 使身分模型脆弱。
4. data layer 支援 `idempotency_key`，但 HTTP 路由未接收；`created_by` 與 `station_name` 不應由客戶端決定。
5. `POST /system-logs` 僅要求登入，提交權限過寬。
6. 多個 GET 會刷新 runtime 並可能建立通訊告警，讀取 API 帶有寫入副作用。
7. 錯誤契約缺少 correlation ID、欄位驗證細節與穩定 domain code，500 可能洩漏內部例外。

## V2 實作原則

- 建立 `api/v1_adapter` 凍結舊路由與 DTO；新 API 按 auth、stations、telemetry、alarms、commands、schedules、history、iam、operations 分域。
- 權限、工程模式與 station scope 集中於 application policy。
- 命令白名單、互鎖、冪等、期限、Audit 與回讀驗證集中於 command application service。
- V2 核心 DTO 使用具型別 schema；WPF 格式相容只留在 adapter。
- runtime 離線判定與告警建立移至 worker，GET 應保持純讀。
- 第一個業務批次前先建立 V1 golden contract tests，不得在同一提交同時大搬移與改行為。

## 主要證據

- API 路由：`cloud/services/api/main.py:650`
- 總覽契約：`cloud/services/api/main.py:1274`、`cloud/common/db.py:8706`
- 命令建立：`cloud/services/api/main.py:2021`
- 歷史查詢：`cloud/common/db.py:8180`
- 權限／登入：`cloud/data_access/access_control.py:1506`、`:2159`
- 告警查詢：`cloud/data_access/alarm_records.py:623`、`:664`

