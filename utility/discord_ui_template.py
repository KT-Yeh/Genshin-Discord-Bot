import discord
from typing import Union
from yuanshen.errors import GenshinAPIException


class EmbedTemplate:
    """Discord Embed 訊息的範本"""

    @staticmethod
    def normal(message: str, **kwargs) -> discord.Embed:
        """正常訊息的 Embed 範本"""
        return discord.Embed(color=0x7289DA, description=message, **kwargs)

    @staticmethod
    def error(exception: Union[GenshinAPIException, Exception, str], **kwargs) -> discord.Embed:
        """錯誤訊息的 Embed 範本"""
        embed = discord.Embed(color=0xB54031, **kwargs)

        if "title" not in kwargs:
            embed.title = "發生錯誤！"

        if isinstance(exception, GenshinAPIException):
            embed.description = f"{exception.message}\n```{exception.origin}```"
        else:  # Exception | str
            embed.description = str(exception)

        return embed
