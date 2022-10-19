import asyncio
import discord
import shutil
import sentry_sdk
from datetime import datetime, date, timedelta
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from utility.config import config
from utility.utils import log, EmbedTemplate, getAppCommandMention
from utility.GenshinApp import genshin_app
from data.database import db, ScheduleDaily, ScheduleResin

class Schedule(commands.Cog, name='自動化'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.schedule.start()
    
    async def cog_unload(self) -> None:
        self.schedule.cancel()

    class ChooseGameButton(discord.ui.View):
        """選擇自動簽到遊戲的按鈕"""
        def __init__(self, author: discord.Member):
            super().__init__(timeout=config.discord_view_short_timeout)
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

    class DailyMentionButton(discord.ui.View):
        """每日簽到是否要tag使用者"""
        def __init__(self, author: discord.Member):
            super().__init__(timeout=config.discord_view_short_timeout)
            self.value = True
            self.author = author
        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id
        
        @discord.ui.button(label='好！', style=discord.ButtonStyle.blurple)
        async def option1(self, interaction: discord.Interaction, button: discord.ui.button):
            await interaction.response.defer()
            self.value = True
            self.stop()
        
        @discord.ui.button(label='不用', style=discord.ButtonStyle.blurple)
        async def option2(self, interaction: discord.Interaction, button: discord.ui.button):
            await interaction.response.defer()
            self.value = False
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
        function=[Choice(name='① 顯示使用說明', value='help'),
                  Choice(name='② 訊息推送測試', value='test'),
                  Choice(name='★ 每日自動簽到', value='daily'),
                  Choice(name='★ 樹脂額滿提醒', value='resin')],
        switch=[Choice(name='開啟功能', value=1),
                Choice(name='關閉功能', value=0)])
    async def slash_schedule(self, interaction: discord.Interaction, function: str, switch: int):
        log.info(f'[指令][{interaction.user.id}]schedule(function={function}, switch={switch})')
        if function == 'help': # 排程功能使用說明
            msg = ('· 排程會在特定時間執行功能，執行結果會在設定指令的頻道推送\n'
            '· 設定前請先確認小幫手有在該頻道發言的權限，如果推送訊息失敗，小幫手會自動移除排程設定\n'
            '· 若要更改推送頻道，請在新的頻道重新設定指令一次\n\n'
            f'· 每日簽到：每日 {config.schedule_daily_reward_time}~{config.schedule_daily_reward_time+3} 點之間自動論壇簽到，設定前請先使用 {getAppCommandMention("daily每日簽到")} 指令確認小幫手能正確幫你簽到\n'
            f'· 樹脂提醒：每小時檢查一次，當樹脂超過 {config.schedule_check_resin_threshold} 會發送提醒，設定前請先用 {getAppCommandMention("notes即時便箋")} 指令確認小幫手能讀到你的樹脂資訊\n')
            await interaction.response.send_message(embed=EmbedTemplate.normal(msg, title='排程功能使用說明'), ephemeral=True)
            return
        
        if function == 'test': # 測試機器人是否能在該頻道推送訊息
            try:
                msg_sent = await interaction.channel.send('測試推送訊息...')
            except:
                await interaction.response.send_message(embed=EmbedTemplate.error('小幫手無法在本頻道推送訊息，請管理員檢查身分組的權限設定'))
            else:
                await interaction.response.send_message(embed=EmbedTemplate.normal('測試完成，小幫手可以在本頻道推送訊息'))
                await msg_sent.delete()
            return
        
        # 設定前先確認使用者是否有Cookie資料
        user = await db.users.get(interaction.user.id)
        check, msg = await db.users.exist(user)
        if check == False:
            await interaction.response.send_message(embed=EmbedTemplate.error(msg))
            return
        if function == 'daily': # 每日自動簽到
            if switch == 1: # 開啟簽到功能
                choose_game_btn = self.ChooseGameButton(interaction.user)
                await interaction.response.send_message('請選擇要自動簽到的遊戲：', view=choose_game_btn)
                await choose_game_btn.wait()
                if choose_game_btn.value == None: 
                    await interaction.edit_original_response(embed=EmbedTemplate.normal('已取消') ,content=None, view=None)
                    return
                
                daily_mention_btn = self.DailyMentionButton(interaction.user)
                await interaction.edit_original_response(content=f'每日自動簽到時希望小幫手tag你({interaction.user.mention})嗎？', view=daily_mention_btn)
                await daily_mention_btn.wait()
                
                # 新增使用者
                await db.schedule_daily.add(ScheduleDaily(
                    id=interaction.user.id,
                    channel_id=interaction.channel_id,
                    is_mention=daily_mention_btn.value,
                    has_honkai=(True if choose_game_btn.value == '原神+崩3' else False))
                )
                await interaction.edit_original_response(embed=EmbedTemplate.normal(
                    f'{choose_game_btn.value}每日自動簽到已開啟，簽到時小幫手{"會" if daily_mention_btn.value else "不會"}tag你 (今日已幫你簽到)'), content=None, view=None)
                # 設定完成後幫使用者當日簽到
                await genshin_app.claimDailyReward(interaction.user.id, honkai=(choose_game_btn.value == '原神+崩3'))
            elif switch == 0: # 關閉簽到功能
                await db.schedule_daily.remove(interaction.user.id)
                await interaction.response.send_message(embed=EmbedTemplate.normal('每日自動簽到已關閉'))
        elif function == 'resin': # 樹脂額滿提醒
            if switch == 1: # 開啟檢查樹脂功能
                await db.schedule_resin.add(ScheduleResin(
                    id=interaction.user.id,
                    channel_id=interaction.channel_id)
                )
                await interaction.response.send_message(embed=EmbedTemplate.normal('樹脂額滿提醒已開啟'))
            elif switch == 0: # 關閉檢查樹脂功能
                await db.schedule_resin.remove(interaction.user.id)
                await interaction.response.send_message(embed=EmbedTemplate.normal('樹脂額滿提醒已關閉'))

    # 具有頻道管理訊息權限的人可使用本指令，移除指定使用者的頻道排程設定
    @app_commands.command(name='移除排程使用者', description='擁有管理此頻道訊息權限的人可使用本指令，移除指定使用者的排程設定')
    @app_commands.rename(function='功能', user='使用者')
    @app_commands.describe(function='選擇要移除的功能')
    @app_commands.choices(
        function=[Choice(name='每日自動簽到', value='daily'),
                  Choice(name='樹脂額滿提醒', value='resin')])
    @app_commands.default_permissions(manage_messages=True)
    async def slash_remove_user(self, interaction: discord.Interaction, function: str, user: discord.User):
        log.info(f'[指令][{interaction.user.id}]移除排程使用者(function={function}, user={user.id})')
        if function == 'daily':
            await db.schedule_daily.remove(user.id)
            await interaction.response.send_message(embed=EmbedTemplate.normal(f'{user.display_name}的每日自動簽到已關閉'))
        elif function == 'resin':
            await db.schedule_resin.remove(user.id)
            await interaction.response.send_message(embed=EmbedTemplate.normal(f'{user.display_name}的樹脂額滿提醒已關閉'))

    loop_interval = 1 # 循環間隔1分鐘
    @tasks.loop(minutes=loop_interval)
    async def schedule(self):
        now = datetime.now()
        # 確認沒有在遊戲維護時間內
        if config.game_maintenance_time == None or not(config.game_maintenance_time[0] <= now < config.game_maintenance_time[1]):
            # 每日 {config.schedule_daily_reward_time} 點自動簽到
            if now.hour == config.schedule_daily_reward_time and now.minute < self.loop_interval:
                asyncio.create_task(self.autoClaimDailyReward())
            
            # 每小時檢查一次樹脂
            if now.minute < self.loop_interval:
                asyncio.create_task(self.autoCheckResin())

        # 每日凌晨一點備份資料庫、刪除過期使用者資料
        if now.hour == 1 and now.minute < self.loop_interval:
            try:
                shutil.copyfile('data/bot.db', 'data/bot_backup.db')
            except Exception as e:
                log.warning(str(e))
                sentry_sdk.capture_exception(e)
            
            asyncio.create_task(db.removeExpiredUser(config.expired_user_days))

    @schedule.before_loop
    async def before_schedule(self):
        await self.bot.wait_until_ready()

    async def autoClaimDailyReward(self):
        log.info('[排程][System]schedule: 每日自動簽到開始')
        daily_users = await db.schedule_daily.getAll()
        total, honkai_count = 0, 0 # 統計簽到人數
        for user in daily_users:
            # 檢查今天是否已經簽到過
            if user.last_checkin_date == date.today():
                continue
            # 取得要發送的頻道
            channel = self.bot.get_channel(user.channel_id)
            # 檢查使用者資料
            check, msg = await db.users.exist(await db.users.get(user.id), update_using_time=False)
            # 若發送頻道或使用者資料不存在，則移除此使用者
            if channel == None or check == False:
                await db.schedule_daily.remove(user.id)
                continue
            # 簽到並更新最後簽到時間
            result = await genshin_app.claimDailyReward(user.id, honkai=user.has_honkai, schedule=True)
            await db.schedule_daily.update(user.id, last_checkin_date=True)
            total += 1
            honkai_count += int(user.has_honkai)
            try:
                # 若不用@提及使用者，則先取得此使用者的暱稱然後發送訊息
                if user.is_mention == False:
                    user = await self.bot.fetch_user(user.id)
                    await channel.send(f'[自動簽到] {user.display_name}：{result}')
                else:
                    await channel.send(f'[自動簽到] <@{user.id}> {result}')
            except Exception as e: # 發送訊息失敗，移除此使用者
                log.warning(f'[排程][{user.id}]自動簽到：{e}')
                await db.schedule_daily.remove(user.id)
            await asyncio.sleep(config.schedule_loop_delay)
        log.info(f'[排程][System]schedule: 每日自動簽到結束，總共 {total} 人簽到，其中 {honkai_count} 人也簽到崩壞3')

    async def autoCheckResin(self):
        log.info('[排程][System]schedule: 自動檢查樹脂開始')
        resin_users = await db.schedule_resin.getAll()
        count = 0 # 統計人數
        for user in resin_users:
            # 若還沒到檢查時間則跳過此使用者
            if datetime.now() < user.next_check_time:
                continue
            
            # 取得要發送訊息的頻道與確認使用者資料，若頻道或使用者資料不存在，則移除此使用者
            channel = self.bot.get_channel(user.channel_id)
            check, msg = await db.users.exist(await db.users.get(user.id), update_using_time=False)
            if channel == None or check == False:
                await db.schedule_resin.remove(user.id)
                continue
            # 檢查使用者樹脂
            try:
                notes = await genshin_app.getRealtimeNote(user.id, schedule=True)
            except Exception as e:
                msg = f"自動檢查樹脂時發生錯誤：{str(e)}"
                # 當發生錯誤時，預計5小時後再檢查
                await db.schedule_resin.update(user.id, next_check_time=(datetime.now() + timedelta(hours=5)))
                embed = None
            else: # 正常檢查樹脂
                # 當樹脂超過設定值，則設定要發送的訊息
                if notes.current_resin >= config.schedule_check_resin_threshold:
                    msg = "樹脂(快要)溢出啦！"
                    embed = await genshin_app.parseNotes(notes, shortForm=True)
                else:
                    msg = None
                # 設定下次檢查時間，當樹脂完全額滿時，預計6小時後再檢查；否則依照樹脂差額預估時間
                minutes = 350 if notes.current_resin >= notes.max_resin else (config.schedule_check_resin_threshold - notes.current_resin) * 8 - 10
                await db.schedule_resin.update(user.id, next_check_time=(datetime.now() + timedelta(minutes=minutes)))
            count += 1
            # 當有錯誤訊息或是樹脂快要溢出時，向使用者發送訊息
            if msg != None:
                try: # 發送訊息提醒使用者
                    user = await self.bot.fetch_user(user.id)
                    msg_sent = await channel.send(f"{user.mention}，{msg}", embed=embed)
                except Exception as e: # 發送訊息失敗，移除此使用者
                    log.info(f'[例外][{user.id}]排程檢查樹脂發送訊息：{e}')
                    await db.schedule_resin.remove(user.id)
                else:
                    # 若使用者不在發送訊息的頻道則移除
                    if user.mentioned_in(msg_sent) == False:
                        log.info(f'[排程][{user.id}]檢查樹脂：使用者不在頻道')
                        await db.schedule_resin.remove(user.id)
            await asyncio.sleep(config.schedule_loop_delay)
        log.info(f'[排程][System]schedule: 自動檢查樹脂結束，{count}/{len(resin_users)} 人已檢查')

async def setup(client: commands.Bot):
    await client.add_cog(Schedule(client))