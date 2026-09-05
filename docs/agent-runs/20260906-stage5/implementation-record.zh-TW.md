# Green V2 第五階段：綠能 Parser 全點位搬移

## 範圍

- 工作樹：`/private/tmp/mobile-station-green-v2-stage5-7`
- 分支：`codex/green-v2-stage5-7`
- 基準 commit：`0266ef2`
- 舊版來源：`origin/dev@23b8274a2a708f9b8d4de2a8c46df2dc541bca6d`

本階段搬移綠能 Parser 的電池組數值、電池告警、控制器 bits、控制排程與額外
控制點位。舊版固定輸入與輸出保存在
`contracts/mq/green-parser-golden-cases-v1.json`。

## Golden cases

- FC4：6 個電池組地址
- FC2：6 個電池組告警地址
- FC2 `0x1F0`：控制器狀態與故障
- FC3 `0x000`：模式與一週充放電排程
- FC3 `0x046`：非自訂模式停止放電 SOC
- 未知點位：`raw_passthrough`

共 16 組案例，輸出由固定舊版 commit 離線產生。V2 測試不在執行時 import
舊版程式，也不需要舊系統服務。

## 隔離與限制

- 沒有修改舊綠能或其他系統程式。
- 沒有連線 AWS、PostgreSQL、RabbitMQ 或設備。
- 本階段只搬移行為，不調整點位比例、名稱或資料格式。
- Runtime listener、consumer 與 DB Writer 分別留在第六、七階段。

## 驗證結果

- 全部測試：`47 passed`
- 16 組新舊 Parser golden cases：全部通過
- Python 編譯：通過
- 程式碼結構限制：通過

## 回退

第五階段使用獨立 commit；回退時只 revert 該 commit。
