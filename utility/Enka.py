import aiohttp
import discord
from typing import Any, Dict, List, Union, Optional
from utility.emoji import emoji
from data.game.characters import characters_map
from data.game.weapons import weapons_map
from data.game.artifacts import artifcats_map
from data.game.fight_prop import fight_prop_map, get_prop_name

class ShowcaseNotPublic(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)

class Showcase:
    data: Dict[str, Any] = None
    uid: int = 0
    url: str = ''

    def __init__(self) -> None:
        pass

    async def getEnkaData(self, uid: int) -> None:
        """從API取得指定UID玩家的角色展示櫃資料"""
        self.uid = uid
        self.url = f'https://enka.shinshin.moe/u/{uid}'
        async with aiohttp.request('GET', self.url + '/__data.json') as resp:
            if resp.status == 200:
                self.data = await resp.json()
                if 'avatarInfoList' not in self.data:
                    raise ShowcaseNotPublic("遊戲內角色展示櫃不公開")
            elif resp.status == 500:
                raise Exception("此UID玩家資料不存在")
            else:
                raise Exception("API資料取得失敗")

    def getPlayerOverviewEmbed(self) -> discord.Embed:
        """取得玩家基本資料的嵌入訊息"""
        player: Dict[str, Any] = self.data['playerInfo']
        embed = discord.Embed(
            title=player.get('nickname', str(self.uid)),
            description=
                f"「{player.get('signature', '')}」\n"
                f"冒險等階：{player.get('level', 1)}\n"
                f"世界等級：{player.get('worldLevel', 0)}\n"
                f"成就總數：{player.get('finishAchievementNum', 0)}\n"
                f"深境螺旋：{player.get('towerFloorIndex', 0)}-{player.get('towerLevelIndex', 0)}"
        )
        if 'profilePicture' in player and 'avatarId' in player['profilePicture']:
            icon = characters_map[str(player['profilePicture']['avatarId'])]['icon']
            embed.set_thumbnail(url=icon)
        embed.set_footer(text=f'UID: {self.uid}')
        return embed

    def getCharacterStatEmbed(self, index: int) -> discord.Embed:
        """取得角色面板的嵌入訊息"""
        avatarInfo: Dict[str, Any] = self.data['avatarInfoList'][index]
        id = str(avatarInfo['avatarId'])
        embed = self.__getDefaultEmbed(id)
        embed.title += ' 角色面板'

        # 天賦等級[A, E, Q]
        skill_level = [0, 0, 0]
        for i in range(3):
            if 'skillOrder' in characters_map[id]:
                skillId = characters_map[id]['skillOrder'][i]
            else:
                skillId = list(avatarInfo['skillLevelMap'])[i]
            skill_level[i] = avatarInfo['skillLevelMap'][str(skillId)]
        # 基本資料
        embed.add_field(
            name=f"角色資料",
            value=f"命座：{0 if 'talentIdList' not in avatarInfo else len(avatarInfo['talentIdList'])}\n"
                  f"等級：Lv. {avatarInfo['propMap']['4001']['val']}\n"
                  f"天賦：{skill_level[0]}/{skill_level[1]}/{skill_level[2]}\n"
                  f"好感：Lv. {avatarInfo['fetterInfo']['expLevel']}",
        )
        # 武器
        equipList: List[Dict[str, Any]] = avatarInfo['equipList']
        if 'weapon' in equipList[-1]:
            weapon = equipList[-1]
            weaponStats = weapon['flat']['weaponStats']
            refinement = 1
            if 'affixMap' in weapon['weapon']:
                refinement += list(weapon['weapon']['affixMap'].values())[0]
            embed.add_field(
                name=f"★{weapon['flat']['rankLevel']} {weapons_map[weapon['itemId']]['name']}",
                value=f"精煉：{refinement} 階\n"
                      f"等級：Lv. {weapon['weapon']['level']}\n"
                      f"{emoji.fightprop.get('FIGHT_PROP_ATTACK', '')}基礎攻擊力 +{weaponStats[0]['statValue']}\n"
                      f"{self.__getStatPropSentence(weaponStats[1]['appendPropId'], weaponStats[1]['statValue'])}"
            )
        # 人物面板
        prop: Dict[str, float] = avatarInfo['fightPropMap']
        substat: str = '\n'.join([self.__getCharacterFightPropSentence(int(id), prop[id]) for
            id in ['20', '22', '28', '26', '23', '30', '40', '41', '42', '43', '44', '45', '46'] if prop[id] > 0])
        embed.add_field(
            name='屬性面板',
            value=f"{emoji.fightprop.get('FIGHT_PROP_HP','')}生命值：{round(prop['2000'])} ({round(prop['1'])} +{round(prop['2000'])-round(prop['1'])})\n"
                  f"{emoji.fightprop.get('FIGHT_PROP_ATTACK','')}攻擊力：{round(prop['2001'])} ({round(prop['4'])} +{round(prop['2001'])-round(prop['4'])})\n"
                  f"{emoji.fightprop.get('FIGHT_PROP_DEFENSE','')}防禦力：{round(prop['2002'])} ({round(prop['7'])} +{round(prop['2002'])-round(prop['7'])})\n"
                  f"{substat}",
            inline=False
        )
        return embed
    
    def getArtifactStatEmbed(self, index: int) -> discord.Embed:
        """取得角色聖遺物的嵌入訊息"""
        avatarInfo: Dict[str, Any] = self.data['avatarInfoList'][index]
        id = str(avatarInfo['avatarId'])
        embed = self.__getDefaultEmbed(id)
        embed.title += ' 聖遺物'

        pos_name_map = {1: '花', 2: '羽', 3: '沙', 4: '杯', 5: '冠'}
        substat_sum: Dict[str, float] = dict() # 副詞條數量統計
        
        equip: Dict[str, Any]
        for equip in avatarInfo['equipList']:
            if 'reliquary' not in equip:
                continue
            artifact_id: int = equip['itemId'] // 10
            flat = equip['flat']
            pos_name = pos_name_map[artifcats_map[artifact_id]['pos']]
            # 主詞條屬性
            embed_value = f"__**{self.__getStatPropSentence(flat['reliquaryMainstat']['mainPropId'], flat['reliquaryMainstat']['statValue'])}**__\n"
            # 副詞條屬性
            for substat in flat['reliquarySubstats']:
                prop: str = substat['appendPropId']
                value: Union[int, float] = substat['statValue']
                embed_value += f"{self.__getStatPropSentence(prop, value)}\n"
                substat_sum[prop] = substat_sum.get(prop, 0) + value
            
            embed.add_field(name=f"{pos_name}：{artifcats_map[artifact_id]['name']}", value=embed_value)

        # 副詞條數量統計
        def substatSummary(prop: str, name: str, base: float) -> str:
            return f"{emoji.fightprop.get(prop, '')}{name}：{round(value / base, 1)}\n" if (value := substat_sum.get(prop)) != None else ''
        
        embed_value = ''
        embed_value += substatSummary('FIGHT_PROP_ATTACK_PERCENT', '攻擊力％', 5.0)
        embed_value += substatSummary('FIGHT_PROP_HP_PERCENT', '生命值％', 5.0)
        embed_value += substatSummary('FIGHT_PROP_DEFENSE_PERCENT', '防禦力％', 6.2)
        embed_value += substatSummary('FIGHT_PROP_CHARGE_EFFICIENCY', '元素充能', 5.5)
        embed_value += substatSummary('FIGHT_PROP_ELEMENT_MASTERY', '元素精通', 20)
        embed_value += substatSummary('FIGHT_PROP_CRITICAL', '暴擊率　', 3.3)
        embed_value += substatSummary('FIGHT_PROP_CRITICAL_HURT', '暴擊傷害', 6.6)
        if embed_value != '':
            embed.add_field(name='副詞條數量統計', value=embed_value)
        
        return embed

    def __getDefaultEmbed(self, character_id: str) -> discord.Embed:
        id = character_id
        color = {'pyro': 0xfb4120, 'electro': 0xbf73e7, 'hydro': 0x15b1ff, 'cryo': 0x70daf1, 'dendro': 0xa0ca22, 'anemo': 0x5cd4ac, 'geo': 0xfab632}
        embed = discord.Embed(
            title=f"★{characters_map[id]['rarity']} {characters_map[id]['name']}",
            color=color.get(characters_map[id]['element'].lower())
        )
        embed.set_thumbnail(url=characters_map[id]['icon'])
        embed.set_author(name=f"{self.data['playerInfo']['nickname']} 的角色展示櫃", url=self.url)
        embed.set_footer(text=f"{self.data['playerInfo']['nickname']}．Lv. {self.data['playerInfo']['level']}．UID: {self.uid}")

        return embed

    def __getCharacterFightPropSentence(self, prop: int, value: Union[int, float]) -> str:
        emoji_str = emoji.fightprop.get(fight_prop_map.get(prop), '')
        prop_name = get_prop_name(prop)
        if '%' in prop_name:
            return emoji_str + prop_name.replace('%', f'：{round(value * 100, 1)}%')
        return emoji_str + prop_name + f'：{round(value)}'

    def __getStatPropSentence(self, prop: str, value: Union[int, float]) -> str:
        emoji_str = emoji.fightprop.get(prop, '')
        prop_name = get_prop_name(prop)
        if '%' in prop_name:
            return emoji_str + prop_name.replace('%', f'+{value}%')
        return emoji_str + prop_name + f'+{value}'


class ShowcaseCharactersDropdown(discord.ui.Select):
    """展示櫃角色下拉選單"""
    showcase: Showcase
    
    def __init__(self, showcase: Showcase) -> None:
        self.showcase = showcase
        avatarInfoList: List[Dict[str, Any]] = showcase.data["avatarInfoList"]
        options = []
        for i, avatarInfo in enumerate(avatarInfoList):
            id = str(avatarInfo['avatarId'])
            level: str = avatarInfo['propMap']['4001']['val']
            rarity: int = characters_map[id]['rarity']
            element: str = characters_map[id]['element']
            name: str = characters_map[id]['name']
            options.append(discord.SelectOption(
                label=f'★{rarity} Lv.{level} {name}',
                value=str(i),
                emoji=emoji.elements.get(element.lower())
            ))
        super().__init__(placeholder=f'選擇展示櫃角色：', options=options)
    
    async def callback(self, interaction: discord.Interaction) -> None:
        character_index = int(self.values[0])
        embed = self.showcase.getCharacterStatEmbed(character_index)
        view = ShowcaseView(self.showcase, character_index)
        await interaction.response.edit_message(embed=embed, view=view)

class CharacterStatButton(discord.ui.Button):
    """角色面板按鈕"""
    showcase: Showcase
    character_index: int

    def __init__(self, showcase: Showcase, character_index: int):
        super().__init__(style=discord.ButtonStyle.green, label='角色面板')
        self.showcase = showcase
        self.character_index = character_index
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        embed = self.showcase.getCharacterStatEmbed(self.character_index)
        await interaction.response.edit_message(embed=embed)

class CharacterArtifactButton(discord.ui.Button):
    """角色聖遺物按鈕"""
    showcase: Showcase
    character_index: int
    def __init__(self, showcase: Showcase, character_index: int):
        super().__init__(style=discord.ButtonStyle.primary, label='聖遺物資料')
        self.showcase = showcase
        self.character_index = character_index
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        embed = self.showcase.getArtifactStatEmbed(self.character_index)
        await interaction.response.edit_message(embed=embed)

class ShowcaseView(discord.ui.View):
    """角色展示櫃View，顯示角色面板、聖遺物按鈕，以及角色下拉選單"""
    def __init__(self, showcase: Showcase, character_index: Optional[int] = None):
        super().__init__(timeout=600)
        if character_index != None:
            self.add_item(CharacterStatButton(showcase, character_index))
            self.add_item(CharacterArtifactButton(showcase ,character_index))
        self.add_item(ShowcaseCharactersDropdown(showcase))
