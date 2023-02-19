import asyncio
import shutil
from datetime import date, datetime, time, timedelta
from typing import Callable, Literal, Optional, Union

import discord
import sentry_sdk
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks

from data.database import ScheduleDaily, ScheduleResin, db
from genshin_py import automation, genshin_app
from utility import EmbedTemplate, config, get_app_command_mention
from utility.custom_log import LOG, SlashCommandLogger


class Schedule(commands.Cog, name="自動化"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.avg_user_daily_time = 3.0  # 初始化平均一位使用者的簽到時間(單位：秒)
        self.schedule.start()

    async def cog_unload(self) -> None:
        self.schedule.cancel()

    class ChooseGameButton(discord.ui.View):
        """選擇自動簽到遊戲的按鈕"""

        def __init__(self, author: Union[discord.User, discord.Member]):
            super().__init__(timeout=config.discord_view_short_timeout)
            self.value: Optional[str] = None
            self.author = author

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id

        @discord.ui.button(label="原神", style=discord.ButtonStyle.blurple)
        async def option1(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            self.value = "原神"
            self.stop()

        @discord.ui.button(label="原神+崩3", style=discord.ButtonStyle.blurple)
        async def option2(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            self.value = "原神+崩3"
            self.stop()

    class DailyMentionButton(discord.ui.View):
        """每日簽到是否要tag使用者"""

        def __init__(self, author: Union[discord.User, discord.Member]):
            super().__init__(timeout=config.discord_view_short_timeout)
            self.value = True
            self.author = author

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id

        @discord.ui.button(label="好！", style=discord.ButtonStyle.blurple)
        async def option1(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            self.value = True
            self.stop()

        @discord.ui.button(label="不用", style=discord.ButtonStyle.blurple)
        async def option2(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            self.value = False
            self.stop()

    class CheckingNotesThresholdModal(discord.ui.Modal, title="設定即時便箋提醒"):
        """設定檢查即時便箋各項閾值的表單"""

        resin = discord.ui.TextInput(
            label="原粹樹脂：設定樹脂額滿之前幾小時發送提醒 (不填表示不提醒)",
            placeholder="請輸入一個介於 0 ~ 5 的整數",
            required=False,
            max_length=1,
        )
        realm_currency = discord.ui.TextInput(
            label="洞天寶錢：設定寶錢額滿之前幾小時發送提醒 (不填表示不提醒)",
            placeholder="請輸入一個介於 0 ~ 8 的整數",
            required=False,
            max_length=1,
        )
        transformer = discord.ui.TextInput(
            label="質變儀：設定質變儀完成之前幾小時發送提醒 (不填表示不提醒)",
            placeholder="請輸入一個介於 0 ~ 5 的整數",
            required=False,
            max_length=1,
        )
        expedition = discord.ui.TextInput(
            label="探索派遣：設定全部派遣完成之前幾小時發送提醒 (不填表示不提醒)",
            placeholder="請輸入一個介於 0 ~ 5 的整數",
            required=False,
            max_length=1,
        )
        commission = discord.ui.TextInput(
            label="每日委託：設定每天幾點提醒今天的委託任務還未完成 (不填表示不提醒)",
            placeholder="請輸入一個介於 0000~2359 的數，例如 0200、2135",
            required=False,
            max_length=4,
            min_length=4,
        )

        def __init__(self, user_setting: Optional[ScheduleResin] = None) -> None:
            """設定表單預設值；若使用者在資料庫已有設定值，則帶入表單預設值"""
            self.resin.default = "1"
            self.realm_currency.default = None
            self.transformer.default = None
            self.expedition.default = None
            self.commission.default = None

            if user_setting:
                int_to_str: Callable[[Optional[int]], Optional[str]] = (
                    lambda i: str(i) if isinstance(i, int) else None
                )
                self.resin.default = int_to_str(user_setting.threshold_resin)
                self.realm_currency.default = int_to_str(user_setting.threshold_currency)
                self.transformer.default = int_to_str(user_setting.threshold_transformer)
                self.expedition.default = int_to_str(user_setting.threshold_expedition)
                self.commission.default = (
                    user_setting.check_commission_time.strftime("%H%M")
                    if user_setting.check_commission_time
                    else None
                )
            super().__init__()

        async def on_submit(self, interaction: discord.Interaction) -> None:
            try:
                # 將字串轉為數字
                str_to_int: Callable[[str], Optional[int]] = (
                    lambda string: int(string) if len(string) > 0 else None
                )
                resin = str_to_int(self.resin.value)
                realm_currency = str_to_int(self.realm_currency.value)
                transformer = str_to_int(self.transformer.value)
                expedition = str_to_int(self.expedition.value)
                commission = str_to_int(self.commission.value)

                # 檢查數字範圍
                if (
                    resin is None
                    and realm_currency is None
                    and transformer is None
                    and expedition is None
                    and commission is None
                ):
                    raise ValueError()
                if (
                    (isinstance(resin, int) and not (0 <= resin <= 5))
                    or (isinstance(realm_currency, int) and not (0 <= realm_currency <= 8))
                    or (isinstance(transformer, int) and not (0 <= transformer <= 5))
                    or (isinstance(expedition, int) and not (0 <= expedition <= 5))
                ):
                    raise ValueError()
                commission_time = None
                if isinstance(commission, int):
                    _time = time(commission // 100, commission % 100)  # 當數字超過範圍時time會拋出例外
                    _date = date.today()
                    commission_time = datetime.combine(_date, _time)
                    # 當今天已經超過設定的時間，則將檢查時間設為明日
                    if commission_time < datetime.now():
                        commission_time += timedelta(days=1)
            except Exception:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("輸入數值有誤，請確認輸入的數值為整數且在規定範圍內"),
                    ephemeral=True,
                )
            else:
                # 儲存設定資料
                await db.schedule_resin.add(
                    ScheduleResin(
                        id=interaction.user.id,
                        channel_id=interaction.channel_id or 0,
                        threshold_resin=resin,
                        threshold_currency=realm_currency,
                        threshold_transformer=transformer,
                        threshold_expedition=expedition,
                        check_commission_time=commission_time,
                    )
                )
                to_msg: Callable[[str, Optional[int]], str] = (
                    lambda title, value: ""
                    if value is None
                    else f"． {title}：當完成時提醒\n"
                    if value == 0
                    else f"． {title}：完成前 {value} 小時提醒\n"
                )
                commission_to_msg: Callable[[str, Optional[datetime]], str] = (
                    lambda title, value: ""
                    if value is None
                    else f"． {title}：每天 {value.strftime('%H:%M')} 檢查\n"
                )
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal(
                        f"設定完成，當達到以下設定值時會發送提醒訊息：\n"
                        f"{to_msg('原粹樹脂', resin)}"
                        f"{to_msg('洞天寶錢', realm_currency)}"
                        f"{to_msg('質變儀　', transformer)}"
                        f"{to_msg('探索派遣', expedition)}"
                        f"{commission_to_msg('每日委託', commission_time)}"
                    )
                )

    # 設定自動排程功能的斜線指令
    @app_commands.command(name="schedule排程", description="設定自動化功能(Hoyolab每日簽到、樹脂額滿提醒)")
    @app_commands.rename(function="功能", switch="開關")
    @app_commands.describe(function="選擇要執行自動化的功能", switch="選擇開啟或關閉此功能")
    @app_commands.choices(
        function=[
            Choice(name="① 顯示使用說明", value="HELP"),
            Choice(name="② 訊息推送測試", value="TEST"),
            Choice(name="★ 每日自動簽到", value="DAILY"),
            Choice(name="★ 即時便箋提醒", value="NOTES"),
        ],
        switch=[Choice(name="開啟功能", value="ON"), Choice(name="關閉功能", value="OFF")],
    )
    @SlashCommandLogger
    async def slash_schedule(
        self,
        interaction: discord.Interaction,
        function: Literal["HELP", "TEST", "DAILY", "NOTES"],
        switch: Literal["ON", "OFF"],
    ):
        if function == "HELP":  # 排程功能使用說明
            msg = (
                "· 排程會在特定時間執行功能，執行結果會在設定指令的頻道推送\n"
                "· 設定前請先確認小幫手有在該頻道發言的權限，如果推送訊息失敗，小幫手會自動移除排程設定\n"
                "· 若要更改推送頻道，請在新的頻道重新設定指令一次\n\n"
                f"· 每日自動簽到：每日 {config.schedule_daily_reward_time} 點依照使用者登記順序開始自動簽到，"
                f"現在登記預計簽到時間為 {await self.predict_daily_checkin_time()}，"
                f'設定前請先使用 {get_app_command_mention("daily每日簽到")} 指令確認小幫手能幫你簽到\n'
                f'· 即時便箋提醒：當超過設定值時會發送提醒，設定前請先用 {get_app_command_mention("notes即時便箋")} '
                f"指令確認小幫手能讀到你的樹脂資訊\n"
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
        user = await db.users.get(interaction.user.id)
        check, msg = await db.users.exist(user)
        if check is False and msg is not None:
            await interaction.response.send_message(embed=EmbedTemplate.error(msg))
            return

        if function == "DAILY":  # 每日自動簽到
            if switch == "ON":  # 開啟簽到功能
                choose_game_btn = self.ChooseGameButton(interaction.user)
                await interaction.response.send_message("請選擇要自動簽到的遊戲：", view=choose_game_btn)
                await choose_game_btn.wait()
                if choose_game_btn.value is None:
                    await interaction.edit_original_response(
                        embed=EmbedTemplate.normal("已取消"), content=None, view=None
                    )
                    return

                daily_mention_btn = self.DailyMentionButton(interaction.user)
                await interaction.edit_original_response(
                    content=f"每日自動簽到時希望小幫手tag你({interaction.user.mention})嗎？",
                    view=daily_mention_btn,
                )
                await daily_mention_btn.wait()

                # 新增使用者
                await db.schedule_daily.add(
                    ScheduleDaily(
                        id=interaction.user.id,
                        channel_id=interaction.channel_id or 0,
                        is_mention=daily_mention_btn.value,
                        has_honkai=(True if choose_game_btn.value == "原神+崩3" else False),
                    )
                )
                await interaction.edit_original_response(
                    embed=EmbedTemplate.normal(
                        f"{choose_game_btn.value}每日自動簽到已開啟，"
                        f'簽到時小幫手{"會" if daily_mention_btn.value else "不會"}tag你\n'
                        f"今日已幫你簽到，明日預計簽到的時間為 {await self.predict_daily_checkin_time()} 左右"
                    ),
                    content=None,
                    view=None,
                )
                # 設定完成後幫使用者當日簽到
                await genshin_app.claim_daily_reward(
                    interaction.user.id, honkai=(choose_game_btn.value == "原神+崩3")
                )
                await db.schedule_daily.update(interaction.user.id, last_checkin_date=True)
            elif switch == "OFF":  # 關閉簽到功能
                await db.schedule_daily.remove(interaction.user.id)
                await interaction.response.send_message(embed=EmbedTemplate.normal("每日自動簽到已關閉"))

        elif function == "NOTES":  # 即時便箋檢查提醒
            if switch == "ON":  # 開啟即時便箋檢查功能
                user_setting = await db.schedule_resin.get(interaction.user.id)
                await interaction.response.send_modal(
                    self.CheckingNotesThresholdModal(user_setting)
                )
            elif switch == "OFF":  # 關閉即時便箋檢查功能
                await db.schedule_resin.remove(interaction.user.id)
                await interaction.response.send_message(embed=EmbedTemplate.normal("即時便箋檢查提醒已關閉"))

    # 具有頻道管理訊息權限的人可使用本指令，移除指定使用者的頻道排程設定
    @app_commands.command(name="移除排程使用者", description="擁有管理此頻道訊息權限的人可使用本指令，移除指定使用者的排程設定")
    @app_commands.rename(function="功能", user="使用者")
    @app_commands.describe(function="選擇要移除的功能")
    @app_commands.choices(
        function=[
            Choice(name="每日自動簽到", value="daily"),
            Choice(name="樹脂額滿提醒", value="resin"),
        ]
    )
    @app_commands.default_permissions(manage_messages=True)
    @SlashCommandLogger
    async def slash_remove_user(
        self, interaction: discord.Interaction, function: str, user: discord.User
    ):
        if function == "daily":
            await db.schedule_daily.remove(user.id)
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(f"{user.display_name}的每日自動簽到已關閉")
            )
        elif function == "resin":
            await db.schedule_resin.remove(user.id)
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(f"{user.display_name}的樹脂額滿提醒已關閉")
            )

    loop_interval = 1  # 循環間隔1分鐘

    @tasks.loop(minutes=loop_interval)
    async def schedule(self):
        """排程主循環，每 {loop_interval} 分鐘執行排程相關函式"""

        now = datetime.now()
        # 確認沒有在遊戲維護時間內
        if config.game_maintenance_time is None or not (
            config.game_maintenance_time[0] <= now < config.game_maintenance_time[1]
        ):
            # 每日 {config.schedule_daily_reward_time} 點開始自動簽到
            if now.hour == config.schedule_daily_reward_time and now.minute < self.loop_interval:
                asyncio.create_task(automation.claim_daily_reward(self.bot))

            # 每 {config.schedule_check_resin_interval} 分鐘檢查一次樹脂
            if now.minute % config.schedule_check_resin_interval < self.loop_interval:
                asyncio.create_task(automation.check_realtime_notes(self.bot))

        # 每日凌晨一點備份資料庫、刪除過期使用者資料
        if now.hour == 1 and now.minute < self.loop_interval:
            try:
                db_path = config.database_file_path
                today = date.today()
                shutil.copyfile(db_path, f"{db_path.split('.')[0]}_backup_{today}.db")
            except Exception as e:
                LOG.Error(str(e))
                sentry_sdk.capture_exception(e)
            asyncio.create_task(db.removeExpiredUser(config.expired_user_days))

    @schedule.before_loop
    async def before_schedule(self):
        await self.bot.wait_until_ready()

    async def predict_daily_checkin_time(self) -> str:
        """現在登記簽到，預計的簽到時間 (%H:%M)"""
        total_users = await db.schedule_daily.getTotalNumber()
        base_time = datetime.combine(
            date.today(), time(config.schedule_daily_reward_time)
        )  # 每日開始簽到的時間
        elapsed_time = timedelta(seconds=(self.avg_user_daily_time * total_users))  # 簽到全部使用者需要的時間
        return (base_time + elapsed_time).strftime("%H:%M")


async def setup(client: commands.Bot):
    await client.add_cog(Schedule(client))
