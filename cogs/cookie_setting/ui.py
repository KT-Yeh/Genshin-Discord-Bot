import typing
from http.cookies import SimpleCookie

import discord
import genshin

import genshin_py
from utility import LOG, EmbedTemplate, get_app_command_mention


class GameSelectionView(discord.ui.View):
    """選擇要提交哪些遊戲的 Cookie"""

    @discord.ui.select(
        cls=discord.ui.Select,
        options=[
            discord.SelectOption(label="原神", value="genshin"),
            discord.SelectOption(label="崩壞3", value="honkai3rd"),
            discord.SelectOption(label="星穹鐵道", value="hkrpg"),
        ],
        min_values=1,
        max_values=3,
        placeholder="請選擇遊戲 (可多選)：",
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        modal = CookieModal([genshin.Game(v) for v in select.values])
        await interaction.response.send_modal(modal)


class CookieModal(discord.ui.Modal, title="提交Cookie"):
    """提交 Cookie 的表單"""

    cookie: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Cookie",
        placeholder='請貼上從網頁上取得的Cookie，取得方式請使用指令 "/cookie設定 顯示說明如何取得Cookie"',
        style=discord.TextStyle.long,
        required=True,
        min_length=50,
        max_length=2000,
    )

    def __init__(self, games: list[genshin.Game]):
        self.games: list[genshin.Game] = games
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=EmbedTemplate.normal("設定中，請稍後..."), ephemeral=True
        )
        LOG.Info(f"設定 {LOG.User(interaction.user)} 的Cookie：{self.cookie.value}")
        try:
            cookie = await self._trim_cookies(self.cookie.value)
            if cookie is None:
                raise Exception(
                    f"錯誤或無效的Cookie，請重新輸入(使用 {get_app_command_mention('cookie設定')} 顯示說明)"
                )
            msg = await genshin_py.set_cookie(interaction.user.id, cookie, self.games)
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            await interaction.edit_original_response(embed=EmbedTemplate.normal(msg))

    async def _trim_cookies(self, cookie_string: str) -> str | None:
        """從使用者提交的 Cookie 內容中移除不必要的部分"""
        ALLOWED_COOKIES = (
            "cookie_token",
            "account_id",
            "ltoken",
            "ltuid",
            "cookie_token_v2",
            "account_id_v2",
            "ltoken_v2",
            "ltuid_v2",
            "ltmid_v2",
            "account_mid_v2",
        )
        origin: SimpleCookie[typing.Any] = SimpleCookie(cookie_string)
        cookie: SimpleCookie[typing.Any] = SimpleCookie(
            {k: v for (k, v) in origin.items() if k in ALLOWED_COOKIES}
        )
        # 當有 cookie_token 時，嘗試取得 ltoken 並延長 cookie_token 的過期時間，然後回傳完整 cookie 資料
        if "cookie_token" in cookie and "account_id" in cookie:
            try:
                r = await genshin.complete_cookies(cookie, refresh=True)
                cookie.update(SimpleCookie(r))
            except Exception:
                pass

        if len(cookie) == 0:
            return None
        return cookie.output(header="", sep=" ")
