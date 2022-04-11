from discord.ext import commands
from typing import Optional, Literal
from utility.utils import log

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: Optional[Literal['~']] = None):
        if spec == '~':
            result = await ctx.bot.tree.sync()
        else:
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            result = await ctx.bot.tree.sync(guild=ctx.guild)

        msg = f'已同步以下指令到{"全部" if spec == "~" else "當前"}伺服器\n{" ".join(cmd.name for cmd in result)}'
        log.info(msg)
        await ctx.send(msg)

async def setup(client: commands.Bot):
    await client.add_cog(Admin(client))