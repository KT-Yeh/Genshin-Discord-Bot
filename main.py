from pathlib import Path

import discord
import genshin
import prometheus_client
import sentry_sdk
from discord.ext import commands

from database import Database
from utility import LOG, config, sentry_logging

intents = discord.Intents.default()


class GenshinDiscordBot(commands.AutoShardedBot):
    def __init__(self):
        self.db = Database
        super().__init__(
            command_prefix=commands.when_mentioned_or("$"),
            intents=intents,
            application_id=config.application_id,
        )

    async def setup_hook(self) -> None:
        # 載入 jishaku
        await self.load_extension("jishaku")

        # 初始化資料庫
        await Database.init()

        # 初始化 genshin api 角色名字
        await genshin.utility.update_characters_ambr(["zh-tw"])

        # 從cogs資料夾載入所有cog
        for filepath in Path("./cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            await self.load_extension(f"cogs.{cog_name}")
        for filepath in Path("./cogs_external").glob("**/*.py"):
            cog_name = Path(filepath).stem
            await self.load_extension(f"cogs_external.{cog_name}")

        # 同步Slash commands到測試伺服器，全域伺服器用 /sync 指令
        if config.test_server_id is not None:
            test_guild = discord.Object(id=config.test_server_id)
            self.tree.copy_global_to(guild=test_guild)
            await self.tree.sync(guild=test_guild)

        # 啟動 Prometheus Server
        if config.prometheus_server_port is not None:
            prometheus_client.start_http_server(config.prometheus_server_port)
            LOG.System(f"prometheus server: started on port {config.prometheus_server_port}")

    async def on_ready(self):
        LOG.System(f"on_ready: You have logged in as {self.user}")
        LOG.System(f"on_ready: Total {len(self.guilds)} servers connected")

    async def close(self) -> None:
        # 關閉資料庫
        await Database.close()
        LOG.System("on_close: 資料庫已關閉")
        await super().close()
        LOG.System("on_close: 機器人已結束")

    async def on_command(self, ctx: commands.Context):
        LOG.CmdResult(ctx)

    async def on_command_error(self, ctx: commands.Context, error):
        LOG.ErrorLog(ctx, error)


sentry_sdk.init(dsn=config.sentry_sdk_dsn, integrations=[sentry_logging], traces_sample_rate=1.0)

client = GenshinDiscordBot()


@client.tree.error
async def on_error(
    interaction: discord.Interaction, error: discord.app_commands.AppCommandError
) -> None:
    LOG.ErrorLog(interaction, error)
    sentry_sdk.capture_exception(error)


client.run(config.bot_token)
