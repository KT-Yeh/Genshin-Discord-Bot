import asyncio
import re

import discord
import genshin
from discord.ext import commands

from genshin_py import errors, genshin_app
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
        await interaction.response.send_message(embed=EmbedTemplate.error("沒有偵測到兌換碼，請重新輸入"))
        return
    await interaction.response.defer()

    codes = codes[:5] if len(codes) > 5 else codes  # 避免使用者輸入過多內容
    msg = ""
    invalid_cookie_msg = ""  # genshin api 的 InvalidCookies 原始訊息
    try:
        genshin_client = await genshin_app.get_genshin_client(user.id, game=game, check_uid=False)
    except Exception as e:
        await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        return

    for i, code in enumerate(codes):
        # 使用兌換碼的間隔為5秒
        if i > 0:
            await interaction.edit_original_response(
                embed=discord.Embed(color=0xFCC766, description=f"{msg}正在等待5秒冷卻時間使用第{i+1}組兌換碼...")
            )
            await asyncio.sleep(5)
        try:
            result = "✅" + await genshin_app.redeem_code(user.id, genshin_client, code, game)
        except errors.GenshinAPIException as e:
            result = "❌"
            if isinstance(e.origin, genshin.errors.InvalidCookies):
                result += "無效的Cookie"
                invalid_cookie_msg = str(e.origin)
            else:
                result += e.message
        except Exception as e:
            result = "❌" + str(e)
        # 訊息加上官網兌換連結
        game_host = {genshin.Game.GENSHIN: "genshin", genshin.Game.STARRAIL: "hsr"}
        msg += f"[{code}](https://{game_host.get(game)}.hoyoverse.com/gift?code={code})：{result}\n"

    embed = discord.Embed(color=0x8FCE00, description=msg)
    embed.set_footer(text="點擊上述兌換碼可代入兌換碼至官網兌換")
    if len(invalid_cookie_msg) > 0:
        embed.description += f"\n{invalid_cookie_msg}"  # type: ignore
    await interaction.edit_original_response(embed=embed)


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
