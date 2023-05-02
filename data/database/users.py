from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple, Union

import aiosqlite

from utility.utils import get_app_command_mention


class User:
    """機器人使用者 Table 的資料類別

    Attributes
    -----
    id: `int`
        使用者 Discord ID
    cookie: `str`
        Hoyolab 或米游社網頁的 Cookie
    uid: `Optional[int]`
        使用者原神角色的 UID
    uid_starrail: `Optional[int]`
        使用者星穹鐵道角色的 UID
    last_used_time: `Optional[datetime]`
        使用者最後一次使用機器人指令的時間
    invalid_cookie: `int`
        用來記錄使用者的 Cookie 是否無效，0 表示正常，大於 0 表示錯誤的次數
    """

    id: int
    cookie: str
    uid: Optional[int]
    uid_starrail: Optional[int]
    last_used_time: Optional[datetime]
    invalid_cookie: int

    def __init__(
        self,
        id: int,
        cookie: str = "",
        *,
        uid: Optional[int] = None,
        uid_starrail: Optional[int] = None,
        last_used_time: Optional[Union[datetime, str]] = None,
        invalid_cookie: int = 0,
    ):
        self.id = id
        self.cookie = cookie
        self.uid = uid
        self.uid_starrail = uid_starrail
        self.last_used_time = (
            datetime.fromisoformat(last_used_time)
            if isinstance(last_used_time, str)
            else last_used_time
        )
        self.invalid_cookie = invalid_cookie

    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> User:
        return cls(
            id=row["id"],
            cookie=row["cookie"],
            uid=row["uid"],
            uid_starrail=row["uid_starrail"],
            last_used_time=row["last_used_time"],
            invalid_cookie=row["invalid_cookie"],
        )


class UsersTable:
    """機器人使用者資料的 Table"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        """在資料庫新建 Table"""
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id int NOT NULL PRIMARY KEY,
                cookie text NOT NULL,
                uid int,
                uid_starrail int,
                last_used_time text,
                invalid_cookie int NOT NULL
            )"""
        )
        cursor = await self.db.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in await cursor.fetchall()]
        if "invalid_cookie" not in columns:
            await self.db.execute(
                "ALTER TABLE users ADD COLUMN invalid_cookie int NOT NULL DEFAULT '0'"
            )
        if "uid_starrail" not in columns:
            await self.db.execute("ALTER TABLE users ADD COLUMN uid_starrail int")
        await self.db.commit()

    async def add(self, user: User) -> None:
        """新增使用者到 Table"""
        await self.db.execute(
            "INSERT OR REPLACE INTO users "
            "(id, cookie, uid, uid_starrail, last_used_time, invalid_cookie) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                user.id,
                user.cookie,
                user.uid,
                user.uid_starrail,
                user.last_used_time or datetime.now().isoformat(),
                user.invalid_cookie,
            ],
        )
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[User]:
        """取得指定使用者的資料"""
        async with self.db.execute("SELECT * FROM users WHERE id=?", [user_id]) as cursor:
            row = await cursor.fetchone()
            return User.fromRow(row) if row else None

    async def getAll(self) -> List[User]:
        """取得所有使用者的資料"""
        async with self.db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [User.fromRow(row) for row in rows]

    async def remove(self, user_id: int) -> None:
        """從 Table 移除指定的使用者"""
        await self.db.execute("DELETE FROM users WHERE id=?", [user_id])
        await self.db.commit()

    async def update(
        self,
        user_id: int,
        *,
        cookie: Optional[str] = None,
        uid: Optional[int] = None,
        uid_starrail: Optional[int] = None,
        last_used_time: bool = False,
        invalid_cookie: bool = False,
    ) -> None:
        """更新指定使用者的 Column 資料"""
        if cookie:
            await self.db.execute("UPDATE users SET cookie=? WHERE id=?", [cookie, user_id])
        if uid:
            await self.db.execute("UPDATE users SET uid=? WHERE id=?", [uid, user_id])
        if uid_starrail:
            await self.db.execute(
                "UPDATE users SET uid_starrail=? WHERE id=?", [uid_starrail, user_id]
            )
        if last_used_time:
            await self.db.execute(
                "UPDATE users SET last_used_time=? WHERE id=?",
                [datetime.now().isoformat(), user_id],
            )
        if invalid_cookie:
            await self.db.execute(
                "UPDATE users SET invalid_cookie=invalid_cookie+1 WHERE id=?", [user_id]
            )
        await self.db.commit()

    async def exist(
        self,
        user: Optional[User],
        *,
        check_cookie=True,
        check_uid=True,
    ) -> Tuple[bool, Optional[str]]:
        """檢查使用者特定的資料是否已保存在資料庫內

        Parameters
        ------
        user: `database.User | None`
            資料庫使用者 Table 的資料類別
        check_cookie: `bool`
            是否檢查Cookie
        check_uid: `bool`
            是否檢查UID

        Returns
        ------
        `(bool, str | None)`
            - `True` 檢查成功，資料存在資料庫內；`False` 檢查失敗，資料不存在資料庫內
            - 檢查失敗時，回覆給使用者的訊息
        """
        if user is None:
            return False, f'找不到使用者，請先設定Cookie(使用 {get_app_command_mention("cookie設定")} 顯示說明)'
        if check_cookie and len(user.cookie) == 0:
            return False, f'找不到Cookie，請先設定Cookie(使用 {get_app_command_mention("cookie設定")} 顯示說明)'
        if check_cookie and user.invalid_cookie > 0:
            await self.update(user.id, invalid_cookie=True)
            return False, "Cookie已失效，請從Hoyolab重新取得新Cookie"
        if check_uid and user.uid is None:
            return False, f'找不到原神角色UID，請先使用 {get_app_command_mention("uid設定")} 來設定UID)'
        await self.update(user.id, last_used_time=True)
        return True, None
