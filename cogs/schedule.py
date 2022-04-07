import json
import asyncio
from datetime import datetime
from utility.GenshinApp import genshin_app
from discord.ext import commands, tasks
from utility.config import config
from utility.utils import log

class Schedule(commands.Cog, name='自動排程(BETA)'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.__daily_reward_filename = 'data/schedule_daily_reward.json'
        try:
            with open(self.__daily_reward_filename, 'r', encoding='utf-8') as f:
                self.__daily_dict = json.load(f)
        except:
            self.__daily_dict = { }
        
        self.schedule.start()

    @commands.command(
        brief='設定自動排程功能',
        description='設定自動排程功能，會在特定時間執行功能，執行結果會在當初設定的頻道推送，若要更改頻道，請在新頻道重新設定一次',
        usage='<daily> <on|off>',
        help=f'每日 {config.auto_daily_reward_time} 點左右自動簽到，使用範例：\n\n'
            f'　{config.bot_prefix}set daily on　　　開啟每日自動簽到\n'
            f'　{config.bot_prefix}set daily off 　　關閉每日自動簽到'
    )
    async def set(self, ctx, cmd: str, switch: str):
        log.info(f'set(user_id={ctx.author.id}, cmd={cmd} , switch={switch})')
        if cmd == 'daily':
            if switch == 'on':
                check, msg = genshin_app.checkUserData(str(ctx.author.id))
                if check:
                    self.__add_user(str(ctx.author.id), str(ctx.channel.id), self.__daily_dict)
                    msg = '每日自動簽到已開啟'
                await ctx.reply(msg)
            elif switch == 'off':
                self.__remove_user(str(ctx.author.id), self.__daily_dict)
                await ctx.reply('每日自動簽到已關閉')

    @tasks.loop(minutes=10)
    async def schedule(self):
        log.info(f'schedule() is called')
        now = datetime.now()
        # 每日 X 點自動簽到
        if now.hour == config.auto_daily_reward_time and now.minute < 10:
            # 複製一份避免衝突
            log.info('每日自動簽到開始')
            daily_dict = dict(self.__daily_dict)
            for user_id, value in daily_dict.items():
                channel = self.bot.get_channel(int(value['channel']))
                if channel == None:
                    self.__remove_user(str(user_id), self.__daily_dict)
                    continue
                result = await genshin_app.claimDailyReward(user_id)
                await channel.send(f'[自動簽到] <@{user_id}> {result}')
                await asyncio.sleep(3)
            log.info('每日自動簽到結束')

    @schedule.before_loop
    async def before_schedule(self):
        await self.bot.wait_until_ready()

    def __add_user(self, user_id: str, channel: str, data: dict) -> None:
        if data is self.__daily_dict:
            self.__daily_dict[user_id] = { }
            self.__daily_dict[user_id]['channel'] = channel
            self.__saveScheduleData(self.__daily_dict, self.__daily_reward_filename)

    def __remove_user(self, user_id: str, data: dict) -> None:
        if data is self.__daily_dict:
            try:
                del self.__daily_dict[user_id]
            except:
                log.error(f'__remove_user(self, user_id={user_id}, data: dict)')
            else:
                self.__saveScheduleData(self.__daily_dict, self.__daily_reward_filename)
    
    def __saveScheduleData(self, data: dict, filename: str):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except:
            log.error(f'__saveScheduleData(data: dict, filename: {filename})')

def setup(client):
    client.add_cog(Schedule(client))