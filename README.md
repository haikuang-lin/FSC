# 美股每日收盤研究報告

這個 GitHub Actions 工作流會在美股交易日收盤後，產生繁體中文研究報告，並傳送到 Telegram。

追蹤群組：

- 航太太空：RKLB、ASTS、LUNR、RDW、PL、BKSY、KTOS、AVAV、RTX、LMT、NOC、BA、GE
- AI：NVDA、MSFT、GOOGL、META、AMD、AVGO、PLTR、ARM、TSM、SMCI
- 運動：NKE、LULU、ONON、DECK、UAA、CROX、YETI、SKX、DKS、FL

排程為 UTC 23:20（美東夏令 19:20／冬令 18:20；台北次日 07:20／06:20），並且每份 Markdown 報告會留存在 `reports/`。

## 啟用

1. 在 GitHub 倉庫開啟 **Settings → Actions → General → Workflow permissions**，選擇 **Read and write permissions**，按 Save。這讓工作流能把每天的報告存回 `reports/`。
2. 到 **Settings → Secrets and variables → Actions → Secrets**，按 **New repository secret**，逐一加入：
   - `OPENAI_API_KEY`：你的 OpenAI API 金鑰。這是讓報告產生 AI 中文摘要的必要項。
   - `TELEGRAM_BOT_TOKEN`：由 Telegram 的 `@BotFather` 建立機器人後取得的 token。
   - `TELEGRAM_CHAT_ID`：接收報告的私人聊天室、群組或頻道 ID。
3. （選用）到 **Variables** 新增 `OPENAI_MODEL`，例如 `gpt-4o-mini`。沒有設定時，工作流會用此預設值。
4. 到 **Actions → US market daily report → Run workflow** 手動跑一次。Telegram 會收到短摘要與完整 `.md` 報告附件。

## Telegram Token 與 Chat ID

### 建立 Bot Token

1. 在 Telegram 搜尋並開啟 `@BotFather`。
2. 傳送 `/newbot`，依提示輸入顯示名稱與以 `bot` 結尾的帳號名稱。
3. BotFather 回覆的 HTTP API token 就是 `TELEGRAM_BOT_TOKEN`；不要貼到程式碼、Issue 或聊天群組。
4. 打開你的新 bot，傳送 `/start`。若使用群組或頻道，先把 bot 加入；頻道須給它可發訊息的管理員權限。

### 取得 Chat ID

最簡單的私人聊天方式：先對 bot 傳 `/start`，然後在瀏覽器打開：

`https://api.telegram.org/bot<你的_TOKEN>/getUpdates`

在回傳 JSON 的 `message.chat.id` 找到數字（私人聊天通常是正數）。群組 ID 通常是負數，頻道多以 `-100` 開頭。把這個完整數字填進 `TELEGRAM_CHAT_ID`。

## 自訂股票清單

編輯 [`config/watchlist.json`](config/watchlist.json)，各組使用美股 ticker；下次執行即會套用。資料由 Yahoo Finance 取得，可能有延遲或暫時缺值。本專案只提供研究資訊，並非投資建議。
