import asyncio
import json
import discord
import genshin
import sentry_sdk
from datetime import datetime
from typing import Sequence, Union, Tuple
from .emoji import emoji
from .utils import log, getCharacterName, trimCookie, getServerName, getDayOfWeek,user_last_use_time
from .config import config

class UserDataNotFound(Exception):
    pass

def generalErrorHandler(func):
    """對於使用genshin.py函式的通用例外處理裝飾器"""
    async def wrapper(*args, **kwargs):
        user_id = args[1] if (len(args) >= 2 and isinstance(args[1], str) and len(args[1]) >= 17) else ''
        try:
            return await func(*args, **kwargs)
        except genshin.errors.DataNotPublic as e:
            log.info(f"[例外][{user_id}]{func.__name__}: [retcode]{e.retcode} [原始內容]{e.original} [錯誤訊息]{e.msg}")
            raise Exception('此功能權限未開啟，請先從Hoyolab網頁或App上的個人戰績->設定，將此功能啟用')
        except genshin.errors.InvalidCookies as e:
            log.info(f"[例外][{user_id}]{func.__name__}: [retcode]{e.retcode} [原始內容]{e.original} [錯誤訊息]{e.msg}")
            raise Exception('Cookie已失效，請從Hoyolab重新取得新Cookie')
        except genshin.errors.RedemptionException as e:
            log.info(f"[例外][{user_id}]{func.__name__}: [retcode]{e.retcode} [原始內容]{e.original} [錯誤訊息]{e.msg}")
            raise Exception(e.original)
        except genshin.errors.GenshinException as e:
            log.warning(f"[例外][{user_id}]{func.__name__}: [retcode]{e.retcode} [原始內容]{e.original} [錯誤訊息]{e.msg}")
            sentry_sdk.capture_exception(e)
            raise Exception(e.original)
        except UserDataNotFound as e:
            log.info(f"[例外][{user_id}]{func.__name__}: [錯誤訊息]{e}")
            raise Exception(str(e))
        except Exception as e:
            log.warning(f"[例外][{user_id}]{func.__name__}: [錯誤訊息]{e}")
            sentry_sdk.capture_exception(e)
            raise Exception(str(e))
    return wrapper

class GenshinApp:
    def __init__(self) -> None:
        try:
            with open('data/user_data.json', 'r', encoding="utf-8") as f:
                self.__user_data: dict[str, dict[str, str]] = json.load(f)
        except:
            self.__user_data: dict[str, dict[str, str]] = { }

    @generalErrorHandler
    async def setCookie(self, user_id: str, cookie: str) -> str:
        """設定使用者Cookie
        
        ------
        Parameters
        user_id `str`: 使用者Discord ID
        cookie `str`: Hoyolab cookie
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        log.info(f'[指令][{user_id}]setCookie: cookie={cookie}')
        user_id = str(user_id)
        cookie = trimCookie(cookie)
        if cookie == None:
            return f'無效的Cookie，請重新輸入(輸入 `/cookie設定` 顯示說明)'
        client = genshin.Client(lang='zh-tw')
        client.set_cookies(cookie)
        accounts = await client.genshin_accounts()
        if len(accounts) == 0:
            log.info(f'[資訊][{user_id}]setCookie: 帳號內沒有任何角色')
            result = '帳號內沒有任何角色，取消設定Cookie'
        else:
            self.__user_data[user_id] = {}
            self.__user_data[user_id]['cookie'] = cookie
            log.info(f'[資訊][{user_id}]setCookie: Cookie設置成功')
            
            if len(accounts) == 1 and len(str(accounts[0].uid)) == 9:
                self.setUID(user_id, str(accounts[0].uid))
                result = f'Cookie已設定完成，角色UID: {accounts[0].uid} 已保存！'
            else:
                result = f'Cookie已保存，你的Hoyolab帳號內共有{len(accounts)}名角色\n請使用指令 `/uid設定` 指定要保存的原神角色'
                self.__saveUserData()
        return result

    @generalErrorHandler
    async def getGameAccounts(self, user_id: str) -> Sequence[genshin.models.GenshinAccount]:
        """取得同一個Hoyolab帳號下，各伺服器的原神帳號

        ------
        Parameters
        user_id `str`: 使用者Discord ID
        ------
        Returns
        Sequence[genshin.models.GenshinAccount]`: 查詢結果
        """
        check, msg = self.checkUserData(user_id, checkUID=False)
        if check == False:
            raise UserDataNotFound(msg)
        client = self.__getGenshinClient(user_id)
        return await client.genshin_accounts()
    
    def setUID(self, user_id: str, uid: str) -> str:
        """保存指定的UID

        ------
        Parameters
        user_id `str`: 使用者Discord ID
        uid `str`: 欲保存的原神UID
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        log.info(f'[指令][{user_id}]setUID: uid={uid}')
        self.__user_data[user_id]['uid'] = uid
        self.__saveUserData()
        return f'角色UID: {uid} 已設定完成'
    
    def getUID(self, user_id: str) -> Union[int, None]:
        if user_id in self.__user_data.keys():
            user_last_use_time.update(user_id)
            return int(self.__user_data[user_id].get('uid'))
        return None

    @generalErrorHandler
    async def getRealtimeNote(self, user_id: str, *, schedule = False) -> Union[None, discord.Embed]:
        """取得使用者即時便箋(樹脂、洞天寶錢、參數質變儀、派遣、每日、週本)
        
        ------
        Parameters
        user_id `str`: 使用者Discord ID
        schedule `bool`: 是否為排程檢查樹脂，設為`True`時，只有當樹脂超過設定標準時才會回傳即時便箋結果
        ------
        Returns
        `None | Embed`: 自動檢查樹脂時，未溢出的情況下回傳`None`；正常情況回傳查詢結果`discord.Embed`
        """
        if not schedule:
            log.info(f'[指令][{user_id}]getRealtimeNote')
        check, msg = self.checkUserData(user_id, update_use_time=(not schedule))
        if check == False:
            raise UserDataNotFound(msg)
        uid = self.__user_data[user_id]['uid']
        client = self.__getGenshinClient(user_id)
        notes = await client.get_genshin_notes(int(uid))
        
        if schedule == True and notes.current_resin < config.auto_check_resin_threshold:
            return None
        else:
            msg = f'{getServerName(uid[0])} {uid.replace(uid[3:-3], "***", 1)}\n'
            msg += f'--------------------\n'
            msg += self.__parseNotes(notes, shortForm=schedule)
            # 根據樹脂數量，以80作分界，embed顏色從綠色(0x28c828)漸變到黃色(0xc8c828)，再漸變到紅色(0xc82828)
            r = notes.current_resin
            color = 0x28c828 + 0x010000 * int(0xa0 * r / 80) if r < 80 else 0xc8c828 - 0x000100 * int(0xa0 * (r - 80) / 80)
            embed = discord.Embed(description=msg, color=color)
            return embed

    @generalErrorHandler
    async def redeemCode(self, user_id: str, code: str) -> str:
        """為使用者使用指定的兌換碼

        ------
        Parameters
        user_id `str`: 使用者Discord ID
        code `str`: Hoyolab兌換碼
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        log.info(f'[指令][{user_id}]redeemCode: code={code}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            raise UserDataNotFound(msg)
        client = self.__getGenshinClient(user_id)
        await client.redeem_code(code, int(self.__user_data[user_id]['uid']))
        return f'兌換碼 {code} 使用成功！'

    async def claimDailyReward(self, user_id: str, *, honkai: bool = False, schedule = False) -> str:
        """為使用者在Hoyolab簽到

        ------
        Parameters
        user_id `str`: 使用者Discord ID
        honkai `bool`: 是否也簽到崩壞3
        schedule `bool`: 是否為排程自動簽到
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        if not schedule:
            log.info(f'[指令][{user_id}]claimDailyReward: honkai={honkai}')
        check, msg = self.checkUserData(user_id, update_use_time=(not schedule))
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        
        game_name = {genshin.Game.GENSHIN: '原神', genshin.Game.HONKAI: '崩壞3'}
        async def claimReward(game: genshin.Game, retry: int = 5) -> str:
            try:
                reward = await client.claim_daily_reward(game=game)
            except genshin.errors.AlreadyClaimed:
                return f'{game_name[game]}今日獎勵已經領過了！'
            except genshin.errors.GenshinException as e:
                log.warning(f'[例外][{user_id}]claimDailyReward: {game_name[game]}[retcode]{e.retcode} [例外內容]{e.original}')
                sentry_sdk.capture_exception(e)
                if e.retcode == 0 and retry > 0:
                    await asyncio.sleep(0.5)
                    return await claimReward(game, retry - 1)
                if e.retcode == -10002 and game == genshin.Game.HONKAI:
                    return '崩壞3簽到失敗，未查詢到角色資訊，請確認艦長是否已綁定新HoYoverse通行證'
                return f'{game_name[game]}簽到失敗：[retcode]{e.retcode} [內容]{e.original}'
            except Exception as e:
                log.warning(f'[例外][{user_id}]claimDailyReward: {game_name[game]}[例外內容]{e}')
                sentry_sdk.capture_exception(e)
                return f'{game_name[game]}簽到失敗：{e}'
            else:
                return f'{game_name[game]}今日簽到成功，獲得 {reward.amount}x {reward.name}！'

        result = await claimReward(genshin.Game.GENSHIN)
        if honkai:
            result = result + ' ' + await claimReward(genshin.Game.HONKAI)
        
        # Hoyolab社群簽到
        try:
            await client.check_in_community()
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]claimDailyReward: Hoyolab[retcode]{e.retcode} [例外內容]{e.original}')
        
        return result

    @generalErrorHandler
    async def getSpiralAbyss(self, user_id: str, previous: bool = False) -> genshin.models.SpiralAbyss:
        """取得深境螺旋資訊

        ------
        Parameters
        user_id `str`: 使用者Discord ID
        previous `bool`: `True`查詢前一期的資訊、`False`查詢本期資訊
        ------
        Returns
        `SpiralAbyss`: 查詢結果
        """
        log.info(f'[指令][{user_id}]getSpiralAbyss: previous={previous}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            raise UserDataNotFound(msg)
        client = self.__getGenshinClient(user_id)
        # 為了刷新戰鬥數據榜，需要先對record card發出請求
        await client.get_record_cards()
        return await client.get_genshin_spiral_abyss(int(self.__user_data[user_id]['uid']), previous=previous)

    @generalErrorHandler
    async def getTravelerDiary(self, user_id: str, month: int) -> discord.Embed:
        """取得使用者旅行者札記

        ------
        Parameters:
        user_id `str`: 使用者Discord ID
        month `int`: 欲查詢的月份
        ------
        Returns:
        `discord.Embed`: 查詢結果，已包裝成 discord 嵌入格式
        """
        log.info(f'[指令][{user_id}]getTravelerDiary: month={month}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            raise UserDataNotFound(msg)
        client = self.__getGenshinClient(user_id)
        diary = await client.get_diary(int(self.__user_data[user_id]['uid']), month=month)
        
        d = diary.data
        result = discord.Embed(
            title=f'{diary.nickname}的旅行者札記：{month}月',
            description=f'原石收入比上個月{"增加" if d.primogems_rate > 0 else "減少"}了{abs(d.primogems_rate)}%，摩拉收入比上個月{"增加" if d.mora_rate > 0 else "減少"}了{abs(d.mora_rate)}%',
            color=0xfd96f4
        )
        result.add_field(
            name='當月共獲得', 
            value=f'{emoji.items.primogem}原石：{d.current_primogems} ({round(d.current_primogems/160)}{emoji.items.intertwined_fate})　上個月：{d.last_primogems} ({round(d.last_primogems/160)}{emoji.items.intertwined_fate})\n'
                f'{emoji.items.mora}摩拉：{format(d.current_mora, ",")}　上個月：{format(d.last_mora, ",")}',
            inline=False
        )
        # 將札記原石組成平分成兩個field
        for i in range(0, 2):
            msg = ''
            length = len(d.categories)
            for j in range(round(length/2*i), round(length/2*(i+1))):
                msg += f'{d.categories[j].name[0:2]}：{d.categories[j].percentage}%\n'
            result.add_field(name=f'原石收入組成 ({i+1})', value=msg, inline=True)

        return result

    @generalErrorHandler
    async def getRecordCard(self, user_id: str) -> Tuple[genshin.models.RecordCard, genshin.models.PartialGenshinUserStats]:
        """取得使用者記錄卡片

        ------
        Parameters:
        user_id `str`: 使用者Discord ID
        ------
        Returns:
        `(RecordCard, PartialGenshinUserStats)`: 查詢結果，包含紀錄卡片與部分原神使用者資料
        """
        log.info(f'[指令][{user_id}]getRecordCard')
        check, msg = self.checkUserData(user_id)
        if check == False:
            raise UserDataNotFound(msg)
        client = self.__getGenshinClient(user_id)
        cards = await client.get_record_cards()
        userstats = await client.get_partial_genshin_user(int(self.__user_data[user_id]['uid']))

        for card in cards:
            if card.uid == int(self.__user_data[user_id]['uid']):
                return (card, userstats)
        raise UserDataNotFound('找不到原神紀錄卡片')

    @generalErrorHandler
    async def getCharacters(self, user_id: str) -> Sequence[genshin.models.Character]:
        """取得使用者所有角色資料

        ------
        Parameters:
        user_id `str`: 使用者Discord ID
        ------
        Returns:
        `Sequence[Character]`: 查詢結果
        """
        log.info(f'[指令][{user_id}]getCharacters')
        check, msg = self.checkUserData(user_id)
        if check == False:
            raise UserDataNotFound(msg)
        client = self.__getGenshinClient(user_id)
        return await client.get_genshin_characters(int(self.__user_data[user_id]['uid']))

    def checkUserData(self, user_id: str, *, checkUID = True, update_use_time = True) -> Tuple[bool, str]:
        """檢查使用者相關資料是否已保存在資料庫內
        
        ------
        Parameters
        user_id `str`: 使用者Discord ID
        checkUID `bool`: 是否檢查UID
        update_use_time `bool`: 是否更新使用者最後使用時間
        ------
        Returns
        `bool`: `True`檢查成功，資料存在資料庫內；`False`檢查失敗，資料不存在資料庫內
        `str`: 檢查失敗時，回覆給使用者的訊息
        """
        if user_id not in self.__user_data.keys():
            log.info(f'[資訊][{user_id}]checkUserData: 找不到使用者')
            return False, f'找不到使用者，請先設定Cookie(輸入 `/cookie設定` 顯示說明)'
        else:
            if 'cookie' not in self.__user_data[user_id].keys():
                log.info(f'[資訊][{user_id}]checkUserData: 找不到Cookie')
                return False, f'找不到Cookie，請先設定Cookie(輸入 `/cookie設定` 顯示說明)'
            if checkUID and 'uid' not in self.__user_data[user_id].keys():
                log.info(f'[資訊][{user_id}]checkUserData: 找不到角色UID')
                return False, f'找不到角色UID，請先設定UID(使用 `/uid設定` 來設定UID)'
        if update_use_time:
            user_last_use_time.update(user_id)
        return True, None
    
    def clearUserData(self, user_id: str) -> str:
        """從資料庫內永久刪除使用者資料

        ------
        Parameters
        user_id `str`: 使用者Discord ID
        ------
        Returns:
        `str`: 回覆給使用者的訊息
        """
        log.info(f'[指令][{user_id}]clearUserData')
        try:
            del self.__user_data[user_id]
            user_last_use_time.deleteUser(user_id)
        except:
            return '刪除失敗，找不到使用者資料'
        else:
            self.__saveUserData()
            return '使用者資料已全部刪除'
    
    def deleteExpiredUserData(self) -> None:
        """將超過30天未使用的使用者刪除"""
        now = datetime.now()
        count = 0
        user_data = dict(self.__user_data)
        for user_id in user_data.keys():
            if user_last_use_time.checkExpiry(user_id, now, 30) == True:
                self.clearUserData(user_id)
                count += 1
        log.info(f'[資訊][System]deleteExpiredUserData: {len(user_data)} 位使用者已檢查，已刪除 {count} 位過期使用者')

    def parseAbyssOverview(self, abyss: genshin.models.SpiralAbyss) -> discord.Embed:
        """解析深淵概述資料，包含日期、層數、戰鬥次數、總星數...等等

        ------
        Parameters
        abyss `SpiralAbyss`: 深境螺旋資料
        ------
        Returns
        `discord.Embed`: discord嵌入格式
        """
        result = discord.Embed(description=f'第 {abyss.season} 期：{abyss.start_time.astimezone().strftime("%Y.%m.%d")} ~ {abyss.end_time.astimezone().strftime("%Y.%m.%d")}', color=0x6959c1)
        get_char = lambda c: ' ' if len(c) == 0 else f'{getCharacterName(c[0])}：{c[0].value}'
        result.add_field(
            name=f'最深抵達：{abyss.max_floor}　戰鬥次數：{"👑" if abyss.total_stars == 36 and abyss.total_battles == 12 else abyss.total_battles}　★：{abyss.total_stars}',
            value=f'[最多擊破數] {get_char(abyss.ranks.most_kills)}\n'
                    f'[最強之一擊] {get_char(abyss.ranks.strongest_strike)}\n'
                    f'[受最多傷害] {get_char(abyss.ranks.most_damage_taken)}\n'
                    f'[Ｑ施放次數] {get_char(abyss.ranks.most_bursts_used)}\n'
                    f'[Ｅ施放次數] {get_char(abyss.ranks.most_skills_used)}',
            inline=False
        )
        return result
    
    def parseAbyssFloor(self, embed: discord.Embed, abyss: genshin.models.SpiralAbyss, full_data: bool = False) -> discord.Embed:
        """解析深淵每一樓層，將每層的星數、所使用的人物資料加到embed中
        
        ------
        Parameters
        embed `discord.Embed`: 從`parseAbyssOverview`函式取得的嵌入資料
        abyss `SpiralAbyss`: 深境螺旋資料
        full_data `bool`: `True`表示解析所有樓層；`False`表示只解析最後一層
        ------
        Returns
        `discord.Embed`: discord嵌入格式
        """
        for floor in abyss.floors:
            if full_data == False and floor is not abyss.floors[-1]:
                continue
            for chamber in floor.chambers:
                name = f'{floor.floor}-{chamber.chamber}　★{chamber.stars}'
                # 取得深淵上下半層角色名字
                chara_list = [[], []]
                for i, battle in enumerate(chamber.battles):
                    for chara in battle.characters:
                        chara_list[i].append(getCharacterName(chara))
                value = f'[{".".join(chara_list[0])}]／\n[{".".join(chara_list[1])}]'
                embed.add_field(name=name, value=value)
        return embed
    
    def parseCharacter(self, character: genshin.models.Character) -> discord.Embed:
        """解析角色，包含命座、等級、好感、武器、聖遺物
        
        ------
        Parameters
        character `Character`: 人物資料
        ------
        Returns
        `discord.Embed`: discord嵌入格式
        """
        color = {'pyro': 0xfb4120, 'electro': 0xbf73e7, 'hydro': 0x15b1ff, 'cryo': 0x70daf1, 'dendro': 0xa0ca22, 'anemo': 0x5cd4ac, 'geo': 0xfab632}
        embed = discord.Embed(color=color.get(character.element.lower()))
        embed.set_thumbnail(url=character.icon)
        embed.add_field(name=f'★{character.rarity} {character.name}', inline=True, value=f'命座：{character.constellation}\n等級：Lv. {character.level}\n好感：Lv. {character.friendship}')

        weapon = character.weapon
        embed.add_field(name=f'★{weapon.rarity} {weapon.name}', inline=True, value=f'精煉：{weapon.refinement} 階\n等級：Lv. {weapon.level}')

        if character.constellation > 0:
            number = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六'}
            msg = '\n'.join([f'第{number[constella.pos]}層：{constella.name}' for constella in character.constellations if constella.activated])
            embed.add_field(name='命之座', inline=False, value=msg)

        if len(character.artifacts) > 0:
            msg = '\n'.join([f'{artifact.pos_name}：{artifact.name} ({artifact.set.name})' for artifact in character.artifacts])
            embed.add_field(name='聖遺物', inline=False, value=msg)

        return embed

    def __parseNotes(self, notes: genshin.models.Notes, shortForm: bool = False) -> str:
        result = ''
        # 原粹樹脂
        result += f'{emoji.notes.resin}當前原粹樹脂：{notes.current_resin}/{notes.max_resin}\n'
        if notes.current_resin >= notes.max_resin:
            recover_time = '已額滿！'
        else:
            day_msg = getDayOfWeek(notes.resin_recovery_time)
            recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
        result += f'{emoji.notes.resin}全部恢復時間：{recover_time}\n'
        # 每日、週本
        if not shortForm:
            result += f'{emoji.notes.commission}每日委託任務：剩餘 {notes.max_commissions - notes.completed_commissions} 個\n'
            result += f'{emoji.notes.enemies_of_note}週本樹脂減半：剩餘 {notes.remaining_resin_discounts} 次\n'
        result += f'--------------------\n'
        # 洞天寶錢恢復時間
        result += f'{emoji.notes.realm_currency}當前洞天寶錢：{notes.current_realm_currency}/{notes.max_realm_currency}\n'
        if notes.max_realm_currency > 0:
            if notes.current_realm_currency >= notes.max_realm_currency:
                recover_time = '已額滿！'
            else:
                day_msg = getDayOfWeek(notes.realm_currency_recovery_time)
                recover_time = f'{day_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
            result += f'{emoji.notes.realm_currency}全部恢復時間：{recover_time}\n'
        # 參數質變儀剩餘時間
        if notes.transformer_recovery_time != None:
            t = notes.remaining_transformer_recovery_time
            if t.days > 0:
                recover_time = f'剩餘 {t.days} 天'
            elif t.hours > 0:
                recover_time = f'剩餘 {t.hours} 小時'
            elif t.minutes > 0:
                recover_time = f'剩餘 {t.minutes} 分'
            elif t.seconds > 0:
                recover_time = f'剩餘 {t.seconds} 秒'
            else:
                recover_time = '可使用'
            result += f'{emoji.notes.transformer}參數質變儀　：{recover_time}\n'
        # 探索派遣剩餘時間
        if not shortForm:
            result += f'--------------------\n'
            exped_finished = 0
            exped_msg = ''
            for expedition in notes.expeditions:
                exped_msg += f'· {getCharacterName(expedition.character)}'
                if expedition.finished:
                    exped_finished += 1
                    exped_msg += '：已完成\n'
                else:
                    day_msg = getDayOfWeek(expedition.completion_time)
                    exped_msg += f' 完成時間：{day_msg} {expedition.completion_time.strftime("%H:%M")}\n'
            result += f'探索派遣已完成/總數量：{exped_finished}/{len(notes.expeditions)}\n'
            result += exped_msg
        
        return result

    def __saveUserData(self) -> None:
        with open('data/user_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.__user_data, f)

    def __getGenshinClient(self, user_id: str) -> genshin.Client:
        uid = self.__user_data[user_id].get('uid')
        if uid != None and uid[0] in ['1', '2', '5']:
            client = genshin.Client(region=genshin.Region.CHINESE, lang='zh-cn')
        else:
            client = genshin.Client(lang='zh-tw')
        client.set_cookies(self.__user_data[user_id]['cookie'])
        client.default_game = genshin.Game.GENSHIN
        return client

genshin_app = GenshinApp()