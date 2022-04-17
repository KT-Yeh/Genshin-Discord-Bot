import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from utility.utils import log
from utility.config import config

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
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
        log.info(msg)
        await interaction.response.send_message(msg)

    # 廣播訊息到所有的伺服器
    @app_commands.command(name='broadcast', description='廣播訊息到所有的伺服器')
    @app_commands.rename(message='訊息')
    async def broadcast(self, interaction: discord.Interaction, message: str):
        for guild in self.bot.guilds:
            # 找出第一個可用的頻道發出訊息
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(message)
                    except Exception as e:
                        log.error(f'{guild}: {e}')
                        continue
                    else:
                        break
    
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
            msg = '、'.join([guild.name for guild in self.bot.guilds])
            embed = discord.Embed(title='已連接伺服器名稱', description=msg)
            await interaction.response.send_message(embed=embed)
    
    # 測試伺服器是否有 applications.commands 的 scope
    async def __hasAppCmdScope(self, guild: discord.Guild) -> bool:
        try:
            await self.bot.tree.sync(guild=guild)
        except discord.Forbidden:
            return False
        except Exception as e:
            log.error(f'{guild}: {e}')
            return False
        else:
            return True

async def setup(client: commands.Bot):
    await client.add_cog(Admin(client), guild=discord.Object(id=config.test_server_id))