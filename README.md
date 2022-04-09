# 原神 Discord Bot


## 簡介
使用 Discord 機器人直接查詢原神內各項資訊，包含：
- 查詢即時便箋，包含樹脂、洞天寶錢、探索派遣...等
- 樹脂溢出提醒
- 查詢深境螺旋紀錄
- 查詢旅行者札記
- Hoyolab 自動每日簽到
- Hoyolab 使用兌換碼

## 範例
![](https://i.imgur.com/Ye0HA0G.png)
![](https://i.imgur.com/qHzbvH0.png)
![](https://i.imgur.com/bNY19NW.png)

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

5. 回到 Bot 頁面，按「Reset Token」來取得並複製機器人的 Token，等等會用到

![](https://i.imgur.com/BfzjewI.png)


### 本地端
1. 下載 [本專案](https://github.com/KT-Yeh/Genshin-Discord-Bot/archive/refs/heads/master.zip)
2. 下載並安裝 Python（版本 3.8 以上）: https://www.python.org/downloads/
3. 在專案資料夾（Genshin-Discord-Bot）內，用文字編輯器開啟 `config.example.json` 檔案，把剛才取得的 Token 貼在 `bot_token` 欄位，並將檔案另存為 `config.json`
4. 在專案資料夾內開啟 cmd 或 powershell，輸入底下命令安裝相關套件：
```
pip3 install -r requirements.txt
```
5. 輸入底下命令或是直接滑鼠雙擊開啟 main.py 檔案，開始運行機器人
```
python .\main.py
```

## 配置檔案說明 (config.json)
```python
{
    "bot_token": "ABCDEFG",  # 機器人Token，需從 Discord 網頁取得
    "bot_prefix": "%",       # 機器人指令前綴
    "bot_cooldown": "3",     # 機器人對同一使用者接收指令的冷卻時間 (單位：秒)
    "auto_daily_reward_time": 8,        # 每日Hoyolab自動簽到時間 (單位：時)
    "auto_check_resin_threshold": 150   # 每小時檢查，當超過多少樹脂發送提醒
}
```

## 結尾
構想啟發自: https://github.com/Xm798/Genshin-Dailynote-Helper

API 使用自: https://github.com/thesadru/genshin.py
