from datetime import datetime

import genshin

from utility.custom_log import LOG
from utility.utils import get_app_command_mention

from .app import Database
from .models import User


class Tool:
    @classmethod
    async def check_user(
        cls,
        user: User | None,
        *,
        check_cookie: bool = True,
        check_uid: bool = False,
        game: genshin.Game | None = None,
    ) -> tuple[bool, str]:
        """檢查使用者特定的資料是否已保存在資料庫內

        Parameters
        ------
        user: `database.User | None`
            資料庫使用者的資料類別
        check_cookie: `bool`
            是否檢查 Cookie
        check_uid: `bool`
            是否檢查 UID (需要設定 game 參數)
        game: `genshin.Game | None = None`
            要檢查的遊戲 (只有檢查 UID 會用到)

        Returns
        ------
        (`bool`, `str`):
            - `True` 檢查成功，資料存在資料庫內；`False` 檢查失敗，資料不存在資料庫內
            - 檢查失敗時，回傳錯誤訊息
        """
        if user is None:
            return False, f'找不到使用者，請先設定Cookie(使用 {get_app_command_mention("cookie設定")} 顯示說明)'

        if check_cookie is True and user.cookie_default is None:
            return False, f'找不到Cookie，請先設定Cookie(使用 {get_app_command_mention("cookie設定")} 顯示說明)'

        if check_uid is True and game is not None:
            if (
                (game == genshin.Game.GENSHIN and user.uid_genshin is None)
                or (game == genshin.Game.HONKAI and user.uid_honkai3rd is None)
                or (game == genshin.Game.STARRAIL and user.uid_starrail is None)
                or (game == genshin.Game.ZZZ and user.uid_zzz is None)
            ):
                return False, f'找不到角色UID，請先使用 {get_app_command_mention("uid設定")} 來設定UID)'

        return True, ""

    @classmethod
    async def remove_expired_user(cls, diff_days=60):
        """將超過天數未使用指令的使用者刪除

        Parameters
        ------
        diff_days: `int`
            刪除超過此天數未使用的使用者
        """
        now = datetime.now()
        count = 0
        users = await Database.select_all(User)
        for user in users:
            if user.last_used_time is None:
                continue
            interval = now - user.last_used_time
            if interval.days > diff_days:
                await Database.delete_instance(user)
                count += 1
        LOG.System(f"檢查過期使用者：{len(users)} 位使用者已檢查，已刪除 {count} 位過期使用者")
