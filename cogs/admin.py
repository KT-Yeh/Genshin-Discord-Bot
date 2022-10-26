import discord
import random
import typing
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from pathlib import Path
from utility.CustomLog import SlashCommandLogger
from utility.config import config

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.presence_string: list[str] = ['原神']
        self.change_presence.start()
    
    # 同步 Slash commands 到全域或是當前伺服器
    @app_commands.command(name='sync', description='同步Slash commands到全域或是當前伺服器')
    @app_commands.rename(area='範圍')
    @app_commands.choices(area=[Choice(name='當前伺服器', value=0), Choice(name='全域伺服器', value=1)])
    @SlashCommandLogger
    async def slash_sync(self, interaction: discord.Interaction, area: int = 0):
        await interaction.response.defer()
        if area == 0: # 複製全域指令，同步到當前伺服器，不需等待
            self.bot.tree.copy_global_to(guild=interaction.guild)
            result = await self.bot.tree.sync(guild=interaction.guild)
        else: # 同步到全域，需等待一小時
            result = await self.bot.tree.sync()
        
        msg = f'已同步以下指令到{"全部" if area == 1 else "當前"}伺服器：{"、".join(cmd.name for cmd in result)}'
        await interaction.edit_original_response(msg)
    
    # 顯示機器人相關狀態
    @app_commands.command(name='status', description='顯示小幫手狀態')
    @app_commands.choices(option=[
        Choice(name='延遲', value=0),
        Choice(name='已連接伺服器數量', value=1),
        Choice(name='已連接伺服器名稱', value=2)])
    @SlashCommandLogger
    async def slash_status(self, interaction: discord.Interaction, option: int):
        if option == 0:
            await interaction.response.send_message(f'延遲：{round(self.bot.latency*1000)} 毫秒')
        elif option == 1:
            await interaction.response.send_message(f'已連接 {len(self.bot.guilds)} 個伺服器')
        elif option == 2:
            await interaction.response.defer()
            names = [guild.name for guild in self.bot.guilds]
            for i in range(0, len(self.bot.guilds), 100):
                msg = '、'.join(names[i : i + 100])
                embed = discord.Embed(title=f'已連接伺服器名稱({i + 1})', description=msg)
                await interaction.followup.send(embed=embed)
    
    # 使用系統命令
    @app_commands.command(name='system', description='使用系統命令(操作cog、更改機器人狀態)')
    @app_commands.rename(option='選項', param='參數')
    @app_commands.choices(option=[
        Choice(name='load', value=0),
        Choice(name='unload', value=1),
        Choice(name='reload', value=2),
        Choice(name='presence', value=3)
    ])
    @SlashCommandLogger
    async def slash_system(self, interaction: discord.Interaction, option: int, param: str = None):
        async def operateCogs(func: typing.Callable[[str], typing.Awaitable[None]], param: typing.Optional[str] = None, *, pass_self: bool = False):
            if param == None: # 操作全部cog
                for filepath in Path('./cogs').glob('**/*.py'):
                    cog_name = Path(filepath).stem
                    if pass_self and cog_name == 'admin':
                        continue
                    await func(f"cogs.{cog_name}")
            else: # 操作單一cog
                await func(f"cogs.{param}")
        
        if option == 0: # Load cogs
            await operateCogs(self.bot.load_extension, param, pass_self=True)
            await interaction.response.send_message(f"{param or '全部'}指令集載入完成")
        
        elif option == 1: # Unload cogs
            await operateCogs(self.bot.unload_extension, param, pass_self=True)
            await interaction.response.send_message(f"{param or '全部'}指令集卸載完成")
        
        elif option == 2: # Reload cogs
            await operateCogs(self.bot.reload_extension, param)
            await interaction.response.send_message(f"{param or '全部'}指令集重新載入完成")
        
        elif option == 3: # Change presence string
            self.presence_string = param.split(',')
            await interaction.response.send_message(f'Presence list已變更為：{self.presence_string}')
    
    # 設定config配置檔案的參數值
    @app_commands.command(name='config', description='更改config配置內容')
    @app_commands.rename(option='選項', value='值')
    @app_commands.choices(option=[
        Choice(name='schedule_daily_reward_time', value='schedule_daily_reward_time'),
        Choice(name='schedule_check_resin_threshold', value='schedule_check_resin_threshold'),
        Choice(name='schedule_loop_delay', value='schedule_loop_delay')
    ])
    @SlashCommandLogger
    async def slash_config(self, interaction: discord.Interaction, option: str, value: str):
        if option in ['schedule_daily_reward_time', 'schedule_check_resin_threshold']:
            setattr(config, option, int(value))
        elif option in ['schedule_loop_delay']:
            setattr(config, option, float(value))
        await interaction.response.send_message(f"已將{option}的值設為: {value}")

    @app_commands.command(name='maintenance', description='設定遊戲維護時間，輸入0表示將維護時間設定為關閉')
    @app_commands.rename(month='月', day='日', hour='點', duration='維護幾小時')
    @SlashCommandLogger
    async def slash_maintenance(self, interaction: discord.Interaction, month: int, day: int, hour: int = 6, duration: int = 5):
        if month == 0 or day == 0:
            config.game_maintenance_time = None
            await interaction.response.send_message('已將維護時間設定為：關閉')
        else:
            now = datetime.now()
            start_time = datetime((now.year if month >= now.month else now.year + 1), month, day, hour)
            end_time = start_time + timedelta(hours=duration)
            config.game_maintenance_time = (start_time, end_time)
            await interaction.response.send_message(f"已將維護時間設定為：{start_time} ~ {end_time}")

    # 每一定時間更改機器人狀態
    @tasks.loop(minutes=1)
    async def change_presence(self):
        l = len(self.presence_string)
        n = random.randint(0, l)
        if n < l:
            await self.bot.change_presence(activity=discord.Game(self.presence_string[n]))
        elif n == l:
            await self.bot.change_presence(activity=discord.Game(f'{len(self.bot.guilds)} 個伺服器'))

    @change_presence.before_loop
    async def before_change_presence(self):
        await self.bot.wait_until_ready()

async def setup(client: commands.Bot):
    await client.add_cog(Admin(client), guild=discord.Object(id=config.test_server_id))