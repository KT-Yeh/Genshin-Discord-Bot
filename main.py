import discord
import genshin
import sentry_sdk
from discord.ext import commands
from pathlib import Path
from utility.config import config
from utility.utils import log, sentry_logging
from data import database

intents = discord.Intents.default()
class GenshinDiscordBot(commands.AutoShardedBot):
    def __init__(self):
        self.db = database.db
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            application_id=config.application_id
        )

    async def is_owner(self, user: discord.User) -> bool:
        return (user.id == 969869284518015008) or (await super().is_owner(user))

    async def setup_hook(self) -> None:
        # 載入 jishaku
        await self.load_extension('jishaku')

        # 初始化資料庫
        await self.db.create(config.database_file_path)

        # 初始化 genshin api 角色名字
        await genshin.utility.update_characters_ambr(['zh-tw'])

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

    async def close(self) -> None:
        # 關閉資料庫
        await database.db.close()
        log.info('[資訊][System]on_close: 資料庫已關閉')
        await super().close()
        log.info('[資訊][System]on_close: 機器人已結束')

    async def on_command_error(self, ctx: commands.Context, error):
        log.info(f'[例外][{ctx.author.id}]on_command_error: {error}')

sentry_sdk.init(dsn=config.sentry_sdk_dsn, integrations=[sentry_logging], traces_sample_rate=1.0)

client = GenshinDiscordBot()
@client.tree.error
async def on_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    log.warning(f'[例外][{interaction.user.id}]{type(error)}: {error}')
    sentry_sdk.capture_exception(error)

client.run(config.bot_token)