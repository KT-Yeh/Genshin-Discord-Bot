import discord
from discord.ext import commands

class CustomHelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)
        self.no_category = '幫助'
        self.indent = 2
        self.sort_commands = True
    
    async def send_bot_help(self, mapping):
        return await super().send_bot_help(mapping)

    async def send_cog_help(self, cog):
        return await super().send_cog_help(cog)

    async def send_group_help(self, group):
        return await super().send_group_help(group)

    async def send_command_help(self, command):
        return await super().send_command_help(command)

    def get_ending_note(self):
        command_name = self.invoked_with
        return f'輸入 "{self.context.clean_prefix}{command_name} 指令名稱" 來獲取該指令的詳細資訊'

cmd_attr = {
    'aliases': ["h"],
    'brief': '顯示本使用說明',
    'description': '顯示使用說明',
    'usage': '[指令]',
    'help': f'使用help [指令]來獲取該指令的詳細資訊'
}
custom_help = CustomHelpCommand(command_attrs=cmd_attr)