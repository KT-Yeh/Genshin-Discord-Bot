import re

import discord
import genshin
from discord.ext import commands

from utility import EmbedTemplate, custom_log


async def redeem(
    interaction: discord.Interaction,
    user: discord.User | discord.Member,
    code: str,
    game: genshin.Game,
):
    # 若兌換碼包含兌換網址，則移除該網址
    code = re.sub(r"(https://){0,1}genshin.hoyoverse.com(/.*){0,1}/gift\?code=", "", code)
    code = re.sub(r"(https://){0,1}hsr.hoyoverse.com(/.*){0,1}/gift\?code=", "", code)
    # 匹配多組兌換碼並存成list
    codes = re.findall(r"[A-Za-z0-9]{5,30}", code)
    if len(codes) == 0:
        await interaction.response.send_message(
            embed=EmbedTemplate.error("沒有偵測到兌換碼，請重新輸入")
        )
        return

    codes = codes[:5] if len(codes) > 5 else codes  # 避免使用者輸入過多內容
    msg = "請點下列連結兌換：\n"
    for i, code in enumerate(codes):
        game_host = {genshin.Game.GENSHIN: "genshin", genshin.Game.STARRAIL: "hsr"}
        msg += f"> {i+1}. [{code}](https://{game_host.get(game)}.hoyoverse.com/gift?code={code})\n"

    embed = discord.Embed(color=0x8FCE00, description=msg)
    await interaction.response.send_message(embed=embed)


class RedemptionCodeCog(commands.Cog, name="兌換碼"):
    """斜線指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(client: commands.Bot):
    await client.add_cog(RedemptionCodeCog(client))

    @client.tree.context_menu(name="使用兌換碼(原神)")
    @custom_log.ContextCommandLogger
    async def context_redeem_genshin(interaction: discord.Interaction, msg: discord.Message):
        await redeem(interaction, interaction.user, msg.content, genshin.Game.GENSHIN)

    @client.tree.context_menu(name="使用兌換碼(鐵道)")
    @custom_log.ContextCommandLogger
    async def context_redeem_starrail(interaction: discord.Interaction, msg: discord.Message):
        await redeem(interaction, interaction.user, msg.content, genshin.Game.STARRAIL)
