import discord
from discord.ext import commands
from utility.config import config
from utility.GenshinApp import genshin_app

class Setting(commands.Cog, name='設定'):
    def __init__(self, bot):
        self.bot = bot
    
    # Set genshin cookie
    @commands.command(
        brief=f'設置Cookie(必需)',
        description='設置Cookie',
        usage='<你複製的Cookie>',
        help=f'1.瀏覽器打開Hoyolab登入帳號 https://www.hoyolab.com/\n'
            f'2.按F12打開開發者工具\n'
            f'3.將開發者工具切換至控制台(Console)頁面\n'
            f'4.複製底下程式碼，貼在控制台中按下Enter，然後將Cookie的結果貼在這裡(例: {config.bot_prefix}cookie 你複製的Cookie)\n\n'
            "javascript:(()=>{_=(n)=>{for(i in(r=document.cookie.split(';'))){var a=r[i].split('=');if(a[0].trim()==n)return a[1]}};c=_('account_id')||alert('無效或過期的Cookie,請先登出後再重新登入!');c&&confirm('將Cookie複製到剪貼簿?')&&copy(document.cookie)})();"
    )
    async def cookie(self, ctx, *args):
        await ctx.message.delete()
        msg = await ctx.send('設置中...')
        user_id = ctx.author.id
        cookie = ' '.join(args)
        result = await genshin_app.setCookie(user_id, cookie)
        await msg.delete()
        await ctx.send(result)

    # Set genshin uid
    @commands.command(
        brief='指定要保存的UID(平時不會用到)',
        description='指定自己帳號內要保存的UID',
        usage='<UID>',
        help='一般在設定cookie之後，當有自己帳號內有多個角色時，需指定一個要保存使用的角色UID'
    )
    async def uid(self, ctx, arg):
        user_id = ctx.author.id
        uid = arg
        if genshin_app.setUID(user_id, uid):
            await ctx.send(f'角色UID: {uid} 已設定完成')
        else:
            await ctx.send(f'角色UID: {uid} 設定失敗，請重新設定')

def setup(client):
    client.add_cog(Setting(client))