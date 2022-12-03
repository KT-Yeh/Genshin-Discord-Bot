from __future__ import annotations
from functools import wraps
import discord
import os
import platform
import logging
import re
import time
import traceback
import genshin
from datetime import datetime as dt
from discord.ext import commands
from typing import Any, Callable, List
from importlib.metadata import version

#   六位色碼的正則表達式
COLOR_CODE = re.compile(r"^[#]?[a-f0-9]{6}$")

#   檢查執行的作業系統環境
if platform.system() == "Windows":
    #   讓Windows的cmd.exe看的懂ANSI轉意序列，不執行的話就會把ANSI全印出來，有夠靠杯...
    os.system("")
elif platform.system() == "Linux":
    pass
elif platform.system() == "Java":
    pass
else:
    pass

#   設定 logging
logging.basicConfig(format="%(message)s", level=logging.INFO)

#   Log更改顏色用
class ColorTool:
    """顏色小工具"""

    def __init__(self, custom_colors: List[List[int | str | bool]] = []) -> None:
        """顏色小工具

        Args:
            custom_colors (`List`[`List`[`int`  |  `str`  |  `bool`]], optional): 自定義色碼或RGB。 預設為空。(WIP)
        """
        for custom_color in custom_colors:
            if len(custom_color) != 0:
                color = ""
                if isinstance(custom_color[0], int):
                    font = custom_color[3] if len(custom_color) > 3 else True
                    color = self.RGB(custom_color[0], custom_color[1], custom_color[2], font)
                else:
                    font = custom_color[1] if len(custom_color) > 1 else True
                    color = self.CODE(custom_color[0], font)
                if color != "":
                    self._CUSTOM.append(color)

    #
    #   標準4bit顏色:暗
    _STD_BLACK = "\033[30m"  # 000000
    _STD_RED = "\033[31m"  # 800000
    _STD_GREEN = "\033[32m"  # 008000
    _STD_YELLOW = "\033[33m"  # 808000
    _STD_BLUE = "\033[34m"  # 000080
    _STD_MAGENTA = "\033[35m"  # 800080
    _STD_CYAN = "\033[36m"  # 008080
    _STD_LIGHT_GRAY = "\033[37m"  # C0C0C0
    #   標準4bit顏色:亮
    _STD_DARK_GRAY = "\033[90m"  # 808080
    _STD_LIGHT_RED = "\033[91m"  # FF0000
    _STD_LIGHT_GREEN = "\033[92m"  # 00FF00
    _STD_LIGHT_YELLOW = "\033[93m"  # FFFF00
    _STD_LIGHT_BLUE = "\033[94m"  # 0000FF
    _STD_LIGHT_MAGENTA = "\033[95m"  # FF00FF
    _STD_LIGHT_CYAN = "\033[96m"  # 00FFFF
    _STD_WHITE = "\033[97m"  # FFFFFF
    #
    #   新板:暗(設定來自:https://devblogs.microsoft.com/commandline/updating-the-windows-console-colors/)
    _BLACK = "\033[38;2;12;12;12m"  # 0C0C0C
    _RED = "\033[38;2;197;15;31m"  # C50FFF
    _GREEN = "\033[38;2;19;161;14m"  # 13A10E
    _YELLOW = "\033[38;2;193;156;0m"  # C19C00
    _BLUE = "\033[38;2;0;52;218m"  # 0034DA
    _MAGENTA = "\033[38;2;136;23;152m"  # 881798
    _CYAN = "\033[38;2;58;150;221m"  # 3A96DD
    _LIGHT_GRAY = "\033[38;2;204;204;204m"  # CCCCCC
    #   新板:亮
    _DARK_GRAY = "\033[38;2;118;118;118m"  # 767676
    _LIGHT_RED = "\033[38;2;231;72;86m"  # E74856
    _LIGHT_GREEN = "\033[38;2;22;198;12m"  # 16C00C
    _LIGHT_YELLOW = "\033[38;2;249;241;165m"  # F9F1A5
    _LIGHT_BLUE = "\033[38;2;59;120;255m"  # 3B78FF
    _LIGHT_MAGENTA = "\033[38;2;180;0;158m"  # B4009E
    _LIGHT_CYAN = "\033[38;2;97;214;214m"  # 61D6D6
    _WHITE = "\033[38;2;242;242;242m"  # E2E2E2
    #
    #   灰階:1~7由黑至白(我也不知道這拿來幹嘛，但總覺得該設)
    _GRAY_SCALE_1 = "\033[38;2;32;32;32m"  # 202020 極深灰
    _GRAY_SCALE_2 = "\033[38;2;64;64;64m"  # 404040 深灰
    _GRAY_SCALE_3 = "\033[38;2;96;96;96m"  # 606060 淺深灰
    _GRAY_SCALE_4 = "\033[38;2;128;128;128m"  # 808080 灰
    _GRAY_SCALE_5 = "\033[38;2;160;160;160m"  # A0A0A0 深淺灰
    _GRAY_SCALE_6 = "\033[38;2;192;192;192m"  # C0C0C0 淺灰
    _GRAY_SCALE_7 = "\033[38;2;224;224;224m"  # E0E0E0 極淺灰
    #
    #   自定義專區，拿來自定義喜歡的顏色，注意文本與背景顏色的第一個代號不同
    #   格式如下：
    #   ├ font，即前端文本顏色，第一個代號為38，完整格式:'\033[38;2;{R};{G};{B}m'
    #   └ back，即背景顏色，第一個代號為48，完整格式:'\033[48;2;{R};{G};{B}m'
    _MIKU_GREEN = "\033[38;2;57;197;187m"  # 39C5BB  軟體綠
    _TIAN_YI_BLUE = "\033[38;2;102;204;255m"  # 66CCFF   天依藍
    _DISCORD_DARK = "\033[48;2;54;57;63m"  # 36393F  * Discord暗色背景(改背景)
    _ORANGE = "\033[38;2;255;102;0m"  # FF6600   橘色
    _LIME = "\033[38;2;170;255;85m"  # AAFF55   萊姆綠
    _GOLD = "\033[38;2;255;221;51m"  # FFDD33   金色
    _PINK = "\033[38;2;255;128;255m"  # BB80FF   粉紅色
    _ORANGE_RED = "\033[38;2;255;102;102m"  # FF6666   橘紅色
    _WHEAT_YELLOW = "\033[38;2;238;255;85m"  # EEFF55   小麥色
    _GRASS_GREEN = "\033[38;2;102;255;102m"  # 66FF66   草綠色
    _BRIGHT_ORANGE = "\033[38;2;255;187;102m"  # FFBB66   亮橘色
    _BRIGHT_CYAN_GREEN = "\033[38;2;136;255;255m"  # 88FFFF   亮藍綠色
    _BRIGHT_BLUE = "\033[38;2;51;204;255m"  # 33CCFF   亮藍色
    _BRIGHT_MAGENTA = "\033[38;2;221;51;221m"  # DD33DD   亮桃紅色
    _BRIGHT_PURPLE = "\033[38;2;187;187;255m"  # BBBBFF   淡紫色
    _BRIGHT_GREEN = "\033[38;2;187;255;187m"  # BBFFBB   淡綠色
    _BRIGHT_RED = "\033[38;2;255;187;187m"  # FFBBBB   淡紅色
    _BRIGHT_CYAN = "\033[38;2;187;255;255m"  # BBFFFF   淡青色
    _BRIGHT_PINK = "\033[38;2;255;187;255m"  # FFBBFF   淡粉紅色
    _BRIGHT_YELLOW = "\033[38;2;255;255;187m"  # FFBB   淡黃色
    #
    #   特殊編碼
    RESET = f"\033[0m{_WHITE}"  # 重置:恢復預設(這邊我加了白色是希望預設為白色)
    """重置顏色"""
    _REVERSE = "\033[30;47m"  # 反白(沒在用= =)
    """反白"""
    _BOLD = "\033[1m"  # 粗體(不是想像中的粗體，算是把顏色轉高亮，只對基本暗色編碼有用)
    """粗體/高亮"""
    _CUSTOM: List[str] = []  # 存自定義顏色的
    """自定義顏色列表"""
    #
    #   設定標籤顏色(自己改喜歡的顏色)
    SYSTEM = f"{_BRIGHT_PURPLE}【系統】{RESET}"  # 系統:淡紫色
    ERROR = f"{_RED}【錯誤】{RESET}"  # 錯誤:紅色
    OK = f"{_LIGHT_GREEN}【完成】{RESET}"  # 完成:亮綠色
    EVENT = f"{_LIGHT_YELLOW}【事件】{RESET}"  # 事件:亮黃色
    COMMAND = f"{_BRIGHT_BLUE}【指令】{RESET}"  # 指令:亮藍色
    EXCEPTION = f"{_BRIGHT_MAGENTA}【例外】{RESET}"  # 例外:亮桃紅
    INFO = f"{_BRIGHT_CYAN_GREEN}【資訊】{RESET}"  # 資訊:亮青色
    DEBUG = f"{_LIGHT_RED}【除錯】{RESET}"  # 除錯:亮紅色
    TEST = f"{_GOLD}【測試】{RESET}"  # 測試:金色
    WARN = f"{_ORANGE}【警告】{RESET}"  # 警告:橘色
    INTERACTION = f"{_LIME}【互動】{RESET}"  # 互動:萊姆綠

    def RGB(self, Red: int = 255, Green: int = 255, Blue: int = 255, font: bool = True) -> str:
        """使用RGB獲得ANSI轉義序列

        Args:
            Red (`int`): 紅色的數值。範圍為`0` ~ `255`。預設為`255`
            Green (`int`): 綠色的數值。範圍為`0` ~ `255`。預設為`255`
            Blue (`int`): 藍色的數值。範圍為`0` ~ `255`。預設為`255`
            font (`bool`, optional): 改文字顏色則傳入`True`，改背景顏色傳入`False`，預設為 `True`

        Returns:
            str: ANSI轉義序列
        """
        if (
            (isinstance(Red, int) and Red >= 0 and Red <= 255)
            and (isinstance(Green, int) and Green >= 0 and Green <= 255)
            and (isinstance(Blue, int) and Blue >= 0 and Blue <= 255)
        ):
            return f"\033[{38 if font else 48};2;{Red};{Green};{Blue}m"
        else:
            return ""

    def CODE(self, Color_Code: str = "#ffffff", font: bool = True) -> str:
        """使用6位色碼獲得ANSI轉義序列

        Args:
            Color_Code (`str`, optional): 6位色碼，可接受開頭帶`#`，預設為 `#ffffff`
            font (`bool`, optional): 改文字顏色則傳入`True`，改背景顏色傳入`False`，預設為 `True`

        Returns:
            str: ANSI轉義序列
        """
        code = Color_Code.lstrip("#").lower()
        if COLOR_CODE.fullmatch(code) is not None:
            Red = int(code[0:2], 16)
            Green = int(code[2:4], 16)
            Blue = int(code[4:6], 16)
            return f"\033[{38 if font else 48};2;{Red};{Green};{Blue}m"
        else:
            return ""


class LogTool(ColorTool):
    """自定義Log工具

    範例:
        self.System("虛空系統已啟動。") =>

        [2022-10-24 15:23:39]【系統】虛空系統已啟動。

    區塊上色範例:
        self.System(f"{self._PINK}虛空系統{self.RESET}已啟動。") =>

        [2022-10-24 15:23:39]【系統】`虛空系統`已啟動。(強調處為粉色文字)
    """

    #   版本
    VERSION = "3.1"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.indent = "\n                　　　　"
        self.indent_noTag = "\n                "
        #   下面這段就是拿來看效果的，顏色記得自己調
        print(
            f"\n              {self._MIKU_GREEN}原神小幫手{self.RESET}              System : {self._LIGHT_CYAN}{platform.system()}\n"
            f" {self._LIGHT_RED}Python {self._GRAY_SCALE_6}v{platform.python_version()}"
            f"   {self._BRIGHT_BLUE}discord.py {self._GRAY_SCALE_6}v{version('discord.py')}"
            f"   {self._WHEAT_YELLOW}genshin.py {self._GRAY_SCALE_6}v{version('genshin')}"
            f"   {self._PINK}LogTool {self._GRAY_SCALE_6}v{self.VERSION}{self.RESET}\n"
        )
        #   f" {self._STD_WHITE}-------------------- 顏色範例 --------------------{self.RESET}\n"
        #   f"  {self._BRIGHT_PINK}自定義訊息{self.RESET}:{self._BRIGHT_PINK}範例文字{self.RESET}\n"
        #   f"  {self._ORANGE_RED}範例指令集{self.RESET}({self._BRIGHT_RED}Example{self.RESET})\n"
        #   f"  {self._LIGHT_MAGENTA}例外類型{self.RESET}({self._LIGHT_MAGENTA}Error.ExampleException{self.RESET})\n"
        #   f"  {self._RED}錯誤訊息{self.RESET}:{self._RED}Error Message...{self.RESET}\n"
        #   f"  {self._GRASS_GREEN}伺服器{self.RESET}({self._BRIGHT_GREEN}Guild_ID{self.RESET})\n"
        #   f"  {self._TIAN_YI_BLUE}#頻道{self.RESET}({self._BRIGHT_CYAN}Channel ID{self.RESET})\n"
        #   f"  {self._BRIGHT_ORANGE}@使用者{self.RESET}({self._BRIGHT_YELLOW}User ID{self.RESET})\n"
        #   f" {self._STD_WHITE}-------------------- 標籤範例 --------------------{self.RESET}\n"
        #   f"  {self.SYSTEM}{self.OK}{self.EVENT}{self.COMMAND}{self.INTERACTION}{self.TEST}\n"
        #   f"  {self.DEBUG}{self.INFO}{self.WARN}{self.EXCEPTION}{self.ERROR}\n")

    def __get_timestamp__(self, display: bool = True) -> str:
        """取得Log時間戳記"""
        time_stamp = dt.now().strftime("%m-%d %H:%M:%S")
        if display:
            return f"{self._STD_DARK_GRAY}[{time_stamp}]{self.RESET}"
        else:
            return f"{self._STD_BLACK}[{time_stamp}]{self.RESET}"

    def __print_with_tag__(
        self,
        tag: str | None,
        logging_level: int = logging.INFO,
        message: str = "",
        show_timestamp: bool = True,
    ) -> None:
        message = message[:-1] if (len(message) > 0 and message[-1] == "\n") else message
        msg = str(message).replace("\n", (self.indent if tag != None else self.indent_noTag))
        msg = f'{self.__get_timestamp__(show_timestamp)}{(tag if tag != None else " ")}{msg}'
        for level, func in zip(
            [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL],
            [logging.debug, logging.info, logging.warning, logging.error, logging.critical],
        ):
            if logging_level == level:
                func(msg)
                break

    def System(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【系統】"""
        self.__print_with_tag__(self.SYSTEM, logging.INFO, message, show_timestamp)

    def Ok(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【完成】"""
        self.__print_with_tag__(self.OK, logging.INFO, message, show_timestamp)

    def Event(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【事件】"""
        self.__print_with_tag__(self.EVENT, logging.INFO, message, show_timestamp)

    def Cmd(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【指令】"""
        self.__print_with_tag__(self.COMMAND, logging.INFO, message, show_timestamp)

    def Interact(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【互動】"""
        self.__print_with_tag__(self.INTERACTION, logging.INFO, message, show_timestamp)

    def Debug(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【除錯】"""
        self.__print_with_tag__(self.DEBUG, logging.DEBUG, message, show_timestamp)

    def Info(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【資訊】"""
        self.__print_with_tag__(self.INFO, logging.INFO, message, show_timestamp)

    def Warn(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【警告】"""
        self.__print_with_tag__(self.WARN, logging.WARN, message, show_timestamp)

    def Error(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【錯誤】"""
        self.__print_with_tag__(self.ERROR, logging.WARN, message, show_timestamp)

    def Except(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【例外】"""
        self.__print_with_tag__(self.EXCEPTION, logging.INFO, message, show_timestamp)

    def Test(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss]【測試】"""
        self.__print_with_tag__(self.DEBUG, logging.DEBUG, message, show_timestamp)

    def NoTag(self, message: str = "", show_timestamp: bool = True) -> None:
        """[YYYY-MM-DD hh:mm:ss] (message...)"""
        self.__print_with_tag__(None, logging.INFO, message, show_timestamp)

    def User(self, user: discord.User | discord.Member | str | int):
        if isinstance(user, (str, int)):
            return f"{self._BRIGHT_YELLOW}@{user}{self.RESET}"
        display_name = (
            user.display_name if len(user.display_name) <= 15 else f"{user.display_name[:13]}..."
        )
        return f"{self._BRIGHT_ORANGE}@{display_name}#{user.discriminator}{self.RESET}({self._BRIGHT_YELLOW}{user.id}{self.RESET})"

    def Server(self, server: discord.Guild | None):
        if server:
            server_name = server.name if len(server.name) <= 15 else f"{server.name[:13]}..."
            return f"{self._GRASS_GREEN}{server_name}{self.RESET}({self._BRIGHT_GREEN}{server.id}{self.RESET})"
        return ""

    def Channel(
        self,
        channel: discord.TextChannel | discord.ForumChannel | discord.Thread | discord.DMChannel,
    ) -> str:
        if isinstance(channel, discord.TextChannel):
            return f"{self._MIKU_GREEN}#{channel.name}{self.RESET}({self._BRIGHT_CYAN}{channel.id}{self.RESET})"
        if isinstance(channel, discord.ForumChannel):
            return f"{self._MIKU_GREEN}#{channel.name}{self.RESET}({self._BRIGHT_CYAN}{channel.id}{self.RESET})"
        elif isinstance(channel, discord.Thread):
            return f"{self._MIKU_GREEN}#{channel.parent.name}({self._BRIGHT_CYAN}{channel.parent.id}{self.RESET}) => 討論串：{channel.name}{self.RESET}({self._BRIGHT_CYAN}{channel.id}{self.RESET})"
        else:
            return (
                f"{self._MIKU_GREEN}#私訊頻道{self.RESET}({self._BRIGHT_CYAN}{channel.id}{self.RESET})"
            )

    def CostTime(self, start_time: float) -> str:
        end_time = time.perf_counter()
        return f" {self._PINK}{(end_time-start_time)*1000:.0f}{self.RESET} 毫秒(ms)"

    def Cog(self, id: str, name: str = "", enabled: bool = True):
        if enabled:
            return (
                f"{self._ORANGE_RED}{name}{self.RESET}({self._BRIGHT_RED}{id}{self.RESET})"
                if name != ""
                else f"{self._ORANGE_RED}{id}{self.RESET}"
            )
        else:
            return (
                f"{self._GRAY_SCALE_4}{name}{self.RESET}({self._GRAY_SCALE_4}{id}{self.RESET})"
                if name != ""
                else f"{self._GRAY_SCALE_4}{id}{self.RESET}"
            )

    def ErrorType(self, error: discord.DiscordException | Exception) -> str:
        if isinstance(error, commands.CommandInvokeError):
            return f"({self._LIGHT_MAGENTA}{type(error).__qualname__}{self.RESET} -> {self._LIGHT_MAGENTA}{type(error.original).__qualname__}{self.RESET})"
        else:
            return f"({self._LIGHT_MAGENTA}{type(error).__qualname__}{self.RESET})"

    def CmdCall(self, ctx: discord.Interaction, *args, **kwargs) -> None:
        """指令被呼叫後Log模板"""
        cmd_name = (
            f"/{ctx.command.name}"
            if isinstance(ctx.command, discord.app_commands.Command)
            else f"\u200b{ctx.command.name}"
            if isinstance(ctx.command, discord.app_commands.ContextMenu)
            else "(無相關指令)"
        )

        def parse_argument(arg: Any) -> str:
            """將指令的參數內容轉成字串"""
            return (
                self.User(arg)
                if isinstance(arg, (discord.User, discord.Member))
                else arg.content
                if isinstance(arg, discord.Message)
                else str(arg)
            )

        arg_list = [parse_argument(arg) for arg in args]
        for name, argument in kwargs.items():
            arg_list.append(f"{self.__ParameterName__(name)}={parse_argument(argument)}")
        log = f"{self.User(ctx.user)} 使用了 {self.__CmdName__(cmd_name)}：{', '.join(arg_list)}"
        self.Cmd(log)

    def CmdResult(
        self,
        ctx: commands.Context | discord.Interaction,
        start_time: float = None,
        message: str | None = None,
        command_name: str | None = None,
        success: bool | None = True,
        show_timestamp: bool = True,
    ) -> None:
        """完整的指令結果Log模板

        Args:
            ctx (`commands.Context` | `discord.Interaction`):
                上下文或互動，用以取得指令、使用者、伺服器與頻道等資訊。
            start_time (`float`, optional):
                指令執行起始時間，用以計算總執行時間，傳入`None`則不顯示；預設為`None`。
            message (`str` | `None`, optional):
                額外要顯示在LOG上的訊息，傳入`None`則不顯示；預設為`None`。
            command_name (`str` | `None`, optional):
                指令名稱，可自行傳入指令名稱，傳入`None`則從上下文中取得；預設為`None`。
            success (`bool` | `None`, optional):
                指令執行成功與否，傳入`None`則僅記錄指令被執行；預設為`True`。
            show_timestamp (`bool`, optional):
                是否顯示時間戳；預設為`True`。
        """
        if isinstance(ctx, commands.Context):
            cmd_name = command_name if command_name != None else (ctx.prefix + ctx.command.name)
            log = f'{self.User(ctx.author)} 使用 {self.__CmdName__(cmd_name)} {("" if success == None else "成功" if success else "失敗")}。'
        else:  # discord.Interaction
            cmd_name = (
                command_name
                if command_name != None
                else f"/{ctx.command.name}"
                if isinstance(ctx.command, discord.app_commands.Command)
                else f"\u200b{ctx.command.name}"
                if isinstance(ctx.command, discord.app_commands.ContextMenu)
                else "(無相關指令)"
            )
            log = f'{self.User(ctx.user)} 使用 {self.__CmdName__(cmd_name)} {("" if success == None else "成功" if success else "失敗")}。'
        cost_time = f"耗時：{self.CostTime(start_time)}" if start_time != None else ""
        postition = f"\n伺服器：{self.Server(ctx.guild)}　頻道：{self.Channel(ctx.channel)}\n"
        msg = (
            f"\n訊息：{self._BRIGHT_PINK}{message}{self.RESET}\n"
            if message != None and message != ""
            else ""
        )
        #   輸出Log
        self.Cmd("⤷ " + log + cost_time + postition + msg, show_timestamp)

    def ErrorLog(
        self,
        ctx: commands.Context | discord.Interaction,
        error: commands.CommandInvokeError
        | commands.CommandError
        | discord.app_commands.AppCommandError
        | Exception,
    ) -> None:
        """指令內發生錯誤時Log模板"""
        msg = ""
        if isinstance(ctx, commands.Context):
            if isinstance(error, commands.CommandInvokeError):
                msg = f"{self.User(ctx.author)}執行指令期間發生錯誤{self.ErrorType(error)}：\n錯誤訊息：{self.__ErrorMsg__(error.original)}"
            elif isinstance(error, commands.CommandError):
                msg = f"{self.User(ctx.author)}引發指令錯誤{self.ErrorType(error)}：\n錯誤訊息：{self.__ErrorMsg__(error)}"
            else:
                msg = f"{self.User(ctx.author)}執行指令期間發生錯誤{self.ErrorType(error)}：\n錯誤訊息：{self.__ErrorMsg__(error)}"
        elif isinstance(ctx, discord.Interaction):
            if isinstance(error, discord.app_commands.AppCommandError):
                msg = f"{self.User(ctx.user)}引發斜線指令錯誤{self.ErrorType(error)}：\n錯誤訊息：{self.__ErrorMsg__(error)}"
            else:
                msg = f"{self.User(ctx.user)}執行斜線指令期間發生錯誤{self.ErrorType(error)}：\n錯誤訊息：{self.__ErrorMsg__(error)}"
        self.Error(msg)
        # if not isinstance(error, discord.NotFound):  # 忽略 Not Found 例外
        #     traceback.print_tb(error.__traceback__)

    def FuncExceptionLog(
        self, user: str | int, func_name: str, error: genshin.GenshinException | Exception
    ) -> None:
        """原神函式內發生例外Log模板"""
        msg = f"{self.User(user)} 執行函式 {self.__FuncName__(func_name)} 期間發生錯誤：\n"
        if isinstance(error, genshin.GenshinException):
            msg = msg + (
                f"retcode：{self.__ErrorMsg__(error.retcode)}、"
                f"原始內容：{self.__ErrorMsg__(error.original)}\n"
                f"錯誤訊息：{self.__ErrorMsg__(error.msg)}"
            )
        else:  # Exception
            msg = msg + f"錯誤訊息：{self.__ErrorMsg__(error)}"
        self.Except(msg)

    def HighLight(self, message: str) -> str:
        return f"{self._WHEAT_YELLOW}{message}{self.RESET}"

    def Note(self, message: str) -> str:
        return f"{self._GRAY_SCALE_4}{message}{self.RESET}"

    def __CmdName__(self, command_name: str) -> str:
        return f"{self._BRIGHT_BLUE}{command_name}{self.RESET}"

    def __FuncName__(self, func_name: str) -> str:
        return f"{self._BRIGHT_BLUE}{func_name}{self.RESET}"

    def __ParameterName__(self, parameter_name: str) -> str:
        return f"{self._WHEAT_YELLOW}{parameter_name}{self.RESET}"

    def __ErrorMsg__(self, error: Exception | str | int) -> str:
        return f"{self._RED}{error}{self.RESET}"


LOG = LogTool()


def SlashCommandLogger(func: Callable):
    """斜線指令Log裝飾器"""

    @wraps(func)
    async def inner(self, ctx: discord.Interaction, *args, **kwargs):
        LOG.CmdCall(ctx, *args, **kwargs)
        start_time = time.perf_counter()
        res = await func(self, ctx, *args, **kwargs)
        LOG.CmdResult(ctx, start_time)
        return res

    return inner


def ContextCommandLogger(func: Callable):
    """Context指令Log裝飾器"""

    @wraps(func)
    async def inner(ctx: discord.Interaction, *args, **kwargs):
        LOG.CmdCall(ctx, *args, **kwargs)
        start_time = time.perf_counter()
        res = await func(ctx, *args, **kwargs)
        LOG.CmdResult(ctx, start_time)
        return res

    return inner
