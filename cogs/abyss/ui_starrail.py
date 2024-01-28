import enum
import typing

import discord

import genshin_py
from database import Database, StarrailForgottenHall, StarrailPureFiction, User
from utility import EmbedTemplate, config


class AbyssMode(str, enum.Enum):
    """星穹鐵道深淵模式"""

    FORGOTTEN_HALL = "forgotten_hall"
    """忘卻之庭"""
    PURE_FICTION = "pure_fiction"
    """虛構敘事"""


# Make a discord button to choose which mode
class ChooseAbyssModeButton(discord.ui.View):
    """選擇星穹鐵道深淵模式的按鈕"""

    def __init__(self):
        super().__init__(timeout=config.discord_view_short_timeout)
        self.value = None

    @discord.ui.button(label="忘卻之庭", style=discord.ButtonStyle.blurple)
    async def forgotten_hall(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = AbyssMode.FORGOTTEN_HALL
        self.stop()

    @discord.ui.button(label="虛構敘事", style=discord.ButtonStyle.blurple)
    async def pure_fiction(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = AbyssMode.PURE_FICTION
        self.stop()


class HallRecordDropdown(discord.ui.Select):
    """選擇忘卻之庭、虛構敘事歷史紀錄的下拉選單"""

    def __init__(
        self,
        user: discord.User | discord.Member,
        nickname: str,
        uid: int,
        hall_data_list: typing.Sequence[StarrailForgottenHall]
        | typing.Sequence[StarrailPureFiction],
    ):
        sorted_hall_data_list = sorted(
            hall_data_list, key=lambda x: x.data.begin_time.datetime, reverse=True
        )
        options = [
            discord.SelectOption(
                label=f"[{hall.data.begin_time.datetime.strftime('%Y.%m.%d')} ~ "
                f"{hall.data.end_time.datetime.strftime('%Y.%m.%d')}] ★ {hall.data.total_stars}",
                value=str(i),
            )
            for i, hall in enumerate(sorted_hall_data_list)
        ]
        super().__init__(placeholder="選擇期數：", options=options)
        self.user = user
        self.nickname = nickname
        self.uid = uid
        self.hall_data_list = sorted_hall_data_list

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        index = int(self.values[0])
        await ForgottenHallUI.present(
            interaction,
            self.user,
            self.nickname,
            self.uid,
            self.hall_data_list[index],
            view_item=self,
        )


class HallFloorDropdown(discord.ui.Select):
    """選擇忘卻之庭、虛構敘事樓層的下拉選單"""

    def __init__(
        self,
        overview: discord.Embed,
        avatar: bytes,
        nickname: str,
        uid: int,
        hall_data: StarrailForgottenHall | StarrailPureFiction,
        save_or_remove: typing.Literal["SAVE", "REMOVE"],
    ):
        # 第一個選項依據參數顯示為保存或是刪除紀錄
        _descr = "保存此次紀錄到資料庫，之後可從歷史紀錄查看" if save_or_remove == "SAVE" else "從資料庫中刪除本次忘卻之庭紀錄"
        options = [
            discord.SelectOption(
                label=f"{'📁 儲存本次紀錄' if save_or_remove == 'SAVE' else '❌ 刪除本次紀錄'}",
                description=_descr,
                value=save_or_remove,
            )
        ]
        options += [
            discord.SelectOption(
                label=f"[★{floor.star_num}] {floor.name}",
                value=str(i),
            )
            for i, floor in enumerate(hall_data.data.floors)
        ]

        super().__init__(
            placeholder="選擇樓層（可多選）：",
            options=options,
            max_values=(min(3, len(hall_data.data.floors))),
        )
        self.embed = overview
        self.avatar = avatar
        self.nickname = nickname
        self.uid = uid
        self.hall_data = hall_data
        self.save_or_remove = save_or_remove

    async def callback(self, interaction: discord.Interaction):
        # 儲存或刪除忘卻之庭資料
        if self.save_or_remove in self.values:
            # 檢查互動者是否為忘卻之庭資料本人
            if interaction.user.id == self.hall_data.discord_id:
                if self.save_or_remove == "SAVE":
                    await Database.insert_or_replace(self.hall_data)
                    await interaction.response.send_message(
                        embed=EmbedTemplate.normal("已儲存本次挑戰紀錄"), ephemeral=True
                    )
                else:  # self.save_or_remove == 'REMOVE'
                    await Database.delete_instance(self.hall_data)
                    await interaction.response.send_message(
                        embed=EmbedTemplate.normal("已刪除本次挑戰紀錄"), ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("僅限本人才能操作"), ephemeral=True
                )
        else:  # 繪製樓層圖片
            await interaction.response.defer()
            values = sorted(self.values, key=lambda x: int(x))
            floors = [self.hall_data.data.floors[int(value)] for value in values]
            fp = await genshin_py.draw_starrail_forgottenhall_card(
                self.avatar, self.nickname, self.uid, self.hall_data.data, floors
            )
            fp.seek(0)
            self.embed.set_image(url="attachment://image.jpeg")
            await interaction.edit_original_response(
                embed=self.embed, attachments=[discord.File(fp, "image.jpeg")]
            )


class ForgottenHallUI:
    @staticmethod
    async def present(
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
        nickname: str,
        uid: int,
        hall_data: StarrailForgottenHall | StarrailPureFiction,
        *,
        view_item: discord.ui.Item | None = None,
    ):
        if isinstance(hall_data, StarrailForgottenHall):
            title = "忘卻之庭"
        else:  # isinstance(hall_data, StarrailPureFiction)
            title = "虛構敘事"
        hall = hall_data.data
        embed = genshin_py.parse_starrail_hall_overview(hall)
        embed.title = f"{user.display_name} 的{title}戰績"
        embed.set_thumbnail(url=user.display_avatar.url)
        view = None
        if len(hall.floors) > 0:
            view = discord.ui.View(timeout=config.discord_view_short_timeout)
            avatar = await user.display_avatar.read()
            if view_item:  # 從歷史紀錄取得資料，所以第一個選項是刪除紀錄
                view.add_item(HallFloorDropdown(embed, avatar, nickname, uid, hall_data, "REMOVE"))
                view.add_item(view_item)
            else:  # 從Hoyolab取得資料，所以第一個選項是保存紀錄
                view.add_item(HallFloorDropdown(embed, avatar, nickname, uid, hall_data, "SAVE"))
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])

    @staticmethod
    async def launch(
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
        mode: AbyssMode,
        season_choice: typing.Literal["THIS_SEASON", "PREVIOUS_SEASON", "HISTORICAL_RECORD"],
    ):
        try:
            userstats = await genshin_py.get_starrail_userstats(user.id)
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e), view=None)
            return

        nickname = userstats.info.nickname
        _u = await Database.select_one(User, User.discord_id == user.id)
        uid = _u.uid_starrail if _u else 0
        uid = uid or 0

        if season_choice == "HISTORICAL_RECORD":  # 查詢歷史紀錄
            if mode == AbyssMode.FORGOTTEN_HALL:
                hall_data_list = await Database.select_all(
                    StarrailForgottenHall,
                    StarrailForgottenHall.discord_id.is_(user.id),
                )
            else:  # mode == AbyssMode.PURE_FICTION
                hall_data_list = await Database.select_all(
                    StarrailPureFiction,
                    StarrailPureFiction.discord_id.is_(user.id),
                )
            if len(hall_data_list) == 0:
                await interaction.edit_original_response(
                    embed=EmbedTemplate.normal("此使用者沒有保存任何歷史紀錄"),
                    view=None,
                )
            else:
                view = discord.ui.View(timeout=config.discord_view_short_timeout)
                view.add_item(HallRecordDropdown(user, nickname, uid, hall_data_list))
                await interaction.edit_original_response(view=view)
        else:  # 查詢 Hoyolab 紀錄 (THIS_SEASON、PREVIOUS_SEASON)
            try:
                if mode == AbyssMode.FORGOTTEN_HALL:
                    hall = await genshin_py.get_starrail_forgottenhall(
                        user.id, (season_choice == "PREVIOUS_SEASON")
                    )
                    hall_data = StarrailForgottenHall(user.id, hall.season, hall)
                else:  # mode == AbyssMode.PURE_FICTION
                    hall = await genshin_py.get_starrail_pure_fiction(
                        user.id, (season_choice == "PREVIOUS_SEASON")
                    )
                    hall_data = StarrailPureFiction(user.id, hall.season_id, hall)
            except Exception as e:
                await interaction.edit_original_response(embed=EmbedTemplate.error(e), view=None)
            else:
                await ForgottenHallUI.present(interaction, user, nickname, uid, hall_data)
