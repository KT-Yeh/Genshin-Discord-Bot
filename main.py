import discord
from discord.ext import commands
from pathlib import Path
from utility.config import config
from utility.utils import log

intents = discord.Intents.default()
class GenshinDiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='%$',
            intents=intents,
            application_id=config.application_id
        )

    async def setup_hook(self) -> None:
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
        log.error(f'[例外][{ctx.author.id}]on_command_error: {error}')

client = GenshinDiscordBot()
@client.tree.error
async def on_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    log.error(f'[例外][{interaction.user.id}]{type(error)}: {error}')

client.run(config.bot_token)