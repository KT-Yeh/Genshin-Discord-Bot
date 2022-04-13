import discord
from discord.ext import commands
from typing import Optional, Literal
from utility.utils import log

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
    # 廣播訊息到所有的伺服器
    @commands.command(hidden=True)
    @commands.is_owner()
    async def broadcast(self, ctx: commands.Context, *msg):
        msg = ' '.join(msg)
        log.info(msg)
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

def setup(client: commands.Bot):
    client.add_cog(Admin(client))