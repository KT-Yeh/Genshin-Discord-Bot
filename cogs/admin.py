import discord
import random
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from pathlib import Path
from utility.utils import log
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
    async def sync(self, interaction: discord.Interaction, area: int = 0):
        if area == 0: # 複製全域指令，同步到當前伺服器，不需等待
            self.bot.tree.copy_global_to(guild=interaction.guild)
            result = await self.bot.tree.sync(guild=interaction.guild)
        else: # 同步到全域，需等待一小時
            result = await self.bot.tree.sync()
        
        msg = f'已同步以下指令到{"全部" if area == 1 else "當前"}伺服器\n{"、".join(cmd.name for cmd in result)}'
        log.info(f'[指令][Admin]sync(area={area}): {msg}')
        await interaction.response.send_message(msg)

    # 廣播訊息到所有的伺服器
    @app_commands.command(name='broadcast', description='廣播訊息到所有的伺服器')
    @app_commands.rename(message='訊息')
    async def broadcast(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        count = 0
        for guild in self.bot.guilds:
            # 找出第一個可用的頻道發出訊息
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(message)
                    except Exception as e:
                        log.error(f'[例外][Admin]broadcast: 頻道發送訊息失敗 [伺服器]{guild} [例外內容]{e}')
                        continue
                    else:
                        count += 1
                        break
        await interaction.edit_original_message(content=f'已廣播訊息到 {count} / {len(self.bot.guilds)} 伺服器')
    
    # 顯示機器人相關狀態
    @app_commands.command(name='status', description='顯示小幫手狀態')
    @app_commands.choices(option=[
        Choice(name='延遲', value=0),
        Choice(name='已連接伺服器數量', value=1),
        Choice(name='已連接伺服器名稱', value=2)])
    async def status(self, interaction: discord.Interaction, option: int):
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
    @app_commands.command(name='system', description='使用系統命令')
    @app_commands.rename(option='選項', param='參數')
    @app_commands.choices(option=[Choice(name='reload', value=0), Choice(name='presence', value=1)])
    async def system(self, interaction: discord.Interaction, option: int, param: str = None):
        # Reload cogs
        if option == 0:
            if param != None:
                try:
                    await self.bot.reload_extension(f'cogs.{param}')
                except Exception as e:
                    log.error(f'[例外][Admin]system reload {param}: {e}')
                    await interaction.response.send_message(f'[例外][Admin]system reload {param}: {e}')
                else:
                    await interaction.response.send_message(f'指令集 {param} 重新載入完成')
            else:
                # 從cogs資料夾載入所有cog
                try:
                    for filepath in Path('./cogs').glob('**/*.py'):
                        cog_name = Path(filepath).stem
                        await self.bot.reload_extension(f'cogs.{cog_name}')
                except Exception as e:
                    log.error(f'[例外][Admin]system reload all: {e}')
                    await interaction.response.send_message(f'[例外][Admin]system reload all: {e}')
                else:
                    await interaction.response.send_message('全部指令集重新載入完成')
        # Change presence string
        elif option == 1:
            self.presence_string = param.split(',')
            await interaction.response.send_message(f'Presence list已變更為：{self.presence_string}')

    @tasks.loop(minutes=5)
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
    
    # 測試伺服器是否有 applications.commands 的 scope
    async def __hasAppCmdScope(self, guild: discord.Guild) -> bool:
        try:
            await self.bot.tree.sync(guild=guild)
        except discord.Forbidden:
            return False
        except Exception as e:
            log.error(f'[例外][Admin]Admin > __hasAppCmdScope: [伺服器]{guild} [例外內容]{e}')
            return False
        else:
            return True

async def setup(client: commands.Bot):
    await client.add_cog(Admin(client), guild=discord.Object(id=config.test_server_id))