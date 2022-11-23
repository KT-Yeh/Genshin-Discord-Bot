# 原神 Discord Bot

歡迎將本專案所有或部分程式碼放入你自己的機器人中，只需要在你專案的網頁、README 或任何公開的說明文件放入本專案的作者與連結

Feel free to take all or part of the code to your own bot, just put the author and URL of this project in your project's website, README or any public documentation.

## 邀請原神小幫手
[![](https://i.imgur.com/ULhx0EP.png)](https://bit.ly/原神小幫手邀請)
#### 點擊上圖或邀請連結：https://bit.ly/原神小幫手邀請
Discord 支援伺服器：https://discord.gg/myugWxgRjd

## 簡介
使用機器人直接在 Discord 聊天頻道內查看原神內各項資訊，包含：
- 查詢即時便箋，包含樹脂、洞天寶錢、參數質變儀、探索派遣完成時間...等
- 查詢深境螺旋紀錄
- 查詢旅行者札記
- 個人紀錄卡片（遊戲天數、成就、神瞳、世界探索度...等等）
- 使用 Hoyolab 兌換碼
- 每日早上 8 點開始 Hoyolab 自動簽到 (包含簽到崩壞3)
- 自動檢查樹脂、寶錢、質變儀、探索派遣，當快額滿時發送提醒
- 查詢任意玩家的展示櫃，顯示展示櫃內角色的面板、聖遺物詳情
- 採用新的斜線指令，輸入 / 自動彈出指令提示，不需要記憶任何指令的使用方式


## 使用方式
- 邀請到自己伺服器後，輸入斜線 `/` 查看各項指令
- 第一次請先使用指令 `/cookie設定`，Cookie 取得方式：https://bit.ly/3LgQkg0
- 設定自動簽到與樹脂提醒，使用指令 `/schedule排程`

## 展示
更多展示圖片、GIF 請參考巴哈介紹文章：https://forum.gamer.com.tw/Co.php?bsn=36730&sn=162433

<img src="https://i.imgur.com/LcNJ2as.png" width="350"/> <img src="https://i.imgur.com/IEckUqY.jpg" width="500"/>


## 自己安裝 & 架設機器人
安裝前請先確認自己遇到基本的問題有 Google 解決的能力，任何不關於本專案程式碼的問題（例如：python 安裝、套件安裝...等），請不要來問我。舉例來說：你不會拿著食譜去問食譜作者你家的瓦斯爐要怎麼開、烤箱沒插電怎麼辦之類的問題。若是有功能或是程式碼上的問題與建議，歡迎來討論。

### 網頁端
1. 到 [Discord Developer](https://discord.com/developers/applications "Discord Developer") 登入 Discord 帳號

![](https://i.imgur.com/dbDHEM3.png)

2. 點選「New Application」建立應用，輸入想要的名稱後按「Create」

![](https://i.imgur.com/BcJcSnU.png)

3. 在 Bot 頁面，按「Add Bot」新增機器人

![](https://i.imgur.com/lsIgGCi.png)

4. 在 OAuth2/URL Generator，分別勾選「bot」「applications.commands」「Send Messages」，最底下產生的 URL 連結就是機器人的邀請連結，開啟連結將機器人邀請至自己的伺服器

![](https://i.imgur.com/y1Ml43u.png)

### 取得配置檔案所需 ID

1. 在 General Information，取得機器人的 Application ID

![](https://i.imgur.com/h07q5zT.png)

2. 在 Bot 頁面，按「Reset Token」來取得機器人的 Token

![](https://i.imgur.com/BfzjewI.png)

3. 在自己的 Discord **伺服器名稱或圖示**上按滑鼠右鍵，複製**伺服器 ID**（複製 ID 按鈕需要去 設定->進階->開發者模式 開啟）

![](https://i.imgur.com/tCMhEhv.png)

### 本地端
1. 下載 [本專案](https://github.com/KT-Yeh/Genshin-Discord-Bot/archive/refs/heads/master.zip)

2. 新增 `config.json` 檔案：在專案資料夾（Genshin-Discord-Bot）內，用文字編輯器開啟 `config.json.example` 檔案，把剛才取得的 Application ID、機器人 Token、伺服器 ID 貼在 `application_id`、`bot_token`、`test_server_id` 欄位，並將檔案名稱**另存**為 `config.json`

接下來下面兩種方式**二選一**：一種是使用 Docker 容器，優點是你不用管 Python 的版本與套件的安裝可能導致的衝突或是未知原因的錯誤，若你套件一直裝不好的話建議使用此方法；另一種是傳統的安裝 Python 環境以及相關套件。

#### 方法1. Docker 容器
1. 至 [Docker 官網](https://www.docker.com/) 下載並安裝，安裝完成後啟動 Docker Desktop，Windows 桌面右下角會有一隻鯨魚圖示 (不會安裝的請自行 Google 教學)

2. 在機器人專案資料夾內開啟 cmd 或 powershell，輸入底下命令啟動機器人
```
docker-compose up
```
若你想要可以關掉 cmd 在背景執行的話，則使用
```
docker-compose up -d
```
Windows 右下角的鯨魚圖示打開 Docker Desktop 可以隨時管理機器人運行的狀態

#### 方法2. Python + 套件安裝
1. 下載並安裝 [Python](https://www.python.org/downloads/)（版本 3.8 以上，推薦使用 3.10）

2. 在專案資料夾內開啟 cmd 或 powershell，輸入底下命令安裝相關套件：
```
pip3 install -U -r requirements.txt
```

3. 輸入底下命令或是直接滑鼠雙擊開啟 main.py 檔案，開始運行機器人
```
python .\main.py
```

---

註1：當運行後看到 `【系統】on_ready: You have logged in as XXXXX` 表示參數設置正確並成功啟動，此時機器人會自動同步所有指令到你的測試伺服器，稱為「本地同步」。

註2：若你輸入斜線 / 後看不到指令的話，請嘗試 CTRL + R 重新整理或是完全關閉 Discord 軟體並重啟 Discord。

註3：若要在多個伺服器間使用，請在 Discord 測試伺服器的頻道內使用指令 `/sync 範圍:全域伺服器`，並等待（約幾分鐘）Discord 將指令推送，稱為「全域同步」。

## 配置檔案說明 (config.json)
前三行必需改成自己的設定值，其他行可以不改保留預設值
```python
{
    "application_id": 123456789123456789,   # 機器人 Application ID，從 Discord Developer 網頁上取得
    "test_server_id": 212340008888812345,   # 測試伺服器 ID，用來測試斜線指令，管理員指令只能在本伺服器使用
    "bot_token": "ABCDEFG",                 # 機器人 Token，從 Discord Developer 網頁取得
    "schedule_daily_reward_time": 8,        # 每日 Hoyolab 自動簽到的開始時間 (單位：時)
    "schedule_check_resin_interval": 10,    # 自動檢查即時便箋的間隔 (單位：分鐘)
    "schedule_loop_delay": 2.0,             # 排程執行時每位使用者之間的等待間隔（單位：秒）
    "expired_user_days": 30,                # 過期使用者天數，會刪除超過此天數未使用任何指令的使用者
    "slash_cmd_cooldown": 5.0,              # 使用者重複呼叫部分斜線指令的冷卻時間（單位：秒）
    "discord_view_long_timeout": 1800,      # Discord 長時間互動介面（例：下拉選單） 的逾時時間（單位：秒）
    "discord_view_short_timeout": 60,       # Discord 短時間互動介面（例：確認、選擇按鈕）的逾時時間（單位：秒）
    "database_file_path": "data/bot.db",    # 資料庫儲存的資料夾位置與檔名
    "sentry_sdk_dsn": "https://XXX@XXX",    # Sentry DSN 位址設定，參考底下說明
    "notification_channel_id"               # 每日簽到完成後統計訊息欲發送到的 Discord 頻道 ID
}
```
## 表情符號配置說明 (data/emoji.json)
非必要，不配置表情符號也能正常運行機器人
1. 將 `data/emoji.json.example` 重新命名為 `data/emoji.json`
2. 自行上傳相關的表情符號至自己的伺服器
3. 將相對應的表情符號依照 Discord 格式填入到 `emoji.json` 檔案裡

註：
- Discord 表情符號格式：`<:表符名字:表符ID>`，例如：`<:Mora:979597026285200002>`
- 可以在 Discord 訊息頻道輸入 `\:表符名字:` 取得上述格式
- 若使用的表情符號不在同一個伺服器內，則機器人所在的頻道，「Everyone」身分組（不是機器人本身的身分組）需要有使用外部表情符號的權限

## Sentry 配置說明
非必要，Sentry 是用來追蹤程式執行中沒接到的例外，並將發生例外當時的函式呼叫、變數、例外...等詳細資訊傳送到網頁上供開發者追蹤，若不需要此功能的話可以跳過此設定

1. 到官網註冊帳號：https://sentry.io/
2. 在帳號內建立一個 Python 專案，建立後可取得該專案的 DSN 網址（格式：`https://xxx@xxx.sentry.io/xxx`）
3. 將此 DSN 網址貼到 `config.json` 檔案

註：
- 若沒有指定，Sentry 預設只發送沒有 try/except 的例外
- 若要將特定接到的例外發送到 Sentry 的話，請在該 except 內使用 `sentry_sdk.capture_exception(exception)`

## Admin 管理指令說明
管理指令只能在配置檔案設定的測試伺服器內才能使用
```python
/sync：同步斜線指令，範圍「當前伺服器」表示將指令同步到你配置檔案的測試伺服器、「全域伺服器」表示將指令推送到所有伺服器，需等待約 1 小時
/status：顯示機器人狀態，包含延遲、已連接伺服器數量、已連接伺服器名稱
/system reload：重新載入模組，非開發者不需要使用，重新載入後須使用 /sync，否則指令不會同步
/system precense 字串1,字串2,字串3,...：變更機器人顯示狀態(正在玩 ...)，每分鐘隨機變更為設定的其中一個字串，字串數量不限
/maintenance：設定遊戲維護時間，在此時間內自動排程(簽到、檢查樹脂)不會執行
/config：動態改動 config.json 部分配置的值
```

## 致謝
- 原神 API 使用自: https://github.com/thesadru/genshin.py
- Discord API 使用自: https://github.com/Rapptz/discord.py
- Enka Network API 使用自: https://github.com/EnkaNetwork/API-docs