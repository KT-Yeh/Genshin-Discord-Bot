import discord
from discord.ext import commands
from pathlib import Path

from utility.CustomHelp import custom_help
from utility.config import config
from utility.utils import log

# 設定使用者呼叫指定的冷卻時間(秒數)
default_cooldown = commands.Cooldown(1, config.bot_cooldown)
intents = discord.Intents.default()
intents.message_content = True
class GenshinDiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.bot_prefix,
            intents=intents,
            help_command=custom_help,
            description=f'Hello，原神小幫手的指令前綴為"{config.bot_prefix}"\n'
                        f'第一次使用原神指令前必需先設置Cookie(請參閱 {config.bot_prefix}help cookie)\n'
                        f'小幫手全部指令如下：'
        )

    async def setup_hook(self) -> None:
        # 從cogs資料夾載入所有cog
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            await self.load_extension(f'cogs.{cog_name}')

    async def on_ready(self):
        log.info(f'You have logged in as {client}')
        log.info(f'Total {len(self.guilds)} servers connected')
        for command in self.commands:
            command._buckets._cooldown = default_cooldown
        await self.change_presence(activity=discord.Game(name='Genshin Impact'))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'指令缺少必要參數，請使用 `{config.bot_prefix}help {ctx.command}` 查看使用方式')

client = GenshinDiscordBot()
client.run(config.bot_token)