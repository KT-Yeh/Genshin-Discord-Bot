import asyncio
from typing import Literal, Optional, Sequence, Union

import discord
import genshin

import genshin_py
from database import Database, GenshinSpiralAbyss
from utility import EmbedTemplate, config


class AbyssRecordDropdown(discord.ui.Select):
    """選擇深淵歷史紀錄的下拉選單"""

    def __init__(
        self,
        user: Union[discord.User, discord.Member],
        abyss_data_list: Sequence[GenshinSpiralAbyss],
    ):
        def honor(abyss: genshin.models.SpiralAbyss) -> str:
            """判斷一些特殊紀錄，例如12通、單通、雙通"""
            if abyss.total_stars == 36:
                if abyss.total_battles == 12:
                    return "(👑)"
                last_battles = abyss.floors[-1].chambers[-1].battles
                num_of_characters = max(
                    len(last_battles[0].characters), len(last_battles[1].characters)
                )
                if num_of_characters == 2:
                    return "(雙通)"
                if num_of_characters == 1:
                    return "(單通)"
            return ""

        options = [
            discord.SelectOption(
                label=f"[第 {abyss.season} 期] ★ {abyss.abyss.total_stars} {honor(abyss.abyss)}",
                description=(
                    f"{abyss.abyss.start_time.astimezone().strftime('%Y.%m.%d')} ~ "
                    f"{abyss.abyss.end_time.astimezone().strftime('%Y.%m.%d')}"
                ),
                value=str(i),
            )
            for i, abyss in enumerate(abyss_data_list)
        ]
        super().__init__(placeholder="選擇期數：", options=options)
        self.user = user
        self.abyss_data_list = abyss_data_list

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        index = int(self.values[0])
        await SpiralAbyssUI.presentation(
            interaction, self.user, self.abyss_data_list[index], view_item=self
        )


class AbyssFloorDropdown(discord.ui.Select):
    """選擇深淵樓層的下拉選單"""

    def __init__(
        self,
        overview: discord.Embed,
        abyss_data: GenshinSpiralAbyss,
        save_or_remove: Literal["SAVE", "REMOVE"],
    ):
        # 第一個選項依據參數顯示為保存或是刪除紀錄
        _description = "保存此次紀錄到資料庫，之後可從歷史紀錄查看" if save_or_remove == "SAVE" else "從資料庫中刪除本次深淵紀錄"
        option = [
            discord.SelectOption(
                label=f"{'📁 儲存本次紀錄' if save_or_remove == 'SAVE' else '❌ 刪除本次紀錄'}",
                description=_description,
                value=save_or_remove,
            )
        ]
        options = option + [
            discord.SelectOption(
                label=f"[★{floor.stars}] 第 {floor.floor} 層",
                description=genshin_py.parse_genshin_abyss_chamber(floor.chambers[-1]),
                value=str(i),
            )
            for i, floor in enumerate(abyss_data.abyss.floors)
        ]
        super().__init__(placeholder="選擇樓層：", options=options)
        self.embed = overview
        self.abyss_data = abyss_data
        self.save_or_remove = save_or_remove

    async def callback(self, interaction: discord.Interaction):
        # 儲存或刪除深淵資料
        if self.values[0] == self.save_or_remove:
            # 檢查互動者是否為深淵資料本人
            if interaction.user.id == self.abyss_data.discord_id:
                if self.save_or_remove == "SAVE":
                    await Database.insert_or_replace(self.abyss_data)
                    await interaction.response.send_message(
                        embed=EmbedTemplate.normal("已儲存本次深淵紀錄"), ephemeral=True
                    )
                else:  # self.save_or_remove == 'REMOVE'
                    await Database.delete_instance(self.abyss_data)
                    await interaction.response.send_message(
                        embed=EmbedTemplate.normal("已刪除本次深淵紀錄"), ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("僅限本人才能操作"), ephemeral=True
                )
        else:  # 繪製樓層圖片
            await interaction.response.defer()
            fp = await genshin_py.draw_abyss_card(
                self.abyss_data.abyss.floors[int(self.values[0])],
                self.abyss_data.characters,
            )
            fp.seek(0)
            self.embed.set_image(url="attachment://image.jpeg")
            await interaction.edit_original_response(
                embed=self.embed, attachments=[discord.File(fp, "image.jpeg")]
            )


class SpiralAbyssUI:
    """深境螺旋"""

    @staticmethod
    async def presentation(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member],
        abyss_data: GenshinSpiralAbyss,
        *,
        view_item: Optional[discord.ui.Item] = None,
    ):
        embed = genshin_py.parse_genshin_abyss_overview(abyss_data.abyss)
        embed.title = f"{user.display_name} 的深境螺旋戰績"
        embed.set_thumbnail(url=user.display_avatar.url)
        view = None
        if len(abyss_data.abyss.floors) > 0:
            view = discord.ui.View(timeout=config.discord_view_short_timeout)
            if view_item:  # 從歷史紀錄取得資料，所以第一個選項是刪除紀錄
                view.add_item(AbyssFloorDropdown(embed, abyss_data, "REMOVE"))
                view.add_item(view_item)
            else:  # 從Hoyolab取得資料，所以第一個選項是保存紀錄
                view.add_item(AbyssFloorDropdown(embed, abyss_data, "SAVE"))
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])

    @staticmethod
    async def abyss(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member],
        season_choice: Literal["THIS_SEASON", "PREVIOUS_SEASON", "HISTORICAL_RECORD"],
    ):
        if season_choice == "HISTORICAL_RECORD":  # 查詢歷史紀錄
            abyss_data_list = await Database.select_all(
                GenshinSpiralAbyss,
                GenshinSpiralAbyss.discord_id.is_(user.id),
            )
            if len(abyss_data_list) == 0:
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("此使用者沒有保存任何歷史紀錄")
                )
            else:
                abyss_data_list = sorted(abyss_data_list, key=lambda x: x.season, reverse=True)
                view = discord.ui.View(timeout=config.discord_view_short_timeout)
                # 一次最多顯示 25 筆資料，所以要分批顯示
                for i in range(0, len(abyss_data_list), 25):
                    view.add_item(AbyssRecordDropdown(user, abyss_data_list[i : i + 25]))
                await interaction.response.send_message(view=view)
        else:  # 查詢 Hoyolab 紀錄 (THIS_SEASON、PREVIOUS_SEASON)
            try:
                defer, abyss_data = await asyncio.gather(
                    interaction.response.defer(),
                    genshin_py.get_genshin_spiral_abyss(
                        user.id, (season_choice == "PREVIOUS_SEASON")
                    ),
                )
            except Exception as e:
                await interaction.edit_original_response(embed=EmbedTemplate.error(e))
            else:
                await SpiralAbyssUI.presentation(interaction, user, abyss_data)
