# Genshin Discord Bot
This branch uses discord.py v1.7.3, which is the old API

At present, the bot development has been converted to the pre-discord.py v2.0 version, please refer to the [v2.0 branch](https://github.com/KT-Yeh/Genshin-Discord-Bot/tree/discord.py_v2.0 )

When the official version of discord.py v2.0 is released, the branch will be merged back to master

## Introduction
Use the Discord bot to directly query various information in Genshin Impact, including:
- Query instant notes, including resin, Dongtianbao money, exploration dispatch...etc
- Resin overflow reminder
- Query the deep spiral record
- Check traveler's notes
- Hoyolab automatic daily check-in
- Hoyolab use redemption code

## Example
![](https://i.imgur.com/QQLBbUn.png)
![](https://i.imgur.com/Ye0HA0G.png)
![](https://i.imgur.com/qHzbvH0.png)
![](https://i.imgur.com/bNY19NW.png)

## public bots
[![](https://i.imgur.com/ULhx0EP.png)](https://bit.ly/Invitation from Genshin Impact)

#### Invitation link: https://bit.ly/Yuanshen Little Helper Invitation
- For multi-player servers, ask someone with administrative rights to invite the robot
- Personal use can create a Discord server with only yourself, and then invite bots

## Install & build the robot yourself

### Web page
1. Go to [Discord Developer](https://discord.com/developers/applications "Discord Developer") and log in to your Discord account

![](https://i.imgur.com/dbDHEM3.png)

2. Click "New Application" to create an application, enter the desired name and click "Create"

![](https://i.imgur.com/BcJcSnU.png)

3. On the Bot page, click "Add Bot" to add a bot

![](https://i.imgur.com/lsIgGCi.png)

4. In OAuth2/URL Generator, check "Bot", "Send Messages" and "Manage Messages" respectively. The URL link generated at the bottom is the robot's invitation link. Open the link to invite the robot to your own server.

![](https://i.imgur.com/08fcHs0.png)

5. Go back to the Bot page, press "Reset Token" to get and copy the Bot's Token, which will be used later

![](https://i.imgur.com/BfzjewI.png)


### Local (choose docker or general method)
#### docker method (recommended, no need to install python and suite environment by yourself)
1. Download and install [docker](https://www.docker.com/get-started/)
2. Download [this project](https://github.com/KT-Yeh/Genshin-Discord-Bot/archive/refs/heads/master.zip)
3. In the project folder (Genshin-Discord-Bot), use a text editor to open the `.env(example)` file, paste the Token just obtained after the `BOT_TOKEN=` field, and save the file as ` .env`
4. Open cmd or powershell in the project folder and enter the following docker-compose command
    ````python
    # run in foreground (close terminal = close bot)
    docker-compose up
    
    # run in the background (close docker = close bot, you can close the terminal)
    docker-compose up -d
    
    # View the output of the bot
    docker-compose logs -f
    
    # close the bot
    docker-compose down
    ````

#### General way
1. Download [this project](https://github.com/KT-Yeh/Genshin-Discord-Bot/archive/refs/heads/master.zip)
2. Download and install Python (version 3.8 and above): https://www.python.org/downloads/
3. In the project folder (Genshin-Discord-Bot), use a text editor to open the `.env(example)` file, paste the Token just obtained after the `BOT_TOKEN=` field, and save the file as ` .env`
4. Open cmd or powershell in the project folder, and enter the following commands to install the relevant packages:
````
pip3 install -r requirements.txt
````
5. Enter the following command or double-click to open the main.py file and start running the robot
````
python .\main.py
````


## Configuration file description (.env)
````python
BOT_TOKEN=ABCDEFG # Robot Token, which needs to be obtained from the Discord webpage
BOT_PREFIX=% # Robot command prefix
BOT_COOLDOWN=3 # Cooldown time for the robot to receive commands from the same user (unit: seconds)
AUTO_DAILY_REWARD_TIME=8 # Daily Hoyolab automatic check-in time (unit: hour)
AUTO_CHECK_RESIN_THRESHOLD=150 # Check every hour, send a reminder when how much resin is exceeded
````

## Thanks
Concept inspired by: https://github.com/Xm798/Genshin-Dailynote-Helper

API used from: https://github.com/thesadru/genshin.py
