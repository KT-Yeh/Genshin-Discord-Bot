import json
import discord
import genshin
from datetime import datetime, timedelta
from typing import Sequence, Union, Tuple
from .utils import log, getCharacterName, trimCookie, getServerName, getDayOfWeek,user_last_use_time
from .config import config

class GenshinApp:
    def __init__(self) -> None:
        try:
            with open('data/user_data.json', 'r', encoding="utf-8") as f:
                self.__user_data: dict[str, dict[str, str]] = json.load(f)
        except:
            self.__user_data: dict[str, dict[str, str]] = { }

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
        try:
            accounts = await client.get_game_accounts()
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]setCookie: [retcode]{e.retcode} [例外內容]{e.original}')
            result = e.original
        else:
            if len(accounts) == 0:
                log.info(f'[資訊][{user_id}]setCookie: 帳號內沒有任何角色')
                result = '帳號內沒有任何角色，取消設定Cookie'
            else:
                self.__user_data[user_id] = {}
                self.__user_data[user_id]['cookie'] = cookie
                log.info(f'[資訊][{user_id}]setCookie: Cookie設置成功')
                
                if len(accounts) == 1 and len(str(accounts[0].uid)) == 9:
                    await self.setUID(user_id, str(accounts[0].uid))
                    result = f'Cookie已設定完成，角色UID: {accounts[0].uid} 已保存！'
                else:
                    result = f'帳號內共有{len(accounts)}個角色\n```'
                    for account in accounts:
                        result += f'UID:{account.uid} 等級:{account.level} 角色名字:{account.nickname}\n'
                    result += f'```\n請用 `/uid設定` 指定要保存原神的角色(例: `/uid設定 812345678`)'
                    self.__saveUserData()
        finally:
            return result
    
    async def setUID(self, user_id: str, uid: str, *, check_uid: bool = False) -> str:
        """設定原神UID，當帳號內有多名角色時，保存指定的UID

        ------
        Parameters
        user_id `str`: 使用者Discord ID
        uid `str`: 欲保存的原神UID
        check_uid `bool`: `True`表示檢查此UID是否有效、`False`表示不檢查直接儲存
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        log.info(f'[指令][{user_id}]setUID: uid={uid}, check_uid={check_uid}')
        if not check_uid:
            self.__user_data[user_id]['uid'] = uid
            self.__saveUserData()
            return f'角色UID: {uid} 已設定完成'
        check, msg = self.checkUserData(user_id, checkUID=False)
        if check == False:
            return msg
        if len(uid) != 9:
            return f'UID長度錯誤，請輸入正確的原神UID'
        # 確認UID是否存在
        client = self.__getGenshinClient(user_id)
        try:
            accounts = await client.get_game_accounts()
        except Exception as e:
            log.error(f'[例外][{user_id}]setUID: {e}')
            return '確認帳號資料失敗，請重新設定Cookie或是稍後再試'
        else:
            if int(uid) in [account.uid for account in accounts]:
                self.__user_data[user_id]['uid'] = uid
                self.__saveUserData()
                log.info(f'[資訊][{user_id}]setUID: {uid} 已設定完成')
                return f'角色UID: {uid} 已設定完成'
            else:
                log.info(f'[資訊][{user_id}]setUID: 找不到該UID的角色資料')
                return f'找不到該UID的角色資料，請確認是否輸入正確'

    async def getRealtimeNote(self, user_id: str, *, schedule = False) -> Union[None, str, discord.Embed]:
        """取得使用者即時便箋(樹脂、洞天寶錢、參數質變儀、派遣、每日、週本)
        
        ------
        Parameters
        user_id `str`: 使用者Discord ID
        schedule `bool`: 是否為排程檢查樹脂，設為`True`時，只有當樹脂超過設定標準時才會回傳即時便箋結果
        ------
        Returns
        `None | str | Embed`: 自動檢查樹脂時，在正常未溢出的情況下回傳`None`；發生例外回傳錯誤訊息`str`、正常情況回傳查詢結果`discord.Embed`
        """
        if not schedule:
            log.info(f'[指令][{user_id}]getRealtimeNote')
        check, msg = self.checkUserData(user_id, update_use_time=(not schedule))
        if check == False:
            return msg
   
        uid = self.__user_data[user_id]['uid']
        client = self.__getGenshinClient(user_id)
        try:
            notes = await client.get_genshin_notes(int(uid))
        except genshin.errors.DataNotPublic:
            log.info(f'[例外][{user_id}]getRealtimeNote: DataNotPublic')
            return '即時便箋功能未開啟，請先從Hoyolab網頁或App開啟即時便箋功能'
        except genshin.errors.InvalidCookies as e:
            log.info(f'[例外][{user_id}]getRealtimeNote: [retcode]{e.retcode} [例外內容]{e.original}')
            return 'Cookie已過期失效，請重新設定Cookie'
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]getRealtimeNote: [retcode]{e.retcode} [例外內容]{e.original}')
            return e.original
        except Exception as e:
            log.error(f'[例外][{user_id}]getRealtimeNote: {e}')
            return str(e)
        else:
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
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            await client.redeem_code(code, int(self.__user_data[user_id]['uid']))
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]redeemCode: [retcode]{e.retcode} [例外內容]{e.original}')
            result = e.original
        except Exception as e:
            log.error(f'[例外][{user_id}]redeemCode: [例外內容]{e}')
            result = f'{e}'
        else:
            result = f'兌換碼 {code} 使用成功！'
        finally:
            return result
    
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
        # Hoyolab社群簽到
        try:
            await client.check_in_community()
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]claimDailyReward: Hoyolab[retcode]{e.retcode} [例外內容]{e.original}')
        except Exception as e:
            log.error(f'[例外][{user_id}]claimDailyReward: Hoyolab[例外內容]{e}')
        # 原神簽到
        try:
            reward = await client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            result = '原神今日獎勵已經領過了！'
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]claimDailyReward: 原神[retcode]{e.retcode} [例外內容]{e.original}')
            result = f'原神簽到失敗：{e.original}'
        except Exception as e:
            log.error(f'[例外][{user_id}]claimDailyReward: 原神[例外內容]{e}')
            result = f'原神簽到失敗：{e}'
        else:
            result = f'原神今日簽到成功，獲得 {reward.amount}x {reward.name}！'
        # 崩壞3簽到
        if honkai:
            result += ' '
            try:
                reward = await client.claim_daily_reward(game=genshin.Game.HONKAI)
            except genshin.errors.AlreadyClaimed:
                result += '崩壞3今日獎勵已經領過了！'
            except genshin.errors.GenshinException as e:
                log.info(f'[例外][{user_id}]claimDailyReward: 崩3[retcode]{e.retcode} [例外內容]{e.original}')
                result += '崩壞3簽到失敗，未查詢到角色資訊，請確認艦長是否已綁定新HoYoverse通行證' if e.retcode == -10002 else f'崩壞3簽到失敗：{e.original}'
            except Exception as e:
                log.error(f'[例外][{user_id}]claimDailyReward: 崩3[例外內容]{e}')
                result = f'崩壞3簽到失敗：{e}'
            else:
                result += f'崩壞3今日簽到成功，獲得 {reward.amount}x {reward.name}！'
        return result

    async def getSpiralAbyss(self, user_id: str, previous: bool = False) -> Union[str, genshin.models.SpiralAbyss]:
        """取得深境螺旋資訊

        ------
        Parameters
        user_id `str`: 使用者Discord ID
        previous `bool`: `True`查詢前一期的資訊、`False`查詢本期資訊
        ------
        Returns
        `Union[str, SpiralAbyss]`: 發生例外回傳錯誤訊息`str`、正常情況回傳查詢結果`SpiralAbyss`
        """
        log.info(f'[指令][{user_id}]getSpiralAbyss: previous={previous}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            abyss = await client.get_genshin_spiral_abyss(int(self.__user_data[user_id]['uid']), previous=previous)
        except genshin.errors.GenshinException as e:
            log.error(f'[例外][{user_id}]getSpiralAbyss: [retcode]{e.retcode} [例外內容]{e.original}')
            return e.original
        except Exception as e:
            log.error(f'[例外][{user_id}]getSpiralAbyss: [例外內容]{e}')
            return f'{e}'
        else:
            return abyss
    
    async def getTravelerDiary(self, user_id: str, month: int) -> Union[str, discord.Embed]:
        """取得使用者旅行者札記

        ------
        Parameters:
        user_id `str`: 使用者Discord ID
        month `int`: 欲查詢的月份
        ------
        Returns:
        `Union[str, discord.Embed]`: 發生例外回傳錯誤訊息`str`、正常情況回傳查詢結果`discord.Embed`
        """
        log.info(f'[指令][{user_id}]getTravelerDiary: month={month}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            diary = await client.get_diary(int(self.__user_data[user_id]['uid']), month=month)
        except genshin.errors.GenshinException as e:
            log.error(f'[例外][{user_id}]getTravelerDiary: [retcode]{e.retcode} [例外內容]{e.original}')
            result = e.original
        except Exception as e:
            log.error(f'[例外][{user_id}]getTravelerDiary: [例外內容]{e}')
            result = f'{e}'
        else:    
            d = diary.data
            result = discord.Embed(
                title=f'{diary.nickname}的旅行者札記：{month}月',
                description=f'原石收入比上個月{"增加" if d.primogems_rate > 0 else "減少"}了{abs(d.primogems_rate)}%，摩拉收入比上個月{"增加" if d.mora_rate > 0 else "減少"}了{abs(d.mora_rate)}%',
                color=0xfd96f4
            )
            result.add_field(
                name='當月共獲得', 
                value=f'原石：{d.current_primogems} ({round(d.current_primogems/160)})　上個月：{d.last_primogems} ({round(d.last_primogems/160)})\n'
                    f'摩拉：{format(d.current_mora, ",")}　上個月：{format(d.last_mora, ",")}',
                inline=False
            )
            # 將札記原石組成平分成兩個field
            for i in range(0, 2):
                msg = ''
                length = len(d.categories)
                for j in range(round(length/2*i), round(length/2*(i+1))):
                    msg += f'{d.categories[j].name[0:2]}：{d.categories[j].percentage}%\n'
                result.add_field(name=f'原石收入組成 ({i+1})', value=msg, inline=True)
        finally:
            return result
    
    async def getRecordCard(self, user_id: str) -> Union[str, Tuple[genshin.models.RecordCard, genshin.models.PartialGenshinUserStats]]:
        """取得使用者記錄卡片

        ------
        Parameters:
        user_id `str`: 使用者Discord ID
        ------
        Returns:
        `str | (RecordCard, PartialGenshinUserStats)`: 發生例外回傳錯誤訊息`str`、正常情況回傳查詢結果`(RecordCard, PartialGenshinUserStats)`
        """
        log.info(f'[指令][{user_id}]getRecordCard')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            cards = await client.get_record_cards()
            userstats = await client.get_partial_genshin_user(int(self.__user_data[user_id]['uid']))
        except genshin.errors.GenshinException as e:
            log.error(f'[例外][{user_id}]getRecordCard: [retcode]{e.retcode} [例外內容]{e.original}')
            return e.original
        except Exception as e:
            log.error(f'[例外][{user_id}]getRecordCard: [例外內容]{e}')
            return str(e)
        else:
            for card in cards:
                if card.uid == int(self.__user_data[user_id]['uid']):
                    return (card, userstats)
            return '找不到原神紀錄卡片'

    async def getCharacters(self, user_id: str) -> Union[str, Sequence[genshin.models.Character]]:
        """取得使用者所有角色資料

        ------
        Parameters:
        user_id `str`: 使用者Discord ID
        ------
        Returns:
        `str | Sequence[Character]`: 發生例外回傳錯誤訊息`str`、正常情況回傳查詢結果`Sequence[Character]`
        """
        log.info(f'[指令][{user_id}]getCharacters')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            characters = await client.get_genshin_characters(int(self.__user_data[user_id]['uid']))
        except genshin.errors.GenshinException as e:
            log.error(f'[例外][{user_id}]getCharacters: [retcode]{e.retcode} [例外內容]{e.original}')
            return e.original
        except Exception as e:
            log.error(f'[例外][{user_id}]getCharacters: [例外內容]{e}')
            return str(e)
        else:
            return characters
    
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
        result += f'當前樹脂：{notes.current_resin}/{notes.max_resin}\n'
        # 樹脂
        if notes.current_resin == notes.max_resin:
            recover_time = '已額滿！'  
        else:
            day_msg = getDayOfWeek(notes.resin_recovery_time)
            recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
        result += f'樹脂全部恢復時間：{recover_time}\n'
        # 每日、週本
        if not shortForm:
            result += f'每日委託任務：{notes.completed_commissions} 已完成\n'
            result += f'週本樹脂減半：剩餘 {notes.remaining_resin_discounts} 次\n'
        result += f'--------------------\n'
        # 洞天寶錢恢復時間
        result += f'當前洞天寶錢：{notes.current_realm_currency}/{notes.max_realm_currency}\n'
        if notes.max_realm_currency > 0:
            if notes.current_realm_currency == notes.max_realm_currency:
                recover_time = '已額滿！'
            else:
                day_msg = getDayOfWeek(notes.realm_currency_recovery_time)
                recover_time = f'{day_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
            result += f'寶錢全部恢復時間：{recover_time}\n'
        # 參數質變儀剩餘時間
        if notes.transformer_recovery_time != None:
            t = notes.remaining_transformer_recovery_time
            if t.days > 0:
                recover_time = f'{t.days} 天'
            elif t.hours > 0:
                recover_time = f'{t.hours} 小時'
            elif t.minutes > 0:
                recover_time = f'{t.minutes} 分'
            elif t.seconds > 0:
                recover_time = f'{t.seconds} 秒'
            else:
                recover_time = '可使用'
            result += f'參數質變儀剩餘時間：{recover_time}\n'
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
        try:
            with open('data/user_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.__user_data, f)
        except:
            log.error('[例外][System]GenshinApp > __saveUserData: 存檔寫入失敗')

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