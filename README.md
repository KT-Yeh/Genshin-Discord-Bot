# 原神 Discord Bot
本分支使用 discord.py v2.0 開發版本

## 公共機器人
[![](https://i.imgur.com/ULhx0EP.png)](https://bit.ly/原神小幫手Bot)

#### 點擊上圖或邀請連結：https://bit.ly/原神小幫手Bot
- 多人伺服器要請有管理權限的人員邀請機器人
- 個人使用可以建立一個只有自己的 Discord 伺服器，然後邀請機器人

## 簡介
使用 Discord 機器人直接查詢原神內各項資訊，包含：
- 即時便箋，包含樹脂、洞天寶錢、質變儀、探索派遣...等
- 查詢深境螺旋紀錄
- 查詢旅行者札記
- 個人紀錄卡片（遊戲天數、成就、神瞳...等等）
- Hoyolab 使用兌換碼
- 每日早上 8~9 點 Hoyolab 自動簽到 (包含簽到崩壞3)
- 每兩小時自動檢查樹脂，當樹脂超過 145 時推送提醒
- 採用新的斜線指令，輸入 / 自動彈出指令提示，不需要記憶任何指令的使用方式

## 展示
更多展示圖片、GIF請參考巴哈文章：https://forum.gamer.com.tw/Co.php?bsn=36730&sn=162433

<img src="https://i.imgur.com/LcNJ2as.png" width="400"/> <img src="https://i.imgur.com/oNTOam5.png" width="300"/>


## 自己安裝 & 架設機器人

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
1. 下載 [本專案](https://github.com/KT-Yeh/Genshin-Discord-Bot/archive/refs/heads/discord.py_v2.0.zip)
2. 下載並安裝 Python（版本 3.8 以上）: https://www.python.org/downloads/
3. 在專案資料夾（Genshin-Discord-Bot）內，用文字編輯器開啟 `config.example.json` 檔案，把剛才取得的 Application ID、機器人 Token、伺服器 ID 貼在 `application_id`、`bot_token`、`test_server_id` 欄位，並將檔案另存為 `config.json`
4. 在專案資料夾內開啟 cmd 或 powershell，輸入底下命令安裝相關套件：
```
pip3 install -U -r requirements.txt
```
5. 輸入底下命令或是直接滑鼠雙擊開啟 main.py 檔案，開始運行機器人
```
python .\main.py
```
6. 若要在多個伺服器間使用，請在 Discord 測試伺服器的頻道內輸入 `/sync  範圍:全域伺服器`，並等待（約 1 小時）Discord 將指令推送

註1：當運行後看到 `[資訊][System]on_ready: You have logged in as XXXXX` 表示參數設置正確並成功啟動，此時機器人會自動同步所有指令到你的測試伺服器，稱為「本地同步」。

註2：若你輸入斜線 / 後看不到指令的話，請嘗試完全關閉 Discord 軟體並重啟 Discord。

## 配置檔案說明 (config.json)
```python
{
    "application_id": 123456789123456789,   # 機器人 Application ID，從 Discord Developer 網頁上取得
    "test_server_id": 212340008888812345,   # 測試伺服器 ID，用來測試斜線指令，管理員指令只能在本伺服器使用
    "bot_token": "ABCDEFG",                 # 機器人 Token，從 Discord Developer 網頁取得
    "auto_daily_reward_time": 8,            # 每日 Hoyolab 自動簽到時間 (單位：時)
    "auto_check_resin_threshold": 150,      # 每小時檢查，當超過多少樹脂發送提醒
    "auto_loop_delay": 2.0                  # 排程執行時每位使用者之間的等待間隔（單位：秒）
}
```

## Admin 管理指令說明
管理指令只能在配置檔案內設定的伺服器才能使用
```python
/sync：同步斜線指令，範圍「當前伺服器」表示將指令同步到你配置檔案的測試伺服器、「全域伺服器」表示將指令推送到所有伺服器，需等待約 1 小時
/broadcast：向機器人已連接的所有伺服器廣播訊息
/status：顯示機器人狀態，包含延遲、已連接伺服器數量、已連接伺服器名稱
/system reload：重新載入模組，非開發者不需要使用，重新載入後須使用 /sync，否則指令不會同步
/system precense 字串1,字串2,字串3,...：變更機器人顯示狀態(正在玩 ...)，每 5 分鐘隨機變更為設定的其中一個字串，字串數量不限
```

## 致謝
- 構想啟發自: https://github.com/Xm798/Genshin-Dailynote-Helper
- 原神 API 使用自: https://github.com/thesadru/genshin.py
- Discord API 使用自: https://github.com/Rapptz/discord.py
