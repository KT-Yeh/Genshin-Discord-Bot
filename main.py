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
        # Load all cogs from cogs folder
        for filepath in Path('./cogs').glob('**/*.py'):
            cog_name = Path(filepath).stem
            await self.load_extension(f'cogs.{cog_name}')
        # Sync Slash commands to test server, global server use /sync command
        if config.test_server_id != None:
            test_guild = discord.Object(id=config.test_server_id)
            self.tree.copy_global_to(guild=test_guild)
            await self.tree.sync(guild=test_guild)

    async def on_ready(self):
        log.info(f'[News][System]on_ready: You have logged in as {self.user}')
        log.info(f'[News][System]on_ready: Total {len(self.guilds)} servers connected')

    async def on_command_error(self, ctx: commands.Context, error):
        log.error(f'[exception][{ctx.author.id}]on_command_error: {error}')

client = GenshinDiscordBot()
@client.tree.error
async def on_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    log.error(f'[exception][{interaction.user.id}]{type(error)}: {error}')

client.run(config.bot_token)
