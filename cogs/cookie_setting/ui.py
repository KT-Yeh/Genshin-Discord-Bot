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
            discord.SelectOption(label="未定事件簿", value="tot"),
        ],
        min_values=1,
        max_values=4,
        placeholder="請選擇遊戲 (可多選)：",
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        modal = CookieModal([genshin.Game(v) for v in select.values])
        await interaction.response.send_modal(modal)


class CookieModal(discord.ui.Modal, title="提交Cookie"):
    """提交 Cookie 的表單"""

    ltuid_v2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="ltuid_v2",
        placeholder="請貼上取得的 ltuid_v2",
        style=discord.TextStyle.short,
        required=False,
        min_length=5,
        max_length=20,
    )

    ltoken_v2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="ltoken_v2",
        placeholder="請貼上取得的 ltoken_v2",
        style=discord.TextStyle.short,
        required=False,
        min_length=30,
        max_length=150,
    )

    ltmid_v2: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="ltmid_v2",
        placeholder="請貼上取得的 ltmid_v2",
        style=discord.TextStyle.short,
        required=False,
        min_length=5,
        max_length=20,
    )

    cookie: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Cookie",
        placeholder="非特殊需求本欄請保持空白，此處用來貼完整的 Cookie 字串",
        style=discord.TextStyle.long,
        required=False,
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

        # 將 ltuid_v2 和 ltoken_v2 附加到 cookie 中
        v2_str = ""
        cookie = self.cookie.value
        if len(self.ltoken_v2.value) > 0:
            # 檢測 cookie 是否為 v2 版本
            if self.ltoken_v2.value.startswith("v2"):
                v2_str = "_v2"
            cookie += f" ltoken{v2_str}={self.ltoken_v2.value};"
        if len(self.ltuid_v2.value) > 0:
            if self.ltuid_v2.value.isdigit() is True:
                cookie += f" ltuid{v2_str}={self.ltuid_v2.value};"
                cookie += f" account_id{v2_str}={self.ltuid_v2.value};"
            else:  # ltuid_v2 不是數字，可能是 ltmid_v2
                cookie += f" ltmid_v2={self.ltuid_v2.value};"
                cookie += f" account_mid_v2={self.ltuid_v2.value};"
        if len(self.ltmid_v2.value) > 0:
            cookie += f" ltmid_v2={self.ltmid_v2.value};"
            cookie += f" account_mid_v2={self.ltmid_v2.value};"

        LOG.Info(f"設定 {LOG.User(interaction.user)} 的Cookie：{self.cookie.value}")
        try:
            trimmed_cookie = await self._trim_cookies(cookie)
            if trimmed_cookie is None:
                raise Exception(
                    f"錯誤或無效的Cookie，請重新輸入(使用 {get_app_command_mention('cookie設定')} 顯示說明)"
                )
            msg = await genshin_py.set_cookie(interaction.user.id, trimmed_cookie, self.games)
        except Exception as e:
            embed = EmbedTemplate.error(e)
            if embed.description is not None:
                embed.description += (
                    "點 [>>教學連結<<](https://hackmd.io/66fq-6NsT1Kqxqbpkj1xTA) 查看解決方法\n"
                )
            await interaction.edit_original_response(embed=embed)
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
