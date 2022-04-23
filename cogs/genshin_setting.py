import discord
from discord.ext import commands
from utility.GenshinApp import genshin_app
import os
from dotenv import load_dotenv
load_dotenv()

class Setting(commands.Cog, name='設定'):
    def __init__(self, bot):
        self.bot = bot
    
    # 設定使用者Cookie
    @commands.command(
        brief=f'設置Cookie(必需)',
        description='設置Cookie，請依照底下步驟取得你個人的Cookie然後貼在這裡\n\n'
                    f'註：機器人需要保存你的Cookie供以後使用，Cookie的內容包含你個人的識別代碼（不包含帳號與密碼，也無法用來登入遊戲），是為了用來取得Hoyolab網站上你的原神資料。提供Cookie給別人是有風險的行為，若有疑慮請勿使用，想要隨時清除已保存的Cookie，請使用 {os.getenv("BOT_PREFIX")}clear 指令',
        usage='你取得的Cookie',
        help='```https://i.imgur.com/XuQisa7.jpg \n'
            f'1.電腦打開Hoyolab登入帳號 <https://www.hoyolab.com>\n'
            f'2.按F12打開開發者工具，切換至主控台(Console)頁面\n'
            f'3.複製底下程式碼，貼在主控台中按Enter取得Cookie\n'
            f'4.在這輸入結果，範例：`{os.getenv("BOT_PREFIX")}cookie XXXXX(從網頁取得的Cookie)\n'
            "```js\nd=document.cookie; c=d.includes('account_id') || alert('過期或無效的Cookie,請先登出帳號再重新登入!'); c && confirm('將Cookie複製到剪貼簿?') && copy(d)"
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

    # 設定原神UID，當帳號內有多名角色時，保存指定的UID
    @commands.command(
        brief='指定要保存的UID(帳號內多角色才需用本指令)',
        description='指定自己帳號內要保存的UID，帳號只有一個角色的話設定Cookie時已自動保存，不需再使用本指令',
        usage='<UID>',
        help='在設定cookie之後，如果自己帳號內有多個角色時，需指定一個要保存使用的角色UID，使用範例：\n'
            f'{os.getenv("BOT_PREFIX")}uid 81234567'
    )
    async def uid(self, ctx, uid):
        result = genshin_app.setUID(str(ctx.author.id), uid)
        await ctx.reply(result)

    @commands.command(
        brief='刪除已保存的個人資料',
        description='使用本指令後，刪除該使用者所有保存在機器人內的個人資料',
        usage='yes',
        help=f'使用範例：\n{os.getenv("BOT_PREFIX")}clear yes'
    )
    async def clear(self, ctx, cmd):
        if cmd == 'yes':
            result = genshin_app.clearUserData(str(ctx.author.id))
            await ctx.reply(f'{result}')

def setup(client):
    client.add_cog(Setting(client))