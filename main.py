import discord
from discord.ext import commands
from pathlib import Path

from utility.CustomHelp import custom_help
from utility.config import config
from utility.utils import *

default_cooldown = commands.Cooldown(1, config.bot_cooldown, commands.BucketType.user)
client = commands.Bot(
    command_prefix=config.bot_prefix, 
    help_command=custom_help,
    description=f'Hello，原神小幫手的指令前綴為"{config.bot_prefix}"\n'
                f'第一次使用原神指令前必需先設置Cookie，可使用指令如下：'
)

@client.event
async def on_ready():
    log.info(f'You have logged in as {client}')
    for command in client.commands:
        command._buckets._cooldown = default_cooldown
    await client.change_presence(activity=discord.Game(name='Genshin Impact'))

# Load cogs
for filepath in Path('./cogs').glob('**/*.py'):
    cog_name = Path(filepath).stem
    client.load_extension(f'cogs.{cog_name}')

client.run(config.bot_token)
