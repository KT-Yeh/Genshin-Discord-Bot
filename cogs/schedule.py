import asyncio
import discord
import shutil
import sentry_sdk
from datetime import datetime, date, timedelta, time
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from typing import Callable, Optional
from utility import genshin_app, config, getAppCommandMention, EmbedTemplate
from utility.custom_log import LOG, SlashCommandLogger
from data.database import db, ScheduleDaily, ScheduleResin


class Schedule(commands.Cog, name="自動化"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.avg_user_daily_time = 3.0  # 初始化平均一位使用者的簽到時間(單位：秒)
        self.schedule.start()

    async def cog_unload(self) -> None:
        self.schedule.cancel()

    class ChooseGameButton(discord.ui.View):
        """選擇自動簽到遊戲的按鈕"""

        def __init__(self, author: discord.Member):
            super().__init__(timeout=config.discord_view_short_timeout)
            self.value = None
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

        def __init__(self, author: discord.Member):
            super().__init__(timeout=config.discord_view_short_timeout)
            self.value = True
            self.author = author

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id

        @discord.ui.button(label="好！", style=discord.ButtonStyle.blurple)
        async def option1(self, interaction: discord.Interaction, button: discord.ui.button):
            await interaction.response.defer()
            self.value = True
            self.stop()

        @discord.ui.button(label="不用", style=discord.ButtonStyle.blurple)
        async def option2(self, interaction: discord.Interaction, button: discord.ui.button):
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
            # 設定表單預設值；若使用者在資料庫已有設定值，則帶入表單預設值
            int_to_str: Callable[[Optional[int]], Optional[str]] = (
                lambda i: str(i) if isinstance(i, int) else None
            )
            self.resin.default = int_to_str(user_setting.threshold_resin) if user_setting else "1"
            self.realm_currency.default = (
                int_to_str(user_setting.threshold_currency) if user_setting else None
            )
            self.transformer.default = (
                int_to_str(user_setting.threshold_transformer) if user_setting else None
            )
            self.expedition.default = (
                int_to_str(user_setting.threshold_expedition) if user_setting else None
            )
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
                    resin == None
                    and realm_currency == None
                    and transformer == None
                    and expedition == None
                    and commission == None
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
                        channel_id=interaction.channel_id,
                        threshold_resin=resin,
                        threshold_currency=realm_currency,
                        threshold_transformer=transformer,
                        threshold_expedition=expedition,
                        check_commission_time=commission_time,
                    )
                )
                to_msg: Callable[[str, Optional[int]], str] = (
                    lambda title, value: ""
                    if value == None
                    else f"． {title}：當完成時提醒\n"
                    if value == 0
                    else f"． {title}：完成前 {value} 小時提醒\n"
                )
                commission_to_msg: Callable[[str, Optional[datetime]], str] = (
                    lambda title, value: ""
                    if value == None
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
            Choice(name="① 顯示使用說明", value="help"),
            Choice(name="② 訊息推送測試", value="test"),
            Choice(name="★ 每日自動簽到", value="daily"),
            Choice(name="★ 即時便箋提醒", value="resin"),
        ],
        switch=[Choice(name="開啟功能", value=1), Choice(name="關閉功能", value=0)],
    )
    @SlashCommandLogger
    async def slash_schedule(self, interaction: discord.Interaction, function: str, switch: int):
        if function == "help":  # 排程功能使用說明
            msg = (
                "· 排程會在特定時間執行功能，執行結果會在設定指令的頻道推送\n"
                "· 設定前請先確認小幫手有在該頻道發言的權限，如果推送訊息失敗，小幫手會自動移除排程設定\n"
                "· 若要更改推送頻道，請在新的頻道重新設定指令一次\n\n"
                f"· 每日自動簽到：每日 {config.schedule_daily_reward_time} 點依照使用者登記順序開始自動簽到，"
                f'現在登記預計簽到時間為 {await self.predict_daily_checkin_time()}，設定前請先使用 {getAppCommandMention("daily每日簽到")} 指令確認小幫手能幫你簽到\n'
                f'· 即時便箋提醒：當超過設定值時會發送提醒，設定前請先用 {getAppCommandMention("notes即時便箋")} 指令確認小幫手能讀到你的樹脂資訊\n'
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(msg, title="排程功能使用說明"), ephemeral=True
            )
            return

        if function == "test":  # 測試機器人是否能在該頻道推送訊息
            try:
                msg_sent = await interaction.channel.send("測試推送訊息...")
            except:
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
        if check == False:
            await interaction.response.send_message(embed=EmbedTemplate.error(msg))
            return
        if function == "daily":  # 每日自動簽到
            if switch == 1:  # 開啟簽到功能
                choose_game_btn = self.ChooseGameButton(interaction.user)
                await interaction.response.send_message("請選擇要自動簽到的遊戲：", view=choose_game_btn)
                await choose_game_btn.wait()
                if choose_game_btn.value == None:
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
                        channel_id=interaction.channel_id,
                        is_mention=daily_mention_btn.value,
                        has_honkai=(True if choose_game_btn.value == "原神+崩3" else False),
                    )
                )
                await interaction.edit_original_response(
                    embed=EmbedTemplate.normal(
                        f'{choose_game_btn.value}每日自動簽到已開啟，簽到時小幫手{"會" if daily_mention_btn.value else "不會"}tag你\n'
                        f"今日已幫你簽到，明日預計簽到的時間為 {await self.predict_daily_checkin_time()} 左右"
                    ),
                    content=None,
                    view=None,
                )
                # 設定完成後幫使用者當日簽到
                await genshin_app.claimDailyReward(
                    interaction.user.id, honkai=(choose_game_btn.value == "原神+崩3")
                )
                await db.schedule_daily.update(interaction.user.id, last_checkin_date=True)
            elif switch == 0:  # 關閉簽到功能
                await db.schedule_daily.remove(interaction.user.id)
                await interaction.response.send_message(embed=EmbedTemplate.normal("每日自動簽到已關閉"))
        elif function == "resin":  # 即時便箋檢查提醒
            if switch == 1:  # 開啟即時便箋檢查功能
                user_setting = await db.schedule_resin.get(interaction.user.id)
                await interaction.response.send_modal(
                    self.CheckingNotesThresholdModal(user_setting)
                )
            elif switch == 0:  # 關閉即時便箋檢查功能
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
        now = datetime.now()
        # 確認沒有在遊戲維護時間內
        if config.game_maintenance_time == None or not (
            config.game_maintenance_time[0] <= now < config.game_maintenance_time[1]
        ):
            # 每日 {config.schedule_daily_reward_time} 點開始自動簽到
            if now.hour == config.schedule_daily_reward_time and now.minute < self.loop_interval:
                asyncio.create_task(self.autoClaimDailyReward())

            # 每 {config.schedule_check_resin_interval} 分鐘檢查一次樹脂
            if now.minute % config.schedule_check_resin_interval < self.loop_interval:
                asyncio.create_task(self.autoCheckResin())

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

    async def autoClaimDailyReward(self):
        LOG.System("每日自動簽到開始")
        start_time = datetime.now()  # 簽到開始時間
        total, honkai_count = 0, 0  # 統計簽到人數
        daily_users = await db.schedule_daily.getAll()
        for user in daily_users:
            # 檢查今天是否已經簽到過
            if user.last_checkin_date == date.today():
                continue
            # 簽到並更新最後簽到時間
            result = await genshin_app.claimDailyReward(
                user.id, honkai=user.has_honkai, schedule=True
            )
            await db.schedule_daily.update(user.id, last_checkin_date=True)
            total += 1
            honkai_count += int(user.has_honkai)
            try:
                channel = self.bot.get_channel(user.channel_id) or await self.bot.fetch_channel(
                    user.channel_id
                )
                # 若不用@提及使用者，則先取得此使用者的暱稱然後發送訊息
                if user.is_mention == False:
                    _user = await self.bot.fetch_user(user.id)
                    await channel.send(f"[自動簽到] {_user.display_name}：{result}")
                else:
                    await channel.send(f"[自動簽到] <@{user.id}> {result}")
            except Exception as e:  # 發送訊息失敗，移除此使用者
                LOG.Except(f"自動簽到發送訊息失敗，移除此使用者 {LOG.User(user.id)}：{e}")
                await db.schedule_daily.remove(user.id)
            await asyncio.sleep(config.schedule_loop_delay)
        LOG.System(f"每日自動簽到結束，總共 {total} 人簽到，其中 {honkai_count} 人也簽到崩壞3")
        # 發送統計結果到通知頻道
        if config.notification_channel_id:
            end_time = datetime.now()
            self.avg_user_daily_time = (end_time - start_time).total_seconds() / (
                total if total > 0 else 1
            )
            embed = EmbedTemplate.normal(
                f"總共 {total} 人簽到，其中 {honkai_count} 人也簽到崩壞3\n"
                f"簽到時間：{start_time.strftime('%H:%M:%S')} ~ {end_time.strftime('%H:%M:%S')}\n"
                f"平均時間：{self.avg_user_daily_time:.2f} 秒/人",
                title="每日自動簽到結果",
            )
            await self.bot.get_channel(config.notification_channel_id).send(embed=embed)

    async def autoCheckResin(self):
        LOG.System("自動檢查樹脂開始")
        resin_users = await db.schedule_resin.getAll()
        count = 0  # 統計人數
        for user in resin_users:
            # 若還沒到檢查時間則跳過此使用者
            if user.next_check_time and datetime.now() < user.next_check_time:
                continue
            # 檢查使用者即時便箋
            try:
                notes = await genshin_app.getRealtimeNote(user.id, schedule=True)
            except Exception as e:
                msg = f"自動檢查樹脂時發生錯誤：{str(e)}\n預計5小時後再檢查"
                # 當發生錯誤時，預計5小時後再檢查
                await db.schedule_resin.update(
                    user.id, next_check_time=(datetime.now() + timedelta(hours=5))
                )
                embed = None
            else:  # 正常檢查即時便箋
                msg = ""
                embed = await genshin_app.parseNotes(notes, shortForm=True)
                next_check_time: list[datetime] = [
                    datetime.now() + timedelta(days=1)
                ]  # 設定一個基本的下次檢查時間
                # 計算下次檢查時間的函式：預計完成時間-使用者設定的時間
                cal_nxt_check_time: Callable[[timedelta, int], datetime] = (
                    lambda remaining, user_threshold: datetime.now()
                    + remaining
                    - timedelta(hours=user_threshold)
                )
                # 檢查樹脂
                if isinstance(user.threshold_resin, int):
                    # 當樹脂距離額滿時間低於設定值，則設定要發送的訊息
                    if notes.remaining_resin_recovery_time <= timedelta(
                        hours=user.threshold_resin, seconds=10
                    ):
                        msg += (
                            "樹脂已經額滿啦！"
                            if notes.remaining_resin_recovery_time <= timedelta(0)
                            else "樹脂快要額滿啦！"
                        )
                    # 設定下次檢查時間，當樹脂完全額滿時，預計6小時後再檢查；否則依照(預計完成-使用者設定的時間)
                    next_check_time.append(
                        datetime.now() + timedelta(hours=6)
                        if notes.current_resin >= notes.max_resin
                        else cal_nxt_check_time(
                            notes.remaining_resin_recovery_time, user.threshold_resin
                        )
                    )
                # 檢查洞天寶錢
                if isinstance(user.threshold_currency, int):
                    if notes.remaining_realm_currency_recovery_time <= timedelta(
                        hours=user.threshold_currency, seconds=10
                    ):
                        msg += (
                            "洞天寶錢已經額滿啦！"
                            if notes.remaining_realm_currency_recovery_time <= timedelta(0)
                            else "洞天寶錢快要額滿啦！"
                        )
                    next_check_time.append(
                        datetime.now() + timedelta(hours=6)
                        if notes.current_realm_currency >= notes.max_realm_currency
                        else cal_nxt_check_time(
                            notes.remaining_realm_currency_recovery_time,
                            user.threshold_currency,
                        )
                    )
                # 檢查質變儀
                if isinstance(user.threshold_transformer, int) and isinstance(
                    notes.transformer_recovery_time, datetime
                ):
                    if notes.remaining_transformer_recovery_time <= timedelta(
                        hours=user.threshold_transformer, seconds=10
                    ):
                        msg += (
                            "質變儀已經完成了！"
                            if notes.remaining_transformer_recovery_time <= timedelta(0)
                            else "質變儀快要完成了！"
                        )
                    next_check_time.append(
                        datetime.now() + timedelta(hours=6)
                        if notes.remaining_transformer_recovery_time.total_seconds() <= 5
                        else cal_nxt_check_time(
                            notes.remaining_transformer_recovery_time,
                            user.threshold_transformer,
                        )
                    )
                # 檢查探索派遣
                if isinstance(user.threshold_expedition, int) and len(notes.expeditions) > 0:
                    # 選出剩餘時間最多的派遣
                    longest_expedition = max(notes.expeditions, key=lambda epd: epd.remaining_time)
                    if longest_expedition.remaining_time <= timedelta(
                        hours=user.threshold_expedition, seconds=10
                    ):
                        msg += (
                            "探索派遣已經完成了！"
                            if longest_expedition.remaining_time <= timedelta(0)
                            else "探索派遣快要完成了！"
                        )
                    next_check_time.append(
                        datetime.now() + timedelta(hours=6)
                        if longest_expedition.finished == True
                        else cal_nxt_check_time(
                            longest_expedition.remaining_time, user.threshold_expedition
                        )
                    )
                # 檢查每日委託
                if isinstance(user.check_commission_time, datetime):
                    _next_check_time = user.check_commission_time
                    # 當現在時間已超過設定的檢查時間
                    if datetime.now() >= user.check_commission_time:
                        if not notes.claimed_commission_reward:
                            msg += "今日的委託任務還未完成！"
                        # 下次檢查時間為今天+1天，並更新至資料庫
                        _next_check_time += timedelta(days=1)
                        await db.schedule_resin.update(
                            user.id, check_commission_time=_next_check_time
                        )
                    next_check_time.append(_next_check_time)

                # 設定下次檢查時間，從上面設定的時間中取最小的值
                check_time = min(next_check_time)
                # 若此次需要發送訊息，則將下次檢查時間設為至少1小時
                if len(msg) > 0:
                    check_time = max(check_time, datetime.now() + timedelta(minutes=60))
                await db.schedule_resin.update(user.id, next_check_time=check_time)
            count += 1
            # 當有錯誤訊息或是樹脂快要溢出時，向使用者發送訊息
            if len(msg) > 0:
                try:  # 發送訊息提醒使用者
                    channel = self.bot.get_channel(
                        user.channel_id
                    ) or await self.bot.fetch_channel(user.channel_id)
                    _user = await self.bot.fetch_user(user.id)
                    msg_sent = await channel.send(f"{_user.mention}，{msg}", embed=embed)
                except Exception as e:  # 發送訊息失敗，移除此使用者
                    LOG.Except(f"自動檢查樹脂發送訊息失敗，移除此使用者 {LOG.User(user.id)}：{e}")
                    await db.schedule_resin.remove(user.id)
                else:  # 成功發送訊息
                    # 若使用者不在發送訊息的頻道則移除
                    if _user.mentioned_in(msg_sent) == False:
                        LOG.Except(f"自動檢查樹脂使用者不在頻道，移除此使用者 {LOG.User(_user)}")
                        await db.schedule_resin.remove(user.id)
            await asyncio.sleep(config.schedule_loop_delay)
        LOG.System(f"自動檢查樹脂結束，{count}/{len(resin_users)} 人已檢查")

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
