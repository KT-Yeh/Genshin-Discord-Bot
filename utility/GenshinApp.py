import json
import discord
import genshin
from datetime import datetime
from typing import Union, Tuple
from .utils import log, getCharacterName, trimCookie
import os
from dotenv import load_dotenv
load_dotenv()

class GenshinApp:
    def __init__(self) -> None:
        self.__server_dict = {'os_usa': '美服', 'os_euro': '歐服', 'os_asia': '亞服', 'os_cht': '台港澳服'}
        self.__weekday_dict = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}
        try:
            with open('data/user_data.json', 'r', encoding="utf-8") as f:
                self.__user_data = json.load(f)
        except:
            self.__user_data = { }

    async def setCookie(self, user_id: str, cookie: str) -> str:
        """設定使用者Cookie
        :param user_id: 使用者Discord ID
        :cookie: Hoyolab cookie
        """
        log.info(f'setCookie(user_id={user_id}, cookie={cookie})') 
        user_id = str(user_id)
        cookie = trimCookie(cookie)
        if cookie == None:
            return f'無效的Cookie，請重新輸入(使用 `{os.getenv("BOT_PREFIX")}help cookie` 查看教學)'
        client = genshin.GenshinClient()
        client.set_cookies(cookie)
        try:
            accounts = await client.genshin_accounts()
        except genshin.errors.GenshinException as e:
            log.error(f'{user_id}: [{e.retcode}] {e.msg}')
            result = e.msg
        else:
            if len(accounts) == 0:
                log.info('帳號內沒有任何角色')
                result = '發生錯誤，該帳號內沒有任何角色'
            else:
                self.__user_data[user_id] = {}
                self.__user_data[user_id]['cookie'] = cookie
                log.info(f'{user_id}的Cookie設置成功')
                
                if len(accounts) == 1:
                    self.setUID(user_id, str(accounts[0].uid))
                    result = 'Cookie設定完成！'
                else:
                    result = f'```帳號內共有{len(accounts)}個角色\n'
                    for account in accounts:
                        result += f'UID:{account.uid} 等級:{account.level} 角色名字:{account.nickname}\n'
                    result += f'```\n請用`{os.getenv("BOT_PREFIX")}uid`指定要保存的角色(例: `{os.getenv("BOT_PREFIX")}uid 812345678`)'
                    self.__saveUserData()
        finally:
            await client.close()
            return result
    
    def setUID(self, user_id: str, uid: str) -> str:
        """設定原神UID，當帳號內有多名角色時，保存指定的UID
        :param user_id: 使用者Discord ID
        :param uid: 欲保存的原神UID
        """
        if all(char.isdigit() for char in uid) == False:
            return 'UID格式錯誤，只能包含數字，請重新輸入'
        try:
            self.__user_data[user_id]['uid'] = uid
            self.__saveUserData()
            log.info(f'{user_id}角色UID:{uid}已保存')
            return f'角色UID: {uid} 已設定完成'
        except:
            log.error(f'{user_id}角色UID:{uid}保存失敗')
            return f'角色UID: {uid} 設定失敗，請先設定Cookie(輸入 `{os.getenv("BOT_PREFIX")}help cookie` 取得詳情)'

    async def getRealtimeNote(self, user_id: str, check_resin_excess = False) -> str:
        """取得使用者即時便箋(樹脂、洞天寶錢、派遣、每日、週本)
        :param user_id: 使用者Discord ID
        :param check_resin_excess: 設為True時，只有當樹脂超過設定標準時才會回傳即時便箋結果，用於自動檢查樹脂
        """
        log.info(f'getRealtimeNote(user_id={user_id}, check_resin_excess={check_resin_excess})')
        user_id = str(user_id)
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
   
        uid = self.__user_data[user_id]['uid']
        client = self.__getGenshinClient(user_id)
        result = None
        try:
            notes = await client.get_notes(uid)
        except genshin.errors.DataNotPublic as e:
            log.error(e.msg)
            result = '即時便箋功能未開啟\n請從HOYOLAB網頁或App開啟即時便箋功能'
        except genshin.errors.GenshinException as e:
            log.error(e.msg)
            result = e.msg
        except Exception as e:
            log.error(e)
        else:
            if check_resin_excess == True and notes.current_resin < os.getenv('AUTO_CHECK_RESIN_THRESHOLD'):
                result = None
            else:
                try:
                    account = await client.get_diary(uid)
                    result = f'{account.nickname} {self.__server_dict[account.region]} {uid.replace(uid[3:-3], "***", 1)}\n'
                except:
                    result = f'{uid.replace(uid[3:-3], "***", 1)}\n'
                result += f'--------------------\n'
                result += self.__parseNotes(notes)
        finally:
            await client.close()
            return result
    
    async def redeemCode(self, user_id: str, code: str) -> str:
        """為使用者使用指定的兌換碼
        :param user_id: 使用者Discord ID
        :param code: Hoyolab兌換碼
        """
        log.info(f'redeemCode(uesr_id={user_id}, code={code})')
        user_id = str(user_id)
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            await client.redeem_code(code, self.__user_data[user_id]['uid'])
        except genshin.errors.GenshinException as e:
            log.error(f'{e.msg}')
            result = e.msg
        else:
            result = '兌換碼使用成功！'
        finally:
            await client.close()
            return result
    
    async def claimDailyReward(self, user_id: str) -> str:
        """為使用者在Hoyolab簽到
        :param user_id: 使用者Discord ID
        """
        log.info(f'claimDailyReward(uesr_id={user_id})')
        user_id = str(user_id)
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            reward = await client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            result = '今日獎勵已經領過了！'
        except genshin.errors.GenshinException as e:
            log.error(e.msg)
            result = e.msg
        else:
            result = f'Hoyolab今日簽到成功！獲得 {reward.amount}x {reward.name}'
        finally:
            await client.close()
            return result

    async def getSpiralAbyss(self, user_id: str, uid: str = None, previous: bool = False, full_data: bool = False) -> Union[str, discord.Embed]:
        """取得深境螺旋資訊
        :param user_id: 欲登入的使用者Discord ID
        :param uid: 欲查詢的原神UID，若為None，則查詢使用者自己已保存的UID
        :param previous: 是否查詢前一期的資訊
        :param full_data: 若為True，結果完整顯示9~12層資訊；若為False，結果只顯示最後一層資訊
        """
        log.info(f'getSpiralAbyss(user_id={user_id}, uid={uid})')
        user_id = str(user_id)
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        if uid is None:
            uid = self.__user_data[user_id]['uid']
        client = self.__getGenshinClient(user_id)
        try:
            abyss = await client.get_spiral_abyss(uid, previous=previous)
        except genshin.errors.GenshinException as e:
            log.error(e.msg)
            result = e.msg
        else:
            result = discord.Embed(title=f'深境螺旋第 {abyss.season} 期戰績', color=0x7fbcf5)
            result.add_field(
                name=f'最深抵達：{abyss.max_floor}　戰鬥次數：{abyss.total_battles}　★：{abyss.total_stars}', 
                value=f'統計週期：{abyss.start_time.strftime("%Y.%m.%d")} ~ {abyss.end_time.strftime("%Y.%m.%d")}', 
                inline=False
            )
            # 取得深淵每一層資料
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
                    value = f'[{".".join(chara_list[0])}]／[{".".join(chara_list[1])}]'
                    result.add_field(name=name, value=value)
        finally:
            await client.close()
            return result
    
    async def getTravelerDiary(self, user_id: str, month: str) -> Union[str, discord.Embed]:
        """取得使用者旅行者札記
        :param user_id: 使用者Discord ID
        :param month: 欲查詢的月份
        """
        log.info(f'getTravelerDiary(user_id={user_id}, month={month})')
        user_id = str(user_id)
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            diary = await client.get_diary(self.__user_data[user_id]['uid'], month=month)
        except genshin.errors.GenshinException as e:
            log.error(e.msg)
            result = e.msg
        else:    
            d = diary.data
            result = discord.Embed(
                title=f'{diary.nickname}的旅行者札記：{month}月',
                description=f'原石收入比上個月{"增加" if d.primogems_rate > 0 else "減少"}了{abs(d.primogems_rate)}%，摩拉收入比上個月{"增加" if d.mora_rate > 0 else "減少"}了{abs(d.mora_rate)}%',
                color=0xfd96f4
            )
            result.add_field(
                name='當月共獲得', 
                value=f'原石：{d.current_primogems}　上個月：{d.last_primogems}\n'
                    f'摩拉：{d.current_mora}　上個月：{d.last_mora}',
                inline=False
            )
            # 將札記原石組成平分成兩個field
            for i in range(0, 2):
                msg = ''
                length = len(d.categories)
                for j in range(round(length/2*i), round(length/2*(i+1))):
                    msg += f'{d.categories[j].name[0:2]}：{d.categories[j].percentage}%\n'
                result.add_field(name=f'原石收入組成 {i+1}', value=msg, inline=True)
        finally:
            await client.close()
            return result
    
    def checkUserData(self, user_id: str, *,checkUserID = True, checkCookie = True, checkUID = True) -> Tuple[bool, str]:
        if checkUserID and user_id not in self.__user_data.keys():
            log.info('找不到使用者，請先設定Cookie(輸入 `%h` 顯示說明)')
            return False, f'找不到使用者，請先設定Cookie(輸入 `{os.getenv("BOT_PREFIX")}help cookie` 顯示說明)'
        else:
            if checkCookie and 'cookie' not in self.__user_data[user_id].keys():
                log.info('找不到Cookie，請先設定Cookie(輸入 `%h` 顯示說明)')
                return False, f'找不到Cookie，請先設定Cookie(輸入 `{os.getenv("BOT_PREFIX")}help cookie` 顯示說明)'
            if checkUID and 'uid' not in self.__user_data[user_id].keys():
                log.info('找不到角色UID，請先設定UID(輸入 `%h` 顯示說明)')
                return False, f'找不到角色UID，請先設定UID(輸入 `{os.getenv("BOT_PREFIX")}help` 顯示說明)'
        return True, None
    
    def clearUserData(self, user_id: str) -> str:
        try:
            del self.__user_data[user_id]
        except:
            return '刪除失敗，找不到使用者資料'
        else:
            self.__saveUserData()
            return '使用者資料已全部刪除'

    def __parseNotes(self, notes: genshin.models.Notes) -> str:
        result = ''
        result += f'當前樹脂：{notes.current_resin}/{notes.max_resin}\n'
        
        if notes.current_resin == notes.max_resin:
            recover_time = '已額滿！'  
        else:
            day_msg = '今天' if notes.resin_recovered_at.day == datetime.now().day else '明天'
            recover_time = f'{day_msg} {notes.resin_recovered_at.strftime("%H:%M")}'
        result += f'樹脂全部恢復時間：{recover_time}\n'
        result += f'每日委託任務：{notes.completed_commissions} 已完成\n'
        result += f'當前洞天寶錢/上限：{notes.current_realm_currency}/{notes.max_realm_currency}\n'
        result += f'寶錢全部恢復時間：{self.__weekday_dict[notes.realm_currency_recovered_at.weekday()]} {notes.realm_currency_recovered_at.strftime("%H:%M")}\n'
        result += f'週本樹脂減半：剩餘 {notes.remaining_resin_discounts} 次\n'
        result += f'--------------------\n'

        exped_finished = 0
        exped_msg = ''
        for expedition in notes.expeditions:
            exped_msg += f'· {getCharacterName(expedition.character)}'
            if expedition.finished:
                exped_finished += 1
                exped_msg += '：已完成\n'
            else:
                day_msg = '今天' if expedition.completed_at.day == datetime.now().day else '明天'
                exped_msg += f' 完成時間：{day_msg} {expedition.completed_at.strftime("%H:%M")}\n'
        result += f'探索派遣已完成/總數量：{exped_finished}/{len(notes.expeditions)}\n'
        result += exped_msg
        
        return result
        
    def __saveUserData(self) -> None:
        try:
            with open('data/user_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.__user_data, f)
        except:
            log.error('__saveUserData(self)')

    def __getGenshinClient(self, user_id: str) -> genshin.GenshinClient:
        uid = str(self.__user_data[user_id]['uid'])
        client = genshin.ChineseClient() if uid.startswith('1') else genshin.GenshinClient(lang='zh-tw')
        client.set_cookies(self.__user_data[user_id]['cookie'])
        return client

genshin_app = GenshinApp()