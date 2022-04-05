import asyncio
import json
import discord
import genshin
from datetime import datetime
from typing import Union, Tuple
from .utils import log, getCharacterName
from .config import config

class GenshinApp:
    def __init__(self) -> None:
        self.__server_dict = {'os_usa': '美服', 'os_euro': '歐服', 'os_asia': '亞服', 'os_cht': '台港澳服'}
        self.__weekday_dict = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}
        try:
            with open('data/user_data.json', 'r', encoding="utf-8") as f:
                self.__user_data = json.loads(f.read())
        except:
            self.__user_data = { } 

    async def setCookie(self, user_id: str, cookie: str) -> str:
        """設定使用者Cookie
        :param user_id: 使用者Discord ID
        :cookie: Hoyolab cookie
        """
        user_id = str(user_id)
        log.info(f'{user_id} Cookie設置:{cookie}')
        
        # 從Cookie確認是否有ltuid, ltoken, cookie_token, account_id
        if any(key not in cookie for key in ('cookie_token', 'ltuid', 'ltoken', 'account_id')):
            return '無效的Cookie，請重新輸入正確的Cookie'
        
        client = genshin.GenshinClient()
        client.set_cookies(cookie)
        try:
            accounts = await client.genshin_accounts()
            await client.close()
        except genshin.errors.GenshinException as e:
            log.error(e.msg)
            return '無效的Cookie，請重新輸入正確的Cookie'
        else:
            if  len(accounts) == 0:
                log.info('帳號內沒有任何角色')
                return '錯誤，該帳號內沒有任何角色'

            self.__user_data[user_id] = {}
            self.__user_data[user_id]['cookie'] = cookie
            log.info(f'{user_id}的Cookie設置成功:{cookie}')
            log.info(f'{user_id}共有{len(accounts)}個角色')
            
            if len(accounts) == 1:
                self.setUID(user_id, accounts[0].uid)
                return 'Cookie設定完成！'
            else:
                message = f'```帳號內共有{len(accounts)}個角色\n'
                for account in accounts:
                    log.info(f'UID:{account.uid} 等級:{account.level} 角色名字:{account.nickname}')
                    message += f'UID:{account.uid} 等級:{account.level} 角色名字:{account.nickname}\n'
                message += f'```\n請用`{config.bot_prefix}uid`指定要保存的角色(例: `{config.bot_prefix}uid 812345678`)'
                self.__saveUserData()
                return message
    
    def setUID(self, user_id: str, uid: str) -> bool:
        """設定原神UID，當帳號內有多名角色時，保存指定的UID
        :param user_id: 使用者Discord ID
        :param uid: 欲保存的原神UID
        """
        try:
            user_id = str(user_id)
            uid = str(uid)
            self.__user_data[user_id]['uid'] = uid
            self.__saveUserData()
            log.info(f'{user_id}角色UID:{uid}已保存')
            return True
        except:
            log.error(f'{user_id}角色UID:{uid}保存失敗')
            return False

    async def getDailyNote(self, user_id: str) -> str:
        """取得使用者即時便箋(樹脂、洞天寶錢、派遣、每日、週本)
        :param user_id: 使用者Discord ID
        """
        user_id = str(user_id)
        check, msg = self.__checkUserData(user_id)
        if check == False:
            return msg
   
        uid = self.__user_data[user_id]['uid']
        client = self.__getGenshinClient(user_id)
        task1 = asyncio.create_task(client.get_diary(uid))
        task2 = asyncio.create_task(client.get_notes(uid))
        try:
            account = await task1
            notes = await task2
            await client.close()
        except genshin.errors.DataNotPublic as e:
            log.error(e.msg)
            return '即時便箋未開啟\n請從HOYOLAB網頁或App開啟即時便箋功能'
        except genshin.errors.GenshinException as e:
            log.error(e.msg)
            return e.msg

        result = f'{account.nickname} {self.__server_dict[account.region]} {uid.replace(uid[3:-3], "***", 1)}\n'
        result += f'--------------------\n'
        result += self.__parseNotes(notes)
        return result
    
    async def redeemCode(self, user_id: str, code: str) -> str:
        """為使用者使用指定的兌換碼
        :param user_id: 使用者Discord ID
        :param code: Hoyolab兌換碼
        """
        user_id = str(user_id)
        check, msg = self.__checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            await client.redeem_code(code, self.__user_data[user_id]['uid'])
            await client.close()
        except genshin.errors.GenshinException as e:
            log.error(f'{e.msg}')
            return e.msg
        else:
            return '兌換碼使用成功！'
    
    async def claimDailyReward(self, user_id: str) -> str:
        """為使用者在Hoyolab簽到
        :param user_id: 使用者Discord ID
        """
        user_id = str(user_id)
        check, msg = self.__checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            reward = await client.claim_daily_reward()
            await client.close()
        except genshin.AlreadyClaimed:
            return '今日獎勵已經領過了！'
        else:
            return f'Hoyolab今日簽到成功！獲得 {reward.amount}x {reward.name}'

    async def getSpiralAbyss(self, user_id: str, uid: str = None, previous: bool = False, full_data: bool = False) -> Union[str, discord.Embed]:
        """取得深境螺旋資訊
        :param user_id: 欲登入的使用者Discord ID
        :param uid: 欲查詢的原神UID，若為None，則查詢使用者自己已保存的UID
        :param previous: 是否查詢前一期的資訊
        :param full_data: 若為True，結果完整顯示9~12層資訊；若為False，結果只顯示最後一層資訊
        """
        user_id = str(user_id)
        check, msg = self.__checkUserData(user_id)
        if check == False:
            return msg
        if uid is None:
            uid = self.__user_data[user_id]['uid']
        client = self.__getGenshinClient(user_id)
        try:
            abyss = await client.get_spiral_abyss(uid, previous=previous)
            await client.close()
        except genshin.errors.GenshinException as e:
            log.error(e.msg)
            return e.msg
        
        embed = discord.Embed(title=f'深境螺旋第 {abyss.season} 期戰績', color=0x7fbcf5)
        embed.add_field(
            name=f'最深抵達：{abyss.max_floor}　戰鬥次數：{abyss.total_battles}　★：{abyss.total_stars}', 
            value=f'統計週期：{abyss.start_time.strftime("%Y.%m.%d")} ~ {abyss.end_time.strftime("%Y.%m.%d")}', 
            inline=False
        )
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
                embed.add_field(name=name, value=value)
        return embed
    
    async def getTravelerDiary(self, user_id: str, month: str) -> Union[str, discord.Embed]:
        """取得使用者旅行者札記
        :param user_id: 使用者Discord ID
        :param month: 欲查詢的月份
        """
        user_id = str(user_id)
        check, msg = self.__checkUserData(user_id)
        if check == False:
            return msg
        client = self.__getGenshinClient(user_id)
        try:
            diary = await client.get_diary(self.__user_data[user_id]['uid'], month=month)
            await client.close()
        except genshin.errors.GenshinException as e:
            log.error(e.msg)
            return e.msg
        
        d = diary.data
        embed = discord.Embed(
            title=f'{diary.nickname}的旅行者札記：{month}月',
            description=f'原石收入比上個月{"增加" if d.primogems_rate > 0 else "減少"}了{abs(d.primogems_rate)}%，摩拉收入比上個月{"增加" if d.mora_rate > 0 else "減少"}了{abs(d.mora_rate)}%',
            color=0xfd96f4
        )
        embed.add_field(
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
            embed.add_field(name=f'原石收入組成 {i+1}', value=msg, inline=True)
        return embed
    
    def __checkUserData(self, user_id: str, *,checkUserID = True, checkCookie = True, checkUID = True) -> Tuple[bool, str]:
        if checkUserID and user_id not in self.__user_data.keys():
            log.info('找不到使用者，請先設定Cookie(輸入 `%h` 顯示說明)')
            return False, f'找不到使用者，請先設定Cookie(輸入 `{config.bot_prefix}help cookie` 顯示說明)'
        else:
            if checkCookie and 'cookie' not in self.__user_data[user_id].keys():
                log.info('找不到Cookie，請先設定Cookie(輸入 `%h` 顯示說明)')
                return False, f'找不到Cookie，請先設定Cookie(輸入 `{config.bot_prefix}help cookie` 顯示說明)'
            if checkUID and 'uid' not in self.__user_data[user_id].keys():
                log.info('找不到角色UID，請先設定UID(輸入 `%h` 顯示說明)')
                return False, f'找不到角色UID，請先設定UID(輸入 `{config.bot_prefix}help` 顯示說明)'
        return True, None

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
        with open('data/user_data.json', 'w') as f:
            f.write(json.dumps(self.__user_data))

    def __getGenshinClient(self, user_id: str) -> genshin.GenshinClient:
        uid = str(self.__user_data[user_id]['uid'])
        client = genshin.ChineseClient() if uid.startswith('1') else genshin.GenshinClient(lang='zh-tw')
        client.set_cookies(self.__user_data[user_id]['cookie'])
        return client

genshin_app = GenshinApp()