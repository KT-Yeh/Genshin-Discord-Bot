import discord
from discord.ext import commands
from typing import Optional, Literal
from utility.utils import log

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
    # 同步 Slash commands 到全域或是當前伺服器
    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: Optional[Literal['~']] = None):
        if spec == '~': # 同步到全域，需等待一小時
            result = await ctx.bot.tree.sync()
        else: # 複製全域指令，同步到當前伺服器，不需等待
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            result = await ctx.bot.tree.sync(guild=ctx.guild)

        msg = f'已同步以下指令到{"全部" if spec == "~" else "當前"}伺服器\n{" ".join(cmd.name for cmd in result)}'
        log.info(msg)
        await ctx.send(msg)
    
    # 廣播訊息到所有的伺服器
    @commands.command(hidden=True)
    @commands.is_owner()
    async def broadcast(self, ctx: commands.Context, *msg):
        msg = ' '.join(msg)
        for guild in self.bot.guilds:
            # 找出第一個可用的頻道發出訊息
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(msg)
                    except Exception as e:
                        log.error(f'{guild}: {e}')
                        continue
                    else:
                        break
    
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
    await client.add_cog(Admin(client))