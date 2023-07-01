from datetime import date, datetime, time, timedelta
from typing import overload

import discord

from database import Database, GenshinScheduleNotes, StarrailScheduleNotes
from utility import EmbedTemplate, config


class DailyRewardOptionsView(discord.ui.View):
    """自動簽到每日的選項，包含遊戲與是否 tag 使用者"""

    def __init__(self, author: discord.User | discord.Member):
        super().__init__(timeout=config.discord_view_short_timeout)
        self.value: str | None = None
        self.has_genshin: bool = False
        self.has_honkai3rd: bool = False
        self.has_starrail: bool = False
        self.is_mention: bool | None = None
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.select(
        cls=discord.ui.Select,
        options=[
            discord.SelectOption(label="原神", value="原神"),
            discord.SelectOption(label="崩壞3", value="崩壞3"),
            discord.SelectOption(label="星穹鐵道", value="星穹鐵道"),
        ],
        min_values=1,
        max_values=3,
        placeholder="請選擇要簽到的遊戲 (可多選)：",
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
        self.value = " + ".join(select.values)
        if "原神" in self.value:
            self.has_genshin = True
        if "崩壞3" in self.value:
            self.has_honkai3rd = True
        if "星穹鐵道" in self.value:
            self.has_starrail = True

    @discord.ui.button(label="要tag", style=discord.ButtonStyle.blurple)
    async def button1_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.is_mention = True
        self.stop()

    @discord.ui.button(label="不用tag", style=discord.ButtonStyle.blurple)
    async def button2_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.is_mention = False
        self.stop()


class BaseNotesThresholdModal(discord.ui.Modal):
    def _int_to_str(self, value: int | None) -> str | None:
        return str(value) if isinstance(value, int) else None

    def _str_to_int(self, value: str) -> int | None:
        return int(value) if len(value) > 0 else None

    @overload
    def _to_msg(self, title: str, value: int | None) -> str:
        ...

    @overload
    def _to_msg(self, title: str, value: datetime | None) -> str:
        ...

    def _to_msg(self, title: str, value: int | datetime | None) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return f"． {title}：每天 {value.strftime('%H:%M')} 檢查\n"
        if value == 0:
            return f"． {title}：當完成時提醒\n"
        else:
            return f"． {title}：完成前 {value} 小時提醒\n"


class GenshinNotesThresholdModal(BaseNotesThresholdModal, title="設定原神即時便箋提醒"):
    """設定原神檢查即時便箋各項閾值的表單"""

    resin: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="原粹樹脂：設定樹脂額滿之前幾小時發送提醒 (不填表示不提醒)",
        placeholder="請輸入一個介於 0 ~ 5 的整數",
        required=False,
        max_length=1,
    )
    realm_currency: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="洞天寶錢：設定寶錢額滿之前幾小時發送提醒 (不填表示不提醒)",
        placeholder="請輸入一個介於 0 ~ 8 的整數",
        required=False,
        max_length=1,
    )
    transformer: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="質變儀：設定質變儀完成之前幾小時發送提醒 (不填表示不提醒)",
        placeholder="請輸入一個介於 0 ~ 5 的整數",
        required=False,
        max_length=1,
    )
    expedition: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="探索派遣：設定全部派遣完成之前幾小時發送提醒 (不填表示不提醒)",
        placeholder="請輸入一個介於 0 ~ 5 的整數",
        required=False,
        max_length=1,
    )
    commission: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="每日委託：設定每天幾點提醒今天的委託任務還未完成 (不填表示不提醒)",
        placeholder="請輸入一個介於 0000~2359 的數，例如 0200、2135",
        required=False,
        max_length=4,
        min_length=4,
    )

    def __init__(self, user_setting: GenshinScheduleNotes | None = None) -> None:
        """設定表單預設值；若使用者在資料庫已有設定值，則帶入表單預設值"""
        self.resin.default = "1"
        self.realm_currency.default = None
        self.transformer.default = None
        self.expedition.default = None
        self.commission.default = None

        if user_setting:
            self.resin.default = self._int_to_str(user_setting.threshold_resin)
            self.realm_currency.default = self._int_to_str(user_setting.threshold_currency)
            self.transformer.default = self._int_to_str(user_setting.threshold_transformer)
            self.expedition.default = self._int_to_str(user_setting.threshold_expedition)
            self.commission.default = (
                user_setting.check_commission_time.strftime("%H%M")
                if user_setting.check_commission_time
                else None
            )
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            resin = self._str_to_int(self.resin.value)
            realm_currency = self._str_to_int(self.realm_currency.value)
            transformer = self._str_to_int(self.transformer.value)
            expedition = self._str_to_int(self.expedition.value)
            commission = self._str_to_int(self.commission.value)

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
            await Database.insert_or_replace(
                GenshinScheduleNotes(
                    discord_id=interaction.user.id,
                    discord_channel_id=interaction.channel_id or 0,
                    threshold_resin=resin,
                    threshold_currency=realm_currency,
                    threshold_transformer=transformer,
                    threshold_expedition=expedition,
                    check_commission_time=commission_time,
                )
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(
                    f"原神設定完成，當達到以下設定值時會發送提醒訊息：\n"
                    f"{self._to_msg('原粹樹脂', resin)}"
                    f"{self._to_msg('洞天寶錢', realm_currency)}"
                    f"{self._to_msg('質變儀　', transformer)}"
                    f"{self._to_msg('探索派遣', expedition)}"
                    f"{self._to_msg('每日委託', commission_time)}"
                )
            )


class StarrailCheckNotesThresholdModal(BaseNotesThresholdModal, title="設定星穹鐵道即時便箋提醒"):
    """設定星穹鐵道檢查即時便箋各項閾值的表單"""

    power: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="開拓力：設定開拓力額滿之前幾小時發送提醒 (不填表示不提醒)",
        placeholder="請輸入一個介於 0 ~ 5 的整數",
        required=False,
        max_length=1,
    )
    expedition: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="委託：設定全部委託完成之前幾小時發送提醒 (不填表示不提醒)",
        placeholder="請輸入一個介於 0 ~ 5 的整數",
        required=False,
        max_length=1,
    )

    def __init__(self, user_setting: StarrailScheduleNotes | None = None):
        """設定表單預設值；若使用者在資料庫已有設定值，則帶入表單預設值"""
        self.power.default = "1"
        self.expedition.default = None

        if user_setting:
            self.power.default = self._int_to_str(user_setting.threshold_power)
            self.expedition.default = self._int_to_str(user_setting.threshold_expedition)
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            power = self._str_to_int(self.power.value)
            expedition = self._str_to_int(self.expedition.value)

            # 檢查數字範圍
            if power is None and expedition is None:
                raise ValueError()
            if (isinstance(power, int) and not (0 <= power <= 5)) or (
                isinstance(expedition, int) and not (0 <= expedition <= 5)
            ):
                raise ValueError()
        except Exception:
            await interaction.response.send_message(
                embed=EmbedTemplate.error("輸入數值有誤，請確認輸入的數值為整數且在規定範圍內"),
                ephemeral=True,
            )
        else:
            # 儲存設定資料
            await Database.insert_or_replace(
                StarrailScheduleNotes(
                    discord_id=interaction.user.id,
                    discord_channel_id=interaction.channel_id or 0,
                    threshold_power=power,
                    threshold_expedition=expedition,
                )
            )
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(
                    f"星穹鐵道設定完成，當達到以下設定值時會發送提醒訊息：\n"
                    f"{self._to_msg('開拓力　', power)}"
                    f"{self._to_msg('委託執行', expedition)}"
                )
            )
