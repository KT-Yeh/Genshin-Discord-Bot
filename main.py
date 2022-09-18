import discord
import sentry_sdk
from discord.ext import commands
from pathlib import Path
from utility.config import config
from utility.utils import log, sentry_logging

intents = discord.Intents.default()
class GenshinDiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            application_id=config.application_id
        )

    async def setup_hook(self) -> None:
        # 載入 jishaku
        await self.load_extension('jishaku')
        
        # 從cogs資料夾載入所有cog
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            await self.load_extension(f'cogs.{cog_name}')
        
        # 同步Slash commands到測試伺服器，全域伺服器用 /sync 指令
        if config.test_server_id != None:
            test_guild = discord.Object(id=config.test_server_id)
            self.tree.copy_global_to(guild=test_guild)
            await self.tree.sync(guild=test_guild)

    async def on_ready(self):
        log.info(f'[資訊][System]on_ready: You have logged in as {self.user}')
        log.info(f'[資訊][System]on_ready: Total {len(self.guilds)} servers connected')

    async def on_command_error(self, ctx: commands.Context, error):
        log.info(f'[例外][{ctx.author.id}]on_command_error: {error}')

sentry_sdk.init(dsn=config.sentry_sdk_dsn, integrations=[sentry_logging], traces_sample_rate=1.0)

client = GenshinDiscordBot()
@client.tree.error
async def on_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    log.warning(f'[例外][{interaction.user.id}]{type(error)}: {error}')
    if not isinstance(error, discord.errors.NotFound): # 忽略 Not Found 例外
        sentry_sdk.capture_exception(error)

client.run(config.bot_token)