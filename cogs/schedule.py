import json
import asyncio
import discord
from datetime import datetime
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from utility.config import config
from utility.utils import log, user_last_use_time
from utility.GenshinApp import genshin_app

class Schedule(commands.Cog, name='自動化(BETA)'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.__daily_reward_filename = 'data/schedule_daily_reward.json'
        self.__resin_notifi_filename = 'data/schedule_resin_notification.json'
        try:
            with open(self.__daily_reward_filename, 'r', encoding='utf-8') as f:
                self.__daily_dict: dict[str, dict[str, str]] = json.load(f)
        except:
            self.__daily_dict: dict[str, dict[str, str]] = { }
        try:
            with open(self.__resin_notifi_filename, 'r', encoding='utf-8') as f:
                self.__resin_dict: dict[str, dict[str, str]] = json.load(f)
        except:
            self.__resin_dict: dict[str, dict[str, str]] = { }
        
        self.schedule.start()
    
    class ChooseGameButton(discord.ui.View):
        """選擇自動簽到遊戲的按鈕"""
        def __init__(self, author: discord.Member, *, timeout: float = 30):
            super().__init__(timeout=timeout)
            self.value = None
            self.author = author
        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id
        
        @discord.ui.button(label='原神', style=discord.ButtonStyle.blurple)
        async def option1(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            self.value = '原神'
            self.stop()
        
        @discord.ui.button(label='原神+崩3', style=discord.ButtonStyle.blurple)
        async def option2(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            self.value = '原神+崩3'
            self.stop()

    # 設定自動排程功能
    @app_commands.command(
        name='schedule排程',
        description='設定自動化功能(Hoyolab每日簽到、樹脂額滿提醒)')
    @app_commands.rename(function='功能', switch='開關')
    @app_commands.describe(
        function='選擇要執行自動化的功能',
        switch='選擇開啟或關閉此功能')
    @app_commands.choices(
        function=[Choice(name='顯示排程功能使用說明', value='help'),
                  Choice(name='每日自動簽到', value='daily'),
                  Choice(name='樹脂額滿提醒', value='resin')],
        switch=[Choice(name='開啟功能', value=1),
                Choice(name='關閉功能', value=0)])
    async def slash_schedule(self, interaction: discord.Interaction, function: str, switch: int):
        log.info(f'[指令][{interaction.user.id}]schedule(function={function} , switch={switch})')
        if function == 'help': # 排程功能使用說明
            msg = ('· 排程會在特定時間執行功能，執行結果會在設定指令的頻道推送\n'
            '· 設定前請先確認小幫手有在該頻道發言的權限，如果推送訊息失敗，小幫手會自動移除排程設定\n'
            '· 若要更改推送頻道，請在新的頻道重新設定指令一次\n\n'
            f'· 每日簽到：每日 {config.auto_daily_reward_time}~{config.auto_daily_reward_time+1} 點之間自動論壇簽到，設定前請先使用 /daily每日簽到 指令確認小幫手能正確幫你簽到\n'
            f'· 樹脂提醒：每小時檢查一次，當樹脂超過 {config.auto_check_resin_threshold} 時會發送提醒，設定前請先用 /notes即時便箋 指令確認小幫手能讀到你的樹脂資訊\n')
            await interaction.response.send_message(embed=discord.Embed(title='排程功能使用說明', description=msg))
            return
        # 確認使用者Cookie資料
        check, msg = genshin_app.checkUserData(str(interaction.user.id))
        if check == False:
            await interaction.response.send_message(msg)
            return
        if function == 'daily': # 每日自動簽到
            if switch == 1: # 開啟簽到功能
                view = self.ChooseGameButton(interaction.user)
                await interaction.response.send_message('請選擇要自動簽到的遊戲：', view=view)
                await view.wait()
                if view.value == None: 
                    await interaction.edit_original_message(content='已取消', view=None)
                    return
                # 新增使用者
                self.__add_user(str(interaction.user.id), str(interaction.channel_id), self.__daily_dict, self.__daily_reward_filename)
                if view.value == '原神+崩3': # 新增崩壞3使用者
                    self.__add_honkai_user(str(interaction.user.id), self.__daily_dict, self.__daily_reward_filename)
                await interaction.edit_original_message(content='已選擇', view=None)
                await interaction.followup.send(f'{view.value}每日自動簽到已開啟')
            elif switch == 0: # 關閉簽到功能
                self.__remove_user(str(interaction.user.id), self.__daily_dict, self.__daily_reward_filename)
                await interaction.response.send_message('每日自動簽到已關閉')
        elif function == 'resin': # 樹脂額滿提醒
            if switch == 1: # 開啟檢查樹脂功能
                self.__add_user(str(interaction.user.id), str(interaction.channel_id), self.__resin_dict, self.__resin_notifi_filename)
                await interaction.response.send_message('樹脂額滿提醒已開啟')
            elif switch == 0: # 關閉檢查樹脂功能
                self.__remove_user(str(interaction.user.id), self.__resin_dict, self.__resin_notifi_filename)
                await interaction.response.send_message('樹脂額滿提醒已關閉')

    loop_interval = 10
    @tasks.loop(minutes=loop_interval)
    async def schedule(self):
        now = datetime.now()
        # 每日 X 點自動簽到
        if now.hour == config.auto_daily_reward_time and now.minute < self.loop_interval:
            log.info('[排程][System]schedule: 每日自動簽到開始')
            # 複製一份避免衝突
            daily_dict = dict(self.__daily_dict)
            count = 0
            for user_id, value in daily_dict.items():
                channel = self.bot.get_channel(int(value['channel']))
                has_honkai = False if value.get('honkai') == None else True
                check, msg = genshin_app.checkUserData(user_id)
                if channel == None or check == False:
                    self.__remove_user(user_id, self.__daily_dict, self.__daily_reward_filename)
                    continue
                result = await genshin_app.claimDailyReward(user_id, honkai=has_honkai)
                count += 1
                try:
                    await channel.send(f'[自動簽到] <@{user_id}> {result}')
                except:
                    self.__remove_user(user_id, self.__daily_dict, self.__daily_reward_filename)
                await asyncio.sleep(5)
            log.info(f'[排程][System]schedule: 每日自動簽到結束，{count} 人已簽到')
        
        # 每小時檢查樹脂
        if 30 <= now.minute < 30 + self.loop_interval:
            log.info('[排程][System]schedule: 自動檢查樹脂開始')
            resin_dict = dict(self.__resin_dict)
            count = 0
            for user_id, value in resin_dict.items():
                channel = self.bot.get_channel(int(value['channel']))
                check, msg = genshin_app.checkUserData(user_id)
                if channel == None or check == False:
                    self.__remove_user(user_id, self.__resin_dict, self.__resin_notifi_filename)
                    continue
                result = await genshin_app.getRealtimeNote(user_id, True)
                count += 1
                if result != None:
                    embed = discord.Embed(title='', description=result, color=0xff2424)
                    try:
                        await channel.send(f'<@{user_id}>，樹脂(快要)溢出啦！', embed=embed)
                    except:
                        self.__remove_user(user_id, self.__resin_dict, self.__resin_notifi_filename)
                await asyncio.sleep(5)
            log.info(f'[排程][System]schedule: 自動檢查樹脂結束，{count} 人已檢查')
        
        user_last_use_time.save() # 定時儲存使用者最後使用時間資料
        # 每日刪除過期使用者資料
        if now.hour == 1 and now.minute < self.loop_interval:
            genshin_app.deleteExpiredUserData()

    @schedule.before_loop
    async def before_schedule(self):
        await self.bot.wait_until_ready()

    def __add_user(self, user_id: str, channel: str, data: dict, filename: str) -> None:
        data[user_id] = { }
        data[user_id]['channel'] = channel
        self.__saveScheduleData(data, filename)
    
    def __add_honkai_user(self, user_id: str, data: dict, filename: str) -> None:
        """加入崩壞3簽到到現有的使用者，使用前請先確認已有該使用者資料"""
        if data.get(user_id) != None:
            data[user_id]['honkai'] = 'True'
            self.__saveScheduleData(data, filename)

    def __remove_user(self, user_id: str, data: dict, filename: str) -> None:
        try:
            del data[user_id]
        except:
            log.info(f'[例外][System]Schedule > __remove_user(user_id={user_id}): 使用者不存在')
        else:
            self.__saveScheduleData(data, filename)
    
    def __saveScheduleData(self, data: dict, filename: str):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except:
            log.error(f'[例外][System]Schedule > __saveScheduleData(filename={filename}): 存檔寫入失敗')

async def setup(client: commands.Bot):
    await client.add_cog(Schedule(client))