# 原神 & 星穹鐵道 Discord Bot

歡迎將本專案所有或部分程式碼放入你自己的機器人中，只需要在你專案的網頁、README 或任何公開的說明文件放入本專案的作者與連結

Feel free to take all or part of the code to your own bot, just put the author and URL of this project in your project's website, README or any public documentation.

## 邀請原神小幫手
[![](https://i.imgur.com/ULhx0EP.png)](https://bit.ly/原神小幫手邀請)
#### 點擊上圖或邀請連結：https://bit.ly/原神小幫手邀請
Discord 支援伺服器：https://discord.gg/myugWxgRjd

## 簡介
使用機器人直接在 Discord 聊天頻道內查看原神、星穹鐵道內各項資訊，包含：

- 原神、崩壞3、星穹鐵道、未定事件簿：
    - **自動簽到**：設定時間每天自動幫你簽到 Hoyolab 領獎

- 原神、星穹鐵道：
    - 查詢**即時便箋**
        - 原神：包含樹脂、每日委託、洞天寶錢、參數質變儀、探索派遣
        - 星穹鐵道：包含開拓力、每日實訓、模擬宇宙、歷戰餘響、委託執行
    - **自動檢查即時便箋**：樹脂 (開拓力)、每日、寶錢、質變儀、探索派遣，當快額滿時發送提醒
    - 查詢深境螺旋、忘卻之庭、虛構敘事紀錄，並可以保存每一期紀錄
    - 查詢任意玩家的**角色展示櫃**，顯示展示櫃內角色的面板、聖遺物詳情

- 原神： 
    - 個人紀錄卡片，包含遊戲天數、成就、神瞳、世界探索度...等等
    - 查詢旅行者札記
    - 查看遊戲內公告，包含活動、卡池資訊
    - 搜尋資料庫，包含角色、武器、各項物品、成就、七聖卡牌資料

## 使用方式
- 邀請到自己伺服器後，輸入斜線 `/` 查看各項指令
- 第一次請先使用指令 `/cookie設定`，Cookie 取得方式：https://bit.ly/3LgQkg0
- 設定自動簽到與即時便箋提醒，使用指令 `/schedule排程`

## 展示
更多展示圖片、GIF 請參考巴哈介紹文章：https://forum.gamer.com.tw/Co.php?bsn=36730&sn=162433

<img src="https://i.imgur.com/LcNJ2as.png" width="350"/>
<img src="https://i.imgur.com/IEckUqY.jpg" width="500"/>
<img src="https://i.imgur.com/PA5HIDO.gif" width="500"/>


## 專案資料夾結構
```
Genshin-Discord-Bot
├── assets         = 存放素材的資料夾
|   ├── font         = 畫圖所用到的字體
|   └── image        = 畫圖所用到的素材、背景圖
├── cogs         = 存放 discord.py cog 資料夾，這裡有所有的機器人指令
├── cogs_external= 存放自訂的 discord.py cog 資料夾，你可以將自己指令的檔案放在這裡
├── configs      = 存放設定檔的資料夾
├── database     = SQLAlchemy ORM、資料庫操作相關的程式碼
|   ├── alembic  =   = 資料庫結構變動版本控制
|   ├── dataclass    = 自定義的 data class
|   └── legacy       = 以前的資料庫程式碼，用來遷移舊資料之外沒有用
├── enka_network = 與 Enka Network API 相關的程式碼
|   └── enka_card    = Submodule，與畫 Enka 圖片相關的程式碼
├── genshin_db   = 與 genshin-db API 相關的程式碼 
|   └── models       = 存放 genshin-db 資料的 pydantic 模型
├── genshin_py   = 與 genshin.py 相關的程式碼
|   ├── auto_task    = 與自動排程任務 (例如：簽到) 相關的程式碼
|   ├── client       = 向 API 請求資料相關的程式碼
|   └── parser       = 將 API 的資料轉成 discord embed 格式
├── star_rail    = 星穹鐵道展示櫃程式碼
└── utility      = 一些本專案用到的設定、公用函數、Log、表情、Prometheus...等程式碼
```


## 自己安裝 & 架設機器人

### 網頁端
需要在此步驟取得：
- 機器人 Application ID
- 機器人 Bot token
- 自己的管理伺服器 ID

<details><summary>>>> 點此查看完整內容 <<<</summary>

1. 到 [Discord Developer](https://discord.com/developers/applications "Discord Developer") 登入 Discord 帳號

![](https://i.imgur.com/dbDHEM3.png)

2. 點選「New Application」建立應用，輸入想要的名稱後按「Create」

![](https://i.imgur.com/BcJcSnU.png)

3. 在 Bot 頁面，按「Add Bot」新增機器人

![](https://i.imgur.com/lsIgGCi.png)

4. 在 OAuth2/URL Generator，分別勾選「bot」「applications.commands」「Send Messages」，最底下產生的 URL 連結就是機器人的邀請連結，開啟連結將機器人邀請至自己的伺服器

![](https://i.imgur.com/y1Ml43u.png)

#### 取得配置檔案所需 ID

1. 在 General Information，取得機器人的 Application ID

![](https://i.imgur.com/h07q5zT.png)

2. 在 Bot 頁面，按「Reset Token」來取得機器人的 Token

![](https://i.imgur.com/BfzjewI.png)

3. 在自己的 Discord **伺服器名稱或圖示**上按滑鼠右鍵，複製**伺服器 ID**（複製 ID 按鈕需要去 設定->進階->開發者模式 開啟）

![](https://i.imgur.com/tCMhEhv.png)

</details>

### 本地端

#### 第一次使用
1. 安裝 Docker (不會安裝的請自行 Google 教學)
    - Windows：至 [Docker 官網](https://www.docker.com/) 下載並安裝，安裝完成後啟動 Docker Desktop，Windows 桌面右下角會有一隻鯨魚圖示
    ![](https://i.imgur.com/FlLszWB.png)
    - Linux：[官網說明](https://docs.docker.com/engine/install/ubuntu/)，左邊有不同 Distribution 可選

接下來沒特別說明都以 Windows、使用 Powershell 來說明

2. 找到你想放資料的地方，建立新資料夾 `Genshin-Discord-Bot`，然後進入

3. 下載 [docker-compose.yml](https://github.com/KT-Yeh/Genshin-Discord-Bot/blob/master/docker-compose.yml) 檔案，放在資料夾內

4. 文字編輯器開啟 `docker-compose.yml` 檔案，基本上都不用動，只要把你剛剛在 [#網頁端](#網頁端) 拿到的三個資料填入底下三個欄位即可，其他設定可根據自己的需求再改，完成後保存
    - APPLICATION_ID=`123456789`
    - TEST_SERVER_ID=`123456789`
    - BOT_TOKEN=`ABCD123456789`

5. 在此資料夾開啟 Powershell，輸入底下命令即可運行
```
docker-compose up
```
若你想要可以關掉 Powershell 在背景執行的話，則使用
```
docker-compose up -d
```
Windows 右下角的鯨魚圖示打開 Docker Desktop 可以隨時管理機器人運行的狀態

註1：當運行後看到 `【系統】on_ready: You have logged in as XXXXX` 表示參數設置正確並成功啟動，此時機器人會自動同步所有指令到你的測試伺服器，稱為「本地同步」。

註2：若你輸入斜線 / 後看不到指令的話，請嘗試 CTRL + R 重新整理或是完全關閉 Discord 軟體並重啟 Discord。

註3：若要在多個伺服器間使用，請在你機器人的私訊頻道內輸入 `$jsk sync`，並等待（約幾分鐘）Discord 將指令推送，稱為「全域同步」。


#### 從舊版 v1.2.1 版升級上來 (新安裝者不用看)

<details><summary>>>> 點此查看完整內容 <<<</summary>

1. 建立新的資料夾 `Genshin-Discord-Bot`，一樣先照上面做到第 4 步驟
2. 將舊版的 `data` 資料夾內的資料：`bot.db` (`emoji.json`)，複製到新資料夾對應位置
3. 所以現在新資料夾結構如下：
```
Genshin-Discord-Bot/
    ├── docker-compose.yml
    └── data/
        ├── bot/
        │   └── bot.db
        ├── app_commands.json
        └── emoji.json
```
4. 回到 `Genshin-Discord-Bot` 目錄，因為資料庫結構有變動，需要先執行指令
    - Windows (Powershell)：`docker run -v ${pwd}/data:/app/data ghcr.io/kt-yeh/genshin-discord-bot:latest python main.py --migrate_database`
    - Linux：`sudo docker run -v $(pwd)/data:/app/data ghcr.io/kt-yeh/genshin-discord-bot:latest python main.py --migrate_database`
5. 完成變更資料庫後，執行 `docker-compose up` 即可開始運行機器人

</details>

---

### 檔案說明 & 資料備份
成功運行機器人後，你的資料夾結構應該是這樣：
```
Genshin-Discord-Bot/
    ├── docker-compose.yml  = docker 設定擋，啟動機器人相關設定都在此檔案
    ├── cogs_external/      = 你可以放自己寫的 discord.py cog 到此目錄
    └── data/               = 機器人運行時產生的資料都放在此目錄
        ├── bot/
        │   └── bot.db         = 資料庫檔案
        ├── font/           = 存放字體資料夾
        ├── image/          = 存放圖片資料夾
        ├── _app_commands.json     = 指令 mention 設定檔案
        ├── _emoji.json            = 表情符號設定檔案
        ├── grafana_dashboard.json = grafana 面板設定檔案 
        └── prometheus.yml         = prometheus 伺服器設定擋
```
資料都放在 `data` 資料夾內，備份整個資料夾即可；還原的時候將備份的資料覆蓋回 `data` 資料夾即可

### 如何更新
當專案有更新時，到 `Genshin-Discord-Bot` 目錄開啟 Powershell
1. 抓新版 image
```
docker-compose pull
```
2. 重新啟動機器人
```
docker-compose up -d
```


## 表情符號配置說明 (data/emoji.json)

<details><summary>點此查看完整內容</summary>

非必要，不配置表情符號也能正常運行機器人
1. 到 `data` 目錄將 `_emoji.json` 重新命名為 `emoji.json`
2. 自行上傳相關的表情符號至自己的伺服器
3. 將相對應的表情符號依照 Discord 格式填入到 `emoji.json` 檔案裡

註：
- Discord 表情符號格式：`<:表符名字:表符ID>`，例如：`<:Mora:979597026285200002>`
- 可以在 Discord 訊息頻道輸入 `\:表符名字:` 取得上述格式

</details>

## Sentry 配置說明

<details><summary>點此查看完整內容</summary>

非必要，Sentry 是用來追蹤程式執行中沒接到的例外，並將發生例外當時的函式呼叫、變數、例外...等詳細資訊傳送到網頁上供開發者追蹤，若不需要此功能的話可以跳過此設定

1. 到官網註冊帳號：https://sentry.io/
2. 在帳號內建立一個 Python 專案，建立後可取得該專案的 DSN 網址（格式：`https://xxx@xxx.sentry.io/xxx`）
3. 將此 DSN 網址貼到 `docker-compose.yml` 檔案的 `SENTRY_SDK_DSN` 欄位裡

註：
- 若沒有指定，Sentry 預設只發送沒有 try/except 的例外
- 若要將特定接到的例外發送到 Sentry 的話，請在該 except 內使用 `sentry_sdk.capture_exception(exception)`

</details>

## Admin 管理指令說明

<details><summary>點此查看完整內容</summary>

管理指令只能在配置檔案設定的測試伺服器內才能使用
```python
/status：顯示機器人狀態，包含延遲、已連接伺服器數量、已連接伺服器名稱
/system：立即開始每日簽到任務、下載 Enka 展示櫃新素材
/system precense 字串1,字串2,字串3,...：變更機器人顯示狀態(正在玩 ...)，每分鐘隨機變更為設定的其中一個字串，字串數量不限
/maintenance：設定遊戲維護時間，在此時間內自動排程(簽到、檢查樹脂)不會執行
/config：動態改動部分設定的值
```

另外，機器人包含了 `jsk` 指令可以做到載入/重載模組、同步指令、執行程式碼...等等，請參考 [jishaku 網站](https://github.com/Gorialis/jishaku) 說明。
要使用 jsk 指令，可以
 - 在機器人私訊內使用，例如：`$jsk ping`
 - 在一般頻道 tag 機器人使用，例如：`@原神小幫手 jsk ping`

</details>

## Prometheus / Grafana 監控儀錶板說明
<details><summary>點此查看完整內容</summary>

#### 儀表板展示圖

![](https://i.imgur.com/SOctABS.png)


總共需要三步驟，分別是
1. Grafana 官網辦帳號取得 API Key
2. 設定 Prometheus 伺服器
3. 在 Grafana 匯入儀表板 (Dashboard)

#### 1. Grafana 帳號辦理
1. 到 [Grafana 官網](https://grafana.com/) 註冊帳號，途中會讓你選 Cloud 地區，直接預設就可以

2. 辦完後回到 [官網](https://grafana.com/)，右上角選 My Account，如下圖可以看到 GRAFANA CLOUD 裡面有 Grafana 與 Prometheus，在 Prometheus 上選擇 Send Metrics
![](https://i.imgur.com/YLaV2fB.png)

3. 滑到頁面中間，在 Password / API Key 這裡選擇 Generate now，然後下面的 Sending metrics 黑底部分很重要，先留在這個頁面
![](https://i.imgur.com/RlY8ovi.png)

#### 2. 設定 Prometheus
1. 回到機器人資料夾，文字編輯器開啟 `docker-compose.yml` 檔案
    1. 最下方 `prometheus` 整段取消註解 (注意欄位格式要對齊)
    2. 機器人進階設定取消註解 `- PROMETHEUS_SERVER_PORT=9091`

2. 到 `data` 資料夾，文字編輯器開啟 `prometheus.yml` 檔案
3. 回到剛才 Grafana 網頁，你會看到網頁上的 `remote_write` 欄位與 `prometheus.yml` 檔案最底下相對應，將網頁上 `remote_write` 的設定內容一一填入到 `prometheus.yml` 內的對應欄位，然後存檔
```
remote_write:
- url: https://....(此行填入 Remote Write Endpoint)
  basic_auth:
    username: 123456(此行填入 Username / Instance ID)
    password: XXXXXX(此行填入 Password / API Key)
```
4. 重新運行機器人 `docker-compose up -d`

#### Grafana 匯入儀表板
有資料後，我們還需要讓資料顯示在儀表板上

1. 與 1-2 步驟一樣，回到 [官網](https://grafana.com/)，右上角選 My Account，這次我們在 Grafana 上按 Launch 啟動

2. 左邊選 Dashboards，然後右邊點選 New → Import，之後按 Upload JSON file 按鈕
![](https://i.imgur.com/6TFw9EM.png)

3. 到 `data` 資料夾，上傳 `grafana_dashboard.json` 到 Grafana 上面，也可以複製貼上到 Grafana

4. 成功匯入儀表板後，即可在儀表板上看到機器人的各項資料，到此完成結束

</details>

## 致謝
API：
- Hoyolab: https://github.com/thesadru/genshin.py
- Discord: https://github.com/Rapptz/discord.py
- Enka Network: https://github.com/EnkaNetwork/API-docs
- Mihomo: https://march7th.xiaohei.moe/en/resource/mihomo_api.html
- Genshin-DB: https://github.com/theBowja/genshin-db

Card：
- [hattvr/enka-card](https://github.com/hattvr/enka-card)
- [DEViantUA/HSRCard](https://github.com/DEViantUA/HSRCard)
- [DEViantUA/GenshinPyRail](https://github.com/DEViantUA/GenshinPyRail)

Misc：
- [Apollo-Roboto/discord.py-ext-prometheus](https://github.com/Apollo-Roboto/discord.py-ext-prometheus)
