# 原神 Discord Bot
本分支使用 discord.py v2.0 開發版本

## 簡介
使用 Discord 機器人直接查詢原神內各項資訊，包含：
- 查詢即時便箋，包含樹脂、洞天寶錢、探索派遣...等
- 樹脂溢出提醒
- 查詢深境螺旋紀錄
- 查詢旅行者札記
- Hoyolab 自動每日簽到（含崩壞3）
- Hoyolab 使用兌換碼

## 範例

![](https://i.imgur.com/LcNJ2as.png)

![](https://i.imgur.com/aFoeVnU.gif)
![](https://i.imgur.com/rGFqQr2.gif)

![](https://i.imgur.com/qHzbvH0.png)

## 安裝 & 架設機器人

### 網頁端
1. 到 [Discord Developer](https://discord.com/developers/applications "Discord Developer") 登入 Discord 帳號

![](https://i.imgur.com/dbDHEM3.png)

2. 點選「New Application」建立應用，輸入想要的名稱後按「Create」

![](https://i.imgur.com/BcJcSnU.png)

3. 在 Bot 頁面，按「Add Bot」新增機器人

![](https://i.imgur.com/lsIgGCi.png)

4. 在 OAuth2/URL Generator，分別勾選「Bot」「Send Messages」「Manage Messages」，最底下產生的 URL 連結就是機器人的邀請連結，開啟連結將機器人邀請至自己的伺服器

![](https://i.imgur.com/08fcHs0.png)

### 取得配置檔案所需 ID

1. 在 General Information，取得機器人的 Application ID

![](https://i.imgur.com/h07q5zT.png)

2. 在 Bot 頁面，按「Reset Token」來取得機器人的 Token

![](https://i.imgur.com/BfzjewI.png)

3. 在自己的 Discord 伺服器名稱或圖示上按滑鼠右鍵，複製伺服器 ID（複製ID按鈕需要去 設定->進階->開發者模式 開啟）

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

## 配置檔案說明 (config.json)
```python
{
    "application_id": 123456789123456789,   # 機器人 Application ID，從 Discord Developer 網頁上取得
    "test_server_id": 212340008888812345,   # 測試用伺服器 ID，用來測試斜線指令，管理員指令只能在本伺服器使用
    "bot_token": "ABCDEFG",                 # 機器人 Token，從 Discord Developer 網頁取得
    "bot_prefix": "%",                      # (已無效) 機器人指令前綴
    "bot_cooldown": "3",                    # (已無效) 機器人對同一使用者接收指令的冷卻時間 (單位：秒)
    "auto_daily_reward_time": 8,            # 每日 Hoyolab 自動簽到時間 (單位：時)
    "auto_check_resin_threshold": 150       # 每小時檢查，當超過多少樹脂發送提醒
}
```

## 致謝
構想啟發自: https://github.com/Xm798/Genshin-Dailynote-Helper

原神 API 使用自: https://github.com/thesadru/genshin.py
