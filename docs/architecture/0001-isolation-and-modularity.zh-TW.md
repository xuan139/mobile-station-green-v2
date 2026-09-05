# ADR-0001：綠能 V2 隔離與模組化原則

日期：2026-09-05
狀態：已接受為第一階段骨架原則

## 決策

1. 綠能 V2 使用全新本地 Git 與全新 GitHub private repository。
2. 舊綠能只能唯讀參考，不修改其程式、資料庫、MQ、AWS 或設備。
3. V2 使用獨立資料庫 `mobile_station_green_v2`、MQ vhost `/green-v2`、
   API `28000` 與 Ingress `29000`。
4. BXSJ／鈉鹽自第一天起位於另一個獨立倉庫，不與綠能互相 import。
5. 外部行為以契約相容為目標；內部依 domain、application、adapter 分層，
   避免重新形成大型 `main.py` 或 `db.py`。
6. 真實設備命令在固定資料回放、契約測試、影子運行及單站審批前保持停用。

## 回退

第一階段沒有外部部署或生產寫入。若骨架不採用，刪除兩個新本地目錄與尚未
建立的 GitHub repository 即可；舊綠能不需任何回退操作。

