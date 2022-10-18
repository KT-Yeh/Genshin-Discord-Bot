import asyncio
import discord
import genshin
import sentry_sdk
from typing import Sequence, Union, Tuple, Optional
from data.database import db, User
from .emoji import emoji
from .utils import log, trimCookie, getServerName, getDayOfWeek, getAppCommandMention

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
        pass

    @generalErrorHandler
    async def setCookie(self, user_id: int, cookie: str) -> str:
        """設定使用者Cookie
        
        ------
        Parameters
        user_id `int`: 使用者Discord ID
        cookie `str`: Hoyolab cookie
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        log.info(f'[指令][{user_id}]setCookie: cookie={cookie}')
        cookie = trimCookie(cookie)
        if cookie == None:
            return f'無效的Cookie，請重新輸入(使用 {getAppCommandMention("cookie設定")} 顯示說明)'
        client = genshin.Client(lang='zh-tw')
        client.set_cookies(cookie)
        accounts = await client.genshin_accounts()
        if len(accounts) == 0:
            log.info(f'[資訊][{user_id}]setCookie: 帳號內沒有任何角色')
            result = '帳號內沒有任何角色，取消設定Cookie'
        else:
            await db.users.add(User(id=user_id, cookie=cookie))
            log.info(f'[資訊][{user_id}]setCookie: Cookie設置成功')
            
            if len(accounts) == 1 and len(str(accounts[0].uid)) == 9:
                await self.setUID(user_id, accounts[0].uid)
                result = f'Cookie已設定完成，角色UID: {accounts[0].uid} 已保存！'
            else:
                result = f'Cookie已保存，你的Hoyolab帳號內共有{len(accounts)}名角色\n請使用 {getAppCommandMention("uid設定")} 指定要保存的原神角色'
        return result

    @generalErrorHandler
    async def getGameAccounts(self, user_id: int) -> Sequence[genshin.models.GenshinAccount]:
        """取得同一個Hoyolab帳號下，各伺服器的原神帳號

        ------
        Parameters
        user_id `int`: 使用者Discord ID
        ------
        Returns
        Sequence[genshin.models.GenshinAccount]`: 查詢結果
        """
        client = await self.__getGenshinClient(user_id, check_uid=False)
        return await client.genshin_accounts()
    
    async def setUID(self, user_id: int, uid: int) -> str:
        """保存指定的UID

        ------
        Parameters
        user_id `int`: 使用者Discord ID
        uid `int`: 欲保存的原神UID
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        log.info(f'[指令][{user_id}]setUID: uid={uid}')
        await db.users.update(user_id, uid=uid)
        return f'角色UID: {uid} 已設定完成'
    
    async def getUID(self, user_id: int) -> Union[int, None]:
        """取得指定使用者的UID"""
        user = await db.users.get(user_id)
        return user.uid

    @generalErrorHandler
    async def getRealtimeNote(self, user_id: int, *, schedule = False) -> genshin.models.Notes:
        """取得使用者的即時便箋
        
        ------
        Parameters
        user_id `int`: 使用者Discord ID
        schedule `bool`: 是否為排程檢查樹脂
        ------
        Returns
        `Notes`: 查詢結果
        """
        if not schedule:
            log.info(f'[指令][{user_id}]getRealtimeNote')
        client = await self.__getGenshinClient(user_id, update_using_time=(not schedule))
        return await client.get_genshin_notes(client.uid)

    @generalErrorHandler
    async def redeemCode(self, user_id: int, code: str) -> str:
        """為使用者使用指定的兌換碼

        ------
        Parameters
        user_id `int`: 使用者Discord ID
        code `str`: Hoyolab兌換碼
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        log.info(f'[指令][{user_id}]redeemCode: code={code}')
        client = await self.__getGenshinClient(user_id)
        await client.redeem_code(code, client.uid)
        return '兌換碼使用成功！'

    async def claimDailyReward(self, user_id: int, *, honkai: bool = False, schedule = False) -> str:
        """為使用者在Hoyolab簽到

        ------
        Parameters
        user_id `int`: 使用者Discord ID
        honkai `bool`: 是否也簽到崩壞3
        schedule `bool`: 是否為排程自動簽到
        ------
        Returns
        `str`: 回覆給使用者的訊息
        """
        if not schedule:
            log.info(f'[指令][{user_id}]claimDailyReward: honkai={honkai}')
        try:
            client = await self.__getGenshinClient(user_id, update_using_time=(not schedule))
        except Exception as e:
            return str(e)
        
        game_name = {genshin.Game.GENSHIN: '原神', genshin.Game.HONKAI: '崩壞3'}
        async def claimReward(game: genshin.Game, retry: int = 5) -> str:
            try:
                reward = await client.claim_daily_reward(game=game)
            except genshin.errors.AlreadyClaimed:
                return f'{game_name[game]}今日獎勵已經領過了！'
            except genshin.errors.InvalidCookies:
                return 'Cookie已失效，請從Hoyolab重新取得新Cookie'
            except genshin.errors.GenshinException as e:
                if e.retcode == -10002 and game == genshin.Game.HONKAI:
                    return '崩壞3簽到失敗，未查詢到角色資訊，請確認艦長是否已綁定新HoYoverse通行證'
                
                log.info(f'[例外][{user_id}]claimDailyReward: {game_name[game]}[retcode]{e.retcode} [例外內容]{e.original}')
                if retry > 0:
                    await asyncio.sleep(1)
                    return await claimReward(game, retry - 1)
                
                log.warning(f'[例外][{user_id}]claimDailyReward: {game_name[game]}[retcode]{e.retcode} [例外內容]{e.original}')
                sentry_sdk.capture_exception(e)
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
            if e.retcode != 2001:
                log.warning(f'[例外][{user_id}]claimDailyReward: Hoyolab[retcode]{e.retcode} [例外內容]{e.original}')
        except Exception as e:
            log.warning(f'[例外][{user_id}]claimDailyReward: Hoyolab[例外內容]{e}')
        
        return result

    @generalErrorHandler
    async def getSpiralAbyss(self, user_id: int, previous: bool = False) -> genshin.models.SpiralAbyss:
        """取得深境螺旋資訊

        ------
        Parameters
        user_id `int`: 使用者Discord ID
        previous `bool`: `True`查詢前一期的資訊、`False`查詢本期資訊
        ------
        Returns
        `SpiralAbyss`: 查詢結果
        """
        log.info(f'[指令][{user_id}]getSpiralAbyss: previous={previous}')
        client = await self.__getGenshinClient(user_id)
        # 為了刷新戰鬥數據榜，需要先對record card發出請求
        await client.get_record_cards()
        return await client.get_genshin_spiral_abyss(client.uid, previous=previous)

    @generalErrorHandler
    async def getTravelerDiary(self, user_id: int, month: int) -> discord.Embed:
        """取得使用者旅行者札記

        ------
        Parameters:
        user_id `int`: 使用者Discord ID
        month `int`: 欲查詢的月份
        ------
        Returns:
        `discord.Embed`: 查詢結果，已包裝成 discord 嵌入格式
        """
        log.info(f'[指令][{user_id}]getTravelerDiary: month={month}')
        client = await self.__getGenshinClient(user_id)
        diary = await client.get_diary(client.uid, month=month)
        
        d = diary.data
        result = discord.Embed(
            title=f'{diary.nickname} 的旅行者札記：{month}月',
            description=f'原石收入比上個月{"增加" if d.current_primogems >= d.last_primogems else "減少"}了{abs(d.primogems_rate)}%，'
                        f'摩拉收入比上個月{"增加" if d.current_mora >= d.last_mora else "減少"}了{abs(d.mora_rate)}%',
            color=0xfd96f4
        )
        result.add_field(
            name='當月共獲得',
            value=f'{emoji.items.primogem}原石：{d.current_primogems} ({round(d.current_primogems/160)}{emoji.items.intertwined_fate})\n'
                  f'{emoji.items.mora}摩拉：{format(d.current_mora, ",")}',
        )
        result.add_field(
            name='上個月獲得',
            value=f'{emoji.items.primogem}原石：{d.last_primogems} ({round(d.last_primogems/160)}{emoji.items.intertwined_fate})\n'
                  f'{emoji.items.mora}摩拉：{format(d.last_mora, ",")}'
        )
        result.add_field(name='\u200b', value='\u200b') # 空白行

        # 將札記原石組成平分成兩個field
        for i in range(0, 2):
            msg = ''
            length = len(d.categories)
            for j in range(round(length/2*i), round(length/2*(i+1))):
                msg += f'{d.categories[j].name[0:2]}：{d.categories[j].amount} ({d.categories[j].percentage}%)\n'
            result.add_field(name=f'原石收入組成 {i+1}', value=msg, inline=True)
        
        result.add_field(name='\u200b', value='\u200b') # 空白行
        return result

    @generalErrorHandler
    async def getRecordCard(self, user_id: int) -> Tuple[genshin.models.GenshinAccount, genshin.models.PartialGenshinUserStats]:
        """取得使用者記錄卡片(成就、活躍天數、角色數、神瞳、寶箱數...等等)

        ------
        Parameters:
        user_id `int`: 使用者Discord ID
        ------
        Returns:
        `(GenshinAccount, PartialGenshinUserStats)`: 查詢結果，包含角色伺服器資料與部分原神使用者資料
        """
        log.info(f'[指令][{user_id}]getRecordCard')
        client = await self.__getGenshinClient(user_id)
        accounts, userstats = await asyncio.gather(
            client.get_game_accounts(),
            client.get_partial_genshin_user(client.uid)
        )
        for account in accounts:
            if account.uid == client.uid:
                return (account, userstats)
        raise UserDataNotFound('找不到原神紀錄卡片')

    @generalErrorHandler
    async def getCharacters(self, user_id: int) -> Sequence[genshin.models.Character]:
        """取得使用者所有角色資料

        ------
        Parameters:
        user_id `int`: 使用者Discord ID
        ------
        Returns:
        `Sequence[Character]`: 查詢結果
        """
        log.info(f'[指令][{user_id}]getCharacters')
        client = await self.__getGenshinClient(user_id)
        return await client.get_genshin_characters(client.uid)

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
        get_char = lambda c: ' ' if len(c) == 0 else f'{c[0].name}：{c[0].value}'
        result.add_field(
            name=f'最深抵達：{abyss.max_floor}　戰鬥次數：{"👑 (12)" if abyss.total_stars == 36 and abyss.total_battles == 12 else abyss.total_battles}　★：{abyss.total_stars}',
            value=f'[最多擊破數] {get_char(abyss.ranks.most_kills)}\n'
                    f'[最強之一擊] {get_char(abyss.ranks.strongest_strike)}\n'
                    f'[受最多傷害] {get_char(abyss.ranks.most_damage_taken)}\n'
                    f'[Ｑ施放次數] {get_char(abyss.ranks.most_bursts_used)}\n'
                    f'[Ｅ施放次數] {get_char(abyss.ranks.most_skills_used)}',
            inline=False
        )
        return result
    
    def parseAbyssChamber(self, chamber: genshin.models.Chamber) -> str:
        """取得深淵某一間的角色名字
        
        ------
        Parameters
        chamber `Chamber`: 深淵某一間的資料
        ------
        Returns
        `str`: 角色名字組成的字串
        """
        chara_list = [[], []] # 分成上下半間
        for i, battle in enumerate(chamber.battles):
            for chara in battle.characters:
                chara_list[i].append(chara.name)
        return f'{".".join(chara_list[0])} ／\n{".".join(chara_list[1])}'
    
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

    async def parseNotes(self, notes: genshin.models.Notes, *, user: Optional[discord.User] = None, shortForm: bool = False) -> discord.Embed:
        """解析即時便箋的資料，將內容排版成discord嵌入格式回傳
        
        ------
        Parameters
        notes `Notes`: 即時便箋的資料
        user `discord.User`: Discord使用者
        shortForm `bool`: 設為`False`，完整顯示樹脂、寶錢、參數質變儀、派遣、每日、週本；設為`True`，只顯示樹脂、寶錢、參數質變儀
        ------
        Returns
        `discord.Embed`: discord嵌入格式
        """
        # 原粹樹脂
        resin_title = f'{emoji.notes.resin}當前原粹樹脂：{notes.current_resin}/{notes.max_resin}\n'
        if notes.current_resin >= notes.max_resin:
            recover_time = '已額滿！'
        else:
            day_msg = getDayOfWeek(notes.resin_recovery_time)
            recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
        resin_msg = f'{emoji.notes.resin}全部恢復時間：{recover_time}\n'
        # 每日、週本
        if not shortForm:
            resin_msg += f'{emoji.notes.commission}每日委託任務：剩餘 {notes.max_commissions - notes.completed_commissions} 個\n'
            resin_msg += f'{emoji.notes.enemies_of_note}週本樹脂減半：剩餘 {notes.remaining_resin_discounts} 次\n'
        # 洞天寶錢恢復時間
        resin_msg += f'{emoji.notes.realm_currency}當前洞天寶錢：{notes.current_realm_currency}/{notes.max_realm_currency}\n'
        if notes.max_realm_currency > 0:
            if notes.current_realm_currency >= notes.max_realm_currency:
                recover_time = '已額滿！'
            else:
                day_msg = getDayOfWeek(notes.realm_currency_recovery_time)
                recover_time = f'{day_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
            resin_msg += f'{emoji.notes.realm_currency}全部恢復時間：{recover_time}\n'
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
            resin_msg += f'{emoji.notes.transformer}參數質變儀　：{recover_time}\n'
        # 探索派遣剩餘時間
        exped_finished = 0
        exped_msg = ''
        for expedition in notes.expeditions:
            exped_msg += f'． {expedition.character.name}：'
            if expedition.finished:
                exped_finished += 1
                exped_msg += '已完成\n'
            else:
                day_msg = getDayOfWeek(expedition.completion_time)
                exped_msg += f'{day_msg} {expedition.completion_time.strftime("%H:%M")}\n'

        exped_title = f'{emoji.notes.expedition}探索派遣結果：{exped_finished}/{len(notes.expeditions)}\n'
 
        # 根據樹脂數量，以80作分界，embed顏色從綠色(0x28c828)漸變到黃色(0xc8c828)，再漸變到紅色(0xc82828)
        r = notes.current_resin
        color = 0x28c828 + 0x010000 * int(0xa0 * r / 80) if r < 80 else 0xc8c828 - 0x000100 * int(0xa0 * (r - 80) / 80)
        embed = discord.Embed(color=color)

        if (not shortForm) and (exped_msg != ''):
            embed.add_field(name=resin_title, value=resin_msg)
            embed.add_field(name=exped_title, value=exped_msg)
        else:
            embed.add_field(name=resin_title, value=(resin_msg + exped_title))

        if user != None:
            uid = str(await self.getUID(user.id))
            embed.set_author(name=f'{getServerName(uid[0])} {uid}', icon_url=user.display_avatar.url)
        return embed

    async def __getGenshinClient(self, user_id: int, *, check_uid = True, update_using_time: bool = True) -> genshin.Client:
        """設定並取得原神API的Client

        ------
        Parameters:
        user_id `int`: 使用者Discord ID
        check_uid `bool`: 是否檢查UID
        update_using_time `bool`: 是否更新使用者最後使用時間
        ------
        Returns:
        `genshin.Client`: 原神API的Client
        """
        user = await db.users.get(user_id)
        check, msg = await db.users.exist(user, check_uid=check_uid, update_using_time=update_using_time)
        if check == False:
            raise UserDataNotFound(msg)
        
        if user.uid != None and str(user.uid)[0] in ['1', '2', '5']:
            client = genshin.Client(region=genshin.Region.CHINESE, lang='zh-cn')
        else:
            client = genshin.Client(lang='zh-tw')
        client.set_cookies(user.cookie)
        client.default_game = genshin.Game.GENSHIN
        client.uid = user.uid
        return client

genshin_app = GenshinApp()