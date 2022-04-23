# 原神 Discord Bot
本分支使用 discord.py v1.7.3，為舊版 API

目前已將機器人開發轉換至 discord.py v2.0，請參考 [v2.0 分支](https://github.com/KT-Yeh/Genshin-Discord-Bot/tree/discord.py_v2.0)

等到 discord.py v2.0 正式版發佈後，屆時會將分支合併回來 master

## 簡介
使用 Discord 機器人直接查詢原神內各項資訊，包含：
- 查詢即時便箋，包含樹脂、洞天寶錢、探索派遣...等
- 樹脂溢出提醒
- 查詢深境螺旋紀錄
- 查詢旅行者札記
- Hoyolab 自動每日簽到
- Hoyolab 使用兌換碼

## 範例
![](https://i.imgur.com/QQLBbUn.png)
![](https://i.imgur.com/Ye0HA0G.png)
![](https://i.imgur.com/qHzbvH0.png)
![](https://i.imgur.com/bNY19NW.png)

## 公共機器人
![](https://i.imgur.com/ULhx0EP.png)

#### 邀請連結：https://bit.ly/原神小幫手Bot
- 多人伺服器要請有管理權限的人員邀請機器人
- 個人使用可以建立一個只有自己的 Discord 伺服器，然後邀請機器人

## 自己安裝 & 架設機器人

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
3. 在專案資料夾（Genshin-Discord-Bot）內，用文字編輯器開啟 `.env(example)` 檔案，把剛才取得的 Token 貼在 `BOT_TOKEN = ` 欄位後面，並將檔案另存為 `.env`
4. 在專案資料夾內開啟 cmd 或 powershell，輸入底下命令安裝相關套件：
```
pip3 install -r requirements.txt
```
5. 輸入底下命令或是直接滑鼠雙擊開啟 main.py 檔案，開始運行機器人
```
python .\main.py
```

### docker方式
1. 安裝docker
2. 下載 [本專案](https://github.com/KT-Yeh/Genshin-Discord-Bot/archive/refs/heads/master.zip) 並解壓
3. 設定好你的`.env`檔案(同"本地端"使用方法步驟3)
4. 在專案資料夾內使用terminal輸入docker-compose指令運行
    ```
    # 在前台運行(關閉terminal=關閉bot)
    docker-compose up
    # 在後台運行(關閉docker=關閉bot,可以關閉terminal)
    docker-compose up -d
    # 查看bot的輸出
    docker-compose logs -f
    # 關閉bot
    docker-compose down
    ```


## 配置檔案說明 (.env)
```python
BOT_TOKEN=ABCDEFG               # 機器人Token，需從 Discord 網頁取得
BOT_PREFIX=%                    # 機器人指令前綴
BOT_COOLDOWN=3                  # 機器人對同一使用者接收指令的冷卻時間 (單位：秒)
AUTO_DAILY_REWARD_TIME=8        # 每日Hoyolab自動簽到時間 (單位：時)
AUTO_CHECK_RESIN_THRESHOLD=150  # 每小時檢查，當超過多少樹脂發送提醒
```

## 致謝
構想啟發自: https://github.com/Xm798/Genshin-Dailynote-Helper

API 使用自: https://github.com/thesadru/genshin.py
