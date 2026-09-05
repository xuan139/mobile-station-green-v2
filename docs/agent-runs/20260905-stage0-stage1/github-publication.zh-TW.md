# Green V2 GitHub 建立與首次推送記錄

日期：2026-09-05
執行帳號：`xuan139`
Repository：`xuan139/mobile-station-green-v2`
URL：`https://github.com/xuan139/mobile-station-green-v2`
可見性：Private
預設分支：`main`

## 本機來源

- 路徑：`/Users/lijiaxi/Documents/mobile-station-green-v2`
- 獨立 Git：`/Users/lijiaxi/Documents/mobile-station-green-v2/.git`
- Remote：`origin = https://github.com/xuan139/mobile-station-green-v2.git`

## 首次推送內容

- `main`：`3cf8c84`，綠能 V2 隔離骨架基準。
- `dev`：首次推送時為 `9e902e0`，包含本機驗證與繁體用字整理。
- Tags：`green-v2-skeleton-r1`、`green-v2-stage1-verified-r1`、`green-v2-stage1-local-r1`。

## 建立與推送命令

```bash
gh repo create xuan139/mobile-station-green-v2 --private --source=. --remote=origin
git push -u origin main
git push -u origin dev
git push origin --tags
```

## 驗證結果

- GitHub repository 顯示為 `PRIVATE`。
- 預設分支為 `main`。
- 本機 `main`／`dev` 已設定追蹤 `origin/main`／`origin/dev`。
- 舊 `xuan139/mobile-station` remote、分支與內容均未修改。

## 未執行事項

- 未建立 Pull Request 或 branch protection。
- 未建立 GitHub Actions secret。
- 未部署 AWS、資料庫、MQ、Station Agent、WPF 或設備。

