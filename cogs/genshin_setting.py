import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from typing import Optional
from utility.config import config
from utility.GenshinApp import genshin_app

class Setting(commands.Cog, name='設定'):
    def __init__(self, bot):
        self.bot = bot
    
    # 設定使用者Cookie
    @commands.command(
        brief=f'設置Cookie(必需)',
        description='設置Cookie，請依照底下步驟取得你個人的Cookie然後貼在這裡\n\n'
                    f'聲明：機器人需要保存你的Cookie供以後使用，Cookie的內容包含你個人的識別代碼（不包含帳號與密碼，也無法用來登入遊戲），是為了用來取得Hoyolab網站上你的原神資料。提供Cookie給別人是有風險的行為，若有疑慮請勿使用，想要隨時清除已保存的Cookie，請使用 {config.bot_prefix}clear 指令',
        usage='你取得的Cookie',
        help='```https://i.imgur.com/XuQisa7.jpg \n```'
            f'1.電腦瀏覽器打開Hoyolab登入帳號 https://www.hoyolab.com/\n'
            f'2.按F12打開開發者工具\n'
            f'3.切換至主控台(Console)頁面\n'
            f'4.複製底下整段程式碼，貼在主控台中按下Enter取得Cookie，然後將結果輸入在這裡(範例: {config.bot_prefix}cookie 你複製的Cookie)\n\n``````'
            "javascript:(()=>{_=(n)=>{for(i in(r=document.cookie.split(';'))){var a=r[i].split('=');if(a[0].trim()==n)return a[1]}};c=_('account_id')||alert('無效或過期的Cookie,請先登出後再重新登入!');c&&confirm('將Cookie複製到剪貼簿?')&&copy(document.cookie)})();"
    )
    async def cookie(self, ctx, *args):
        if ctx.me.guild_permissions.manage_messages:
            await ctx.message.delete()
        msg = await ctx.send('設置中...')
        user_id = ctx.author.id
        cookie = ' '.join(args)
        result = await genshin_app.setCookie(user_id, cookie)
        if ctx.me.guild_permissions.manage_messages:
            await msg.delete()
        await ctx.send(f'<@{user_id}> {result}')
    
    @app_commands.command(
        name='cookie設定', 
        description='設定Cookie，第一次使用前必須先使用本指令設定Cookie')
    @app_commands.describe(cookie='請輸入從網頁上取得的Cookie')
    async def slash_cookie(self, interaction: discord.Interaction, cookie: Optional[str] = None):
        if cookie is None:
            help_msg = "1.電腦開啟Hoyolab登入帳號 <https://www.hoyolab.com>\n2.按F12打開開發者工具，切換至主控台(Console)頁面\n3.複製底下程式碼，貼在主控台中按Enter取得Cookie\n4.在這輸入結果，範例：`/cookie設定 XXXXX(從網頁取得的Cookie)`\n```js\nd=document.cookie; c=d.includes('account_id') || alert('過期或無效的Cookie,請先登出帳號再重新登入!'); c && confirm('將Cookie複製到剪貼簿?') && copy(d)```https://i.imgur.com/dP4RKsb.png"
            await interaction.response.send_message(help_msg)
        else:
            result = await genshin_app.setCookie(str(interaction.user.id), cookie)
            if result.startswith('無效的Cookie'):
                await interaction.response.send_message('無效的Cookie，請重新輸入(使用 `/cookie` 查看教學)', ephemeral=True)
            else:
                await interaction.response.send_message(result, ephemeral=True)

    # 設定原神UID，當帳號內有多名角色時，保存指定的UID
    @commands.command(
        brief='指定要保存的UID(帳號內多角色才需用本指令)',
        description='指定自己帳號內要保存的UID，帳號只有一個角色的話設定Cookie時已自動保存，不需再使用本指令',
        usage='<UID>',
        help='在設定cookie之後，如果自己帳號內有多個角色時，需指定一個要保存使用的角色UID，使用範例：\n'
            f'{config.bot_prefix}uid 81234567'
    )
    async def uid(self, ctx, uid):
        result = genshin_app.setUID(str(ctx.author.id), uid)
        await ctx.reply(result)
    
    @app_commands.command(
        name='uid設定',
        description='帳號內多角色時需保存指定的UID，只有單一角色不需要使用本指令')
    @app_commands.describe(uid='請輸入原神角色的UID')
    async def slash_uid(self, interaction: discord.Interaction, uid: int):
        result = genshin_app.setUID(str(interaction.user.id), str(uid))
        await interaction.response.send_message(result)

    @commands.command(
        brief='刪除已保存的個人資料',
        description='使用本指令後，刪除該使用者所有保存在機器人內的個人資料',
        usage='yes',
        help=f'使用範例：\n{config.bot_prefix}clear yes'
    )
    async def clear(self, ctx, cmd):
        if cmd == 'yes':
            result = genshin_app.clearUserData(str(ctx.author.id))
            await ctx.reply(f'{result}')
    
    @app_commands.command(
        name='清除資料',
        description='刪除使用者所有保存在小幫手內的個人資料')
    @app_commands.rename(confirm='確認刪除')
    @app_commands.describe(confirm='確認刪除保存的資料？')
    @app_commands.choices(confirm=[Choice(name='確認', value=1), Choice(name='取消', value=0)])
    async def slash_clear(self, interaction: discord.Interaction, confirm: int):
        if confirm:
            result = genshin_app.clearUserData(str(interaction.user.id))
            await interaction.response.send_message(result)
        else:
            await interaction.response.send_message('取消指令')

async def setup(client: commands.Bot):
    await client.add_cog(Setting(client))