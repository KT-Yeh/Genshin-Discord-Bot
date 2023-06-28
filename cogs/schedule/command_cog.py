from datetime import date, datetime, time, timedelta
from typing import Literal

import discord
import genshin
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import database
import genshin_py
from database import Database, GenshinScheduleNotes, ScheduleDailyCheckin, StarrailScheduleNotes
from utility import EmbedTemplate, config, get_app_command_mention
from utility.custom_log import SlashCommandLogger

from .ui import (
    DailyRewardOptionsView,
    GenshinNotesThresholdModal,
    StarrailCheckNotesThresholdModal,
)


class ScheduleCommandCog(commands.Cog, name="排程設定指令"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.avg_user_daily_time = 2.8 / (1 + len(config.daily_reward_api_list)) + 0.2
        """平均一位使用者的簽到時間(單位：秒)，預設值是根據有多少 API 服務能夠同時簽到做計算"""

    # 設定自動排程功能的斜線指令
    @app_commands.command(name="schedule排程", description="設定排程功能(Hoyolab每日簽到、樹脂額滿提醒)")
    @app_commands.rename(function="功能", switch="開關")
    @app_commands.describe(function="選擇要執行排程的功能", switch="選擇開啟或關閉此功能")
    @app_commands.choices(
        function=[
            Choice(name="① 顯示使用說明", value="HELP"),
            Choice(name="② 訊息推送測試", value="TEST"),
            Choice(name="★ 每日自動簽到", value="DAILY"),
            Choice(name="★ 即時便箋提醒(原神)", value="GENSHIN_NOTES"),
            Choice(name="★ 即時便箋提醒(星穹鐵道)", value="STARRAIL_NOTES"),
        ],
        switch=[Choice(name="開啟或更新設定", value="ON"), Choice(name="關閉功能", value="OFF")],
    )
    @SlashCommandLogger
    async def slash_schedule(
        self,
        interaction: discord.Interaction,
        function: Literal["HELP", "TEST", "DAILY", "GENSHIN_NOTES", "STARRAIL_NOTES"],
        switch: Literal["ON", "OFF"],
    ):
        msg: str | None  # 欲傳給使用者的訊息
        if function == "HELP":  # 排程功能使用說明
            msg = (
                "· 排程會在特定時間執行功能，執行結果會在設定指令的頻道推送\n"
                "· 設定前請先確認小幫手有在該頻道發言的權限，如果推送訊息失敗，小幫手會自動移除排程設定\n"
                "· 若要更改推送頻道，請在新的頻道重新設定指令一次\n\n"
                f"· 每日自動簽到：每日 {config.schedule_daily_reward_time} 點依照使用者登記順序開始自動簽到，"
                f"現在登記預計簽到時間為 {await self.predict_daily_checkin_time()}，"
                f'設定前請先使用 {get_app_command_mention("daily每日簽到")} 指令確認小幫手能幫你簽到\n'
                f'· 即時便箋提醒：當超過設定值時會發送提醒，設定前請先用 {get_app_command_mention("notes即時便箋")} '
                f"指令確認小幫手能讀到你的即時便箋資訊\n\n"
                f"· 簽到圖形驗證問題：現在原神簽到會遇到圖形驗證的問題，需要先使用 "
                f"{get_app_command_mention('daily每日簽到')} 指令，選項選擇「設定圖形驗證」"
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(msg, title="排程功能使用說明"), ephemeral=True
            )
            return

        if function == "TEST":  # 測試機器人是否能在該頻道推送訊息
            try:
                msg_sent = await interaction.channel.send("測試推送訊息...")  # type: ignore
            except Exception:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("小幫手無法在本頻道推送訊息，請管理員檢查身分組的權限設定")
                )
            else:
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("測試完成，小幫手可以在本頻道推送訊息")
                )
                await msg_sent.delete()
            return

        # 設定前先確認使用者是否有Cookie資料
        user = await Database.select_one(
            database.User, database.User.discord_id.is_(interaction.user.id)
        )
        match function:
            case "DAILY":
                check, msg = await database.Tool.check_user(user)
            case "GENSHIN_NOTES":
                check, msg = await database.Tool.check_user(
                    user, check_uid=True, game=genshin.Game.GENSHIN
                )
            case "STARRAIL_NOTES":
                check, msg = await database.Tool.check_user(
                    user, check_uid=True, game=genshin.Game.STARRAIL
                )

        if check is False:
            await interaction.response.send_message(embed=EmbedTemplate.error(msg))
            return

        if function == "DAILY":  # 每日自動簽到
            if switch == "ON":  # 開啟簽到功能
                # 使用下拉選單讓使用者選擇要簽到的遊戲
                options_view = DailyRewardOptionsView(interaction.user)
                await interaction.response.send_message(
                    "請依序選擇：\n1. 要簽到的遊戲 (請選擇 1~3 項)\n"
                    f"2. 簽到時希望小幫手 tag 你 ({interaction.user.mention}) 嗎？",
                    view=options_view,
                )
                await options_view.wait()
                if options_view.value is None or options_view.is_mention is None:
                    await interaction.edit_original_response(
                        embed=EmbedTemplate.normal("已取消"), content=None, view=None
                    )
                    return

                # 新增使用者
                checkin_time = datetime.combine(datetime.now(), time(8, 0))
                checkin_user = ScheduleDailyCheckin(
                    discord_id=interaction.user.id,
                    discord_channel_id=interaction.channel_id or 0,
                    is_mention=options_view.is_mention,
                    next_checkin_time=checkin_time,
                    has_genshin=options_view.has_genshin,
                    has_honkai3rd=options_view.has_honkai3rd,
                    has_starrail=options_view.has_starrail,
                )
                await Database.insert_or_replace(checkin_user)

                await interaction.edit_original_response(
                    embed=EmbedTemplate.normal(
                        f"{options_view.value} 每日自動簽到已開啟，"
                        f'簽到時小幫手{"會" if options_view.is_mention else "不會"} tag 你\n'
                        f"今日已幫你簽到，明日預計簽到的時間為 {await self.predict_daily_checkin_time()} 左右"
                    ),
                    content=None,
                    view=None,
                )
                # 設定完成後幫使用者當日簽到
                await genshin_py.claim_daily_reward(
                    interaction.user.id,
                    has_genshin=options_view.has_genshin,
                    has_honkai3rd=options_view.has_honkai3rd,
                    has_starrail=options_view.has_starrail,
                )
                checkin_user.update_next_checkin_time()
                await Database.insert_or_replace(checkin_user)

            elif switch == "OFF":  # 關閉簽到功能
                await Database.delete(
                    ScheduleDailyCheckin, ScheduleDailyCheckin.discord_id.is_(interaction.user.id)
                )
                await interaction.response.send_message(embed=EmbedTemplate.normal("每日自動簽到已關閉"))

        elif function == "GENSHIN_NOTES":  # 原神即時便箋檢查提醒
            if switch == "ON":  # 開啟即時便箋檢查功能
                genshin_setting = await Database.select_one(
                    GenshinScheduleNotes,
                    GenshinScheduleNotes.discord_id.is_(interaction.user.id),
                )
                await interaction.response.send_modal(GenshinNotesThresholdModal(genshin_setting))
            elif switch == "OFF":  # 關閉即時便箋檢查功能
                await Database.delete(
                    GenshinScheduleNotes,
                    GenshinScheduleNotes.discord_id.is_(interaction.user.id),
                )
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("原神即時便箋檢查提醒已關閉")
                )

        elif function == "STARRAIL_NOTES":  # 星穹鐵道即時便箋檢查提醒
            if switch == "ON":  # 開啟即時便箋檢查功能
                starrail_setting = await Database.select_one(
                    StarrailScheduleNotes,
                    StarrailScheduleNotes.discord_id.is_(interaction.user.id),
                )
                await interaction.response.send_modal(
                    StarrailCheckNotesThresholdModal(starrail_setting)
                )
            elif switch == "OFF":  # 關閉即時便箋檢查功能
                await Database.delete(
                    StarrailScheduleNotes,
                    StarrailScheduleNotes.discord_id.is_(interaction.user.id),
                )
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("星穹鐵道即時便箋檢查提醒已關閉")
                )

    # 具有頻道管理訊息權限的人可使用本指令，移除指定使用者的頻道排程設定
    @app_commands.command(name="移除排程使用者", description="擁有管理此頻道訊息權限的人可使用本指令，移除指定使用者的排程設定")
    @app_commands.rename(function="功能", user="使用者")
    @app_commands.describe(function="選擇要移除的功能")
    @app_commands.choices(
        function=[
            Choice(name="每日自動簽到", value="DAILY"),
            Choice(name="即時便箋提醒(原神)", value="GENSHIN_NOTES"),
            Choice(name="即時便箋提醒(星穹鐵道)", value="STARRAIL_NOTES"),
        ]
    )
    @app_commands.default_permissions(manage_messages=True)
    @SlashCommandLogger
    async def slash_remove_user(
        self,
        interaction: discord.Interaction,
        function: Literal["DAILY", "GENSHIN_NOTES", "STARRAIL_NOTES"],
        user: discord.User,
    ):
        channel_id = interaction.channel_id
        if function == "DAILY":
            await Database.delete(
                ScheduleDailyCheckin,
                ScheduleDailyCheckin.discord_id.is_(user.id)
                & ScheduleDailyCheckin.discord_channel_id.is_(channel_id),
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(f"{user.name}的每日自動簽到已關閉")
            )
        elif function == "GENSHIN_NOTES":
            await Database.delete(
                GenshinScheduleNotes,
                GenshinScheduleNotes.discord_id.is_(user.id)
                & GenshinScheduleNotes.discord_channel_id.is_(channel_id),
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(f"{user.name}的原神即時便箋提醒已關閉")
            )
        elif function == "STARRAIL_NOTES":
            await Database.delete(
                StarrailScheduleNotes,
                StarrailScheduleNotes.discord_id.is_(user.id)
                & StarrailScheduleNotes.discord_channel_id.is_(channel_id),
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(f"{user.name}的星穹鐵道即時便箋提醒已關閉")
            )

    async def predict_daily_checkin_time(self) -> str:
        """現在登記簽到，預計的簽到時間 (%H:%M)"""
        total_users = len(await Database.select_all(ScheduleDailyCheckin))
        base_time = datetime.combine(
            date.today(), time(config.schedule_daily_reward_time)
        )  # 每日開始簽到的時間
        elapsed_time = timedelta(seconds=(self.avg_user_daily_time * total_users))  # 簽到全部使用者需要的時間
        return (base_time + elapsed_time).strftime("%H:%M")


async def setup(client: commands.Bot):
    await client.add_cog(ScheduleCommandCog(client))
