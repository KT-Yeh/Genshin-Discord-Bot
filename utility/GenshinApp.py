import json
import discord
import genshin
from datetime import datetime, timedelta
from typing import Union, Tuple
from .utils import log, getCharacterName, trimCookie, user_last_use_time
from .config import config

class GenshinApp:
    def __init__(self) -> None:
        self.__server_dict = {'os_usa': '美服', 'os_euro': '歐服', 'os_asia': '亞服', 'os_cht': '台港澳服'}
        self.__uid_server_dict = {'1': '天空島', '2': '天空島', '5': '世界樹', '6': '美服', '7': '歐服', '8': '亞服', '9': '台港澳服'}
        self.__weekday_dict = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}
        try:
            with open('data/user_data.json', 'r', encoding="utf-8") as f:
                self.__user_data: dict[str, dict[str, str]] = json.load(f)
        except:
            self.__user_data: dict[str, dict[str, str]] = { }

    async def setCookie(self, user_id: str, cookie: str) -> str:
        """設定使用者Cookie
        :param user_id: 使用者Discord ID
        :cookie: Hoyolab cookie
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
            log.info(f'[例外][{user_id}]setCookie: [retcode]{e.retcode} [例外內容]{e.msg}')
            result = e.msg
        else:
            if len(accounts) == 0:
                log.info(f'[資訊][{user_id}]setCookie: 帳號內沒有任何角色')
                result = '帳號內沒有任何角色，取消設定Cookie'
            else:
                self.__user_data[user_id] = {}
                self.__user_data[user_id]['cookie'] = cookie
                log.info(f'[資訊][{user_id}]setCookie: Cookie設置成功')
                
                if len(accounts) == 1:
                    await self.setUID(user_id, str(accounts[0].uid))
                    result = f'Cookie已設定完成，角色UID: {accounts[0].uid} 已保存！'
                else:
                    result = f'帳號內共有{len(accounts)}個角色\n```'
                    for account in accounts:
                        result += f'UID:{account.uid} 等級:{account.level} 角色名字:{account.nickname}\n'
                    result += f'```\n請用 `/uid設定` 指定要保存的角色(例: `/uid設定 812345678`)'
                    self.__saveUserData()
        finally:
            return result
    
    async def setUID(self, user_id: str, uid: str, *, check_uid: bool = False) -> str:
        """設定原神UID，當帳號內有多名角色時，保存指定的UID
        :param user_id: 使用者Discord ID
        :param uid: 欲保存的原神UID
        """
        log.info(f'[指令][{user_id}]setUID: uid={uid}, check_uid={check_uid}')
        if not check_uid:
            self.__user_data[user_id]['uid'] = uid
            self.__saveUserData()
            return f'角色UID: {uid} 已設定完成'
            
        check, msg = self.checkUserData(user_id, checkUID=False)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        # 確認UID是否存在
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

    async def getRealtimeNote(self, user_id: str, check_resin_excess = False) -> str:
        """取得使用者即時便箋(樹脂、洞天寶錢、派遣、每日、週本)
        :param user_id: 使用者Discord ID
        :param check_resin_excess: 設為True時，只有當樹脂超過設定標準時才會回傳即時便箋結果，用於自動檢查樹脂
        """
        if not check_resin_excess:
            log.info(f'[指令][{user_id}]getRealtimeNote')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
   
        uid = self.__user_data[user_id]['uid']
        client = self.__getGenshinClient(user_id)
        result = None
        try:
            notes = await client.get_genshin_notes(int(uid))
        except genshin.errors.DataNotPublic as e:
            log.info(f'[例外][{user_id}]getRealtimeNote: {e.msg}')
            result = '即時便箋功能未開啟\n請從HOYOLAB網頁或App開啟即時便箋功能'
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]getRealtimeNote: [retcode]{e.retcode} [例外內容]{e.msg}')
            result = f'發生錯誤: [retcode]{e.retcode} [內容]{e.msg}'
        except Exception as e:
            log.error(f'[例外][{user_id}]getRealtimeNote: {e}')
            result = f'發生錯誤: {e}'
        else:
            if check_resin_excess == True and notes.current_resin < config.auto_check_resin_threshold:
                result = None
            else:
                result = f'{self.__uid_server_dict.get(uid[0])} {uid.replace(uid[3:-3], "***", 1)}\n'
                result += f'--------------------\n'
                result += self.__parseNotes(notes)
        finally:
            return result
    
    async def redeemCode(self, user_id: str, code: str) -> str:
        """為使用者使用指定的兌換碼
        :param user_id: 使用者Discord ID
        :param code: Hoyolab兌換碼
        """
        log.info(f'[指令][{user_id}]redeemCode: code={code}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            await client.redeem_code(code, int(self.__user_data[user_id]['uid']))
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]redeemCode: [retcode]{e.retcode} [例外內容]{e.msg}')
            result = e.msg
        except Exception as e:
            log.error(f'[例外][{user_id}]redeemCode: [例外內容]{e}')
            result = f'{e}'
        else:
            result = '兌換碼使用成功！'
        finally:
            return result
    
    async def claimDailyReward(self, user_id: str, *, honkai: bool = False) -> str:
        """為使用者在Hoyolab簽到
        :param user_id: 使用者Discord ID
        :param honkai: 是否也簽到崩壞3
        """
        log.info(f'[指令][{user_id}]claimDailyReward: honkai={honkai}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            reward = await client.claim_daily_reward()
        except genshin.errors.AlreadyClaimed:
            result = '原神今日獎勵已經領過了！'
        except genshin.errors.GenshinException as e:
            log.info(f'[例外][{user_id}]claimDailyReward: 原神[retcode]{e.retcode} [例外內容]{e.msg}')
            result = f'原神簽到失敗：{e.msg}'
        except Exception as e:
            log.error(f'[例外][{user_id}]claimDailyReward: 原神[例外內容]{e}')
            result = f'原神簽到失敗：{e}'
        else:
            result = f'原神今日簽到成功，獲得 {reward.amount}x {reward.name}！'
        
        # 崩壞3
        if honkai:
            result += ' '
            try:
                reward = await client.claim_daily_reward(game=genshin.Game.HONKAI)
            except genshin.errors.AlreadyClaimed:
                result += '崩壞3今日獎勵已經領過了！'
            except genshin.errors.GenshinException as e:
                log.info(f'[例外][{user_id}]claimDailyReward: 崩3[retcode]{e.retcode} [例外內容]{e.msg}')
                result += '崩壞3簽到失敗，找不到相關的崩壞3帳號' if e.retcode == -10002 else f'崩壞3簽到失敗：{e.msg}'
            except Exception as e:
                log.error(f'[例外][{user_id}]claimDailyReward: 崩3[例外內容]{e}')
                result = f'崩壞3簽到失敗：{e}'
            else:
                result += f'崩壞3今日簽到成功，獲得 {reward.amount}x {reward.name}！'
        return result

    async def getSpiralAbyss(self, user_id: str, previous: bool = False, full_data: bool = False) -> Union[str, discord.Embed]:
        """取得深境螺旋資訊
        :param user_id: 欲登入的使用者Discord ID
        :param previous: 是否查詢前一期的資訊
        :param full_data: 若為True，結果完整顯示9~12層資訊；若為False，結果只顯示最後一層資訊
        """
        log.info(f'[指令][{user_id}]getSpiralAbyss: previous={previous} full_data={full_data}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            abyss = await client.get_genshin_spiral_abyss(int(self.__user_data[user_id]['uid']), previous=previous)
        except genshin.errors.GenshinException as e:
            log.error(f'[例外][{user_id}]getSpiralAbyss: [retcode]{e.retcode} [例外內容]{e.msg}')
            result = e.msg
        except Exception as e:
            log.error(f'[例外][{user_id}]getSpiralAbyss: [例外內容]{e}')
            result = f'{e}'
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
            return result
    
    async def getTravelerDiary(self, user_id: str, month: str) -> Union[str, discord.Embed]:
        """取得使用者旅行者札記
        :param user_id: 使用者Discord ID
        :param month: 欲查詢的月份
        """
        log.info(f'[指令][{user_id}]getTravelerDiary: month={month}')
        check, msg = self.checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            client.uids[genshin.Game.GENSHIN] = int(self.__user_data[user_id]['uid'])
            diary = await client.get_diary(month=month)
        except genshin.errors.GenshinException as e:
            log.error(f'[例外][{user_id}]getTravelerDiary: [retcode]{e.retcode} [例外內容]{e.msg}')
            result = e.msg
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
            return result
    
    def checkUserData(self, user_id: str, *,checkUserID = True, checkCookie = True, checkUID = True) -> Tuple[bool, str]:
        if checkUserID and user_id not in self.__user_data.keys():
            log.info(f'[資訊][{user_id}]checkUserData: 找不到使用者')
            return False, f'找不到使用者，請先設定Cookie(輸入 `/cookie設定` 顯示說明)'
        else:
            if checkCookie and 'cookie' not in self.__user_data[user_id].keys():
                log.info(f'[資訊][{user_id}]checkUserData: 找不到Cookie')
                return False, f'找不到Cookie，請先設定Cookie(輸入 `/cookie設定` 顯示說明)'
            if checkUID and 'uid' not in self.__user_data[user_id].keys():
                log.info(f'[資訊][{user_id}]checkUserData: 找不到角色UID')
                return False, f'找不到角色UID，請先設定UID(使用 `/uid設定` 來設定UID)'
        user_last_use_time.update(user_id)
        return True, None
    
    def clearUserData(self, user_id: str) -> str:
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
        log.info(f'[資訊][System]deleteExpiredUserData: 過期使用者已檢查，已刪除 {count} 位使用者')

    def __parseNotes(self, notes: genshin.models.Notes) -> str:
        result = ''
        result += f'當前樹脂：{notes.current_resin}/{notes.max_resin}\n'
        
        if notes.current_resin == notes.max_resin:
            recover_time = '已額滿！'  
        else:
            day_msg = '今天' if notes.resin_recovery_time.day == datetime.now().day else '明天'
            recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
        result += f'樹脂全部恢復時間：{recover_time}\n'
        result += f'每日委託任務：{notes.completed_commissions} 已完成\n'
        result += f'週本樹脂減半：剩餘 {notes.remaining_resin_discounts} 次\n'
        result += f'--------------------\n'
        
        result += f'當前洞天寶錢/上限：{notes.current_realm_currency}/{notes.max_realm_currency}\n'
        # 洞天寶錢恢復時間
        if notes.current_realm_currency == notes.max_realm_currency:
            recover_time = '已額滿！'
        else:
            weekday_msg = self.__weekday_dict[notes.realm_currency_recovery_time.weekday()]
            recover_time = f'{weekday_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
        result += f'寶錢全部恢復時間：{recover_time}\n'
        # 參數質變儀剩餘時間
        if notes.transformer_recovery_time != None:
            if notes.remaining_transformer_recovery_time < 10:
                recover_time = '已完成！'
            else:
                t = timedelta(seconds=notes.remaining_transformer_recovery_time+10)
                if t.days > 0:
                    recover_time = f'{t.days} 天'
                elif t.seconds > 3600:
                    recover_time = f'{round(t.seconds/3600)} 小時'
                else:
                    recover_time = f'{round(t.seconds/60)} 分'
            result += f'參數質變儀剩餘時間：{recover_time}\n'

        result += f'--------------------\n'

        exped_finished = 0
        exped_msg = ''
        for expedition in notes.expeditions:
            exped_msg += f'· {getCharacterName(expedition.character)}'
            if expedition.finished:
                exped_finished += 1
                exped_msg += '：已完成\n'
            else:
                day_msg = '今天' if expedition.completion_time.day == datetime.now().day else '明天'
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