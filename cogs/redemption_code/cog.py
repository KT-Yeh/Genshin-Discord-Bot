import re
import asyncio
import discord
import genshin
from discord.ext import commands
import genshin_py.client as genshin_py
import genshin_py.errors
from utility import EmbedTemplate, custom_log
from typing import Literal, Optional
from discord import app_commands
from discord.app_commands import Choice


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
    await interaction.response.defer()

    codes = codes[:5] if len(codes) > 5 else codes  # 避免使用者輸入過多內容
    msg = ""
    invalid_cookie_msg = ""  # genshin api 的 InvalidCookies 原始訊息
    try:
        genshin_client = await genshin_py.get_client(user.id, game=game, check_uid=False)
    except Exception as e:
        await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        return

    for i, code in enumerate(codes):
        # 使用兌換碼的間隔為5秒
        if i > 0:
            await interaction.edit_original_response(
                embed=discord.Embed(color=0xFCC766, description=f"{msg} 等待5秒冷卻時間才能使用兌換碼 {i+1}.....")
            )
            await asyncio.sleep(5)
        try:
            genshin_client = await genshin_py.get_client(user.id, game=game, check_uid=False)
            result = "✅ " + await genshin_py.redeem_code(user.id, genshin_client, code, game)
        except genshin_py.errors.GenshinAPIException as e:
            result = "❌ "
            if isinstance(e.origin, genshin.errors.InvalidCookies):
                result += "無效的Cookie"
                invalid_cookie_msg = str(e.origin)
            else:
                result += e.message
        except Exception as e:
            result = "❌ " + str(e)
        msg += f"{code} : {result}\n"
        embed = discord.Embed(color=0x8FCE00, description=msg)
        if len(invalid_cookie_msg) > 0:
            embed.description += f"\n{invalid_cookie_msg}"
        await interaction.edit_original_response(embed=embed)


class RedemptionCodeCog(commands.Cog, name="兌換碼"):
    """斜線指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="redeem兌換", description="使用Hoyolab兌換碼")
    @app_commands.rename(code="兌換碼", game="遊戲", user="使用者")
    @app_commands.describe(code="請輸入要使用的兌換碼，支援多組兌換碼同時輸入") # noqa
    @app_commands.choices(
        game=[
            Choice(name="原神", value="GENSHIN"),
            Choice(name="星穹鐵道", value="STARRAIL"),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_redeem(
        self,
        interaction: discord.Interaction,
        code: str,
        game: Literal["GENSHIN", "STARRAIL"],
        user: Optional[discord.User] = None,
    ):
        game_map = {"GENSHIN": genshin.Game.GENSHIN, "STARRAIL": genshin.Game.STARRAIL}
        await redeem(interaction, user or interaction.user, code, game_map[game])


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
