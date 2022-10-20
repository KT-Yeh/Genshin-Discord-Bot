from __future__ import annotations
import aiosqlite
from typing import Optional, Union, Tuple, List
from datetime import datetime
from utility.utils import getAppCommandMention

class User:
    id: int
    cookie: str
    uid: Optional[int]
    last_used_time: Optional[datetime]

    def __init__(self, id: int, cookie: str, *, uid: Optional[int] = None, last_used_time: Optional[Union[datetime, str]] = None):
        self.id = id
        self.cookie = cookie
        self.uid = uid
        self.last_used_time = datetime.fromisoformat(last_used_time) if isinstance(last_used_time, str) else last_used_time

    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> User:
        return cls(
            id=row['id'],
            cookie=row['cookie'],
            uid=row['uid'],
            last_used_time=row['last_used_time']
        )

class UsersTable:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        await self.db.execute('''CREATE TABLE IF NOT EXISTS users (
                id int NOT NULL PRIMARY KEY,
                cookie text NOT NULL,
                uid int,
                last_used_time text
            )''')
        await self.db.commit()

    async def add(self, user: User) -> None:
        await self.db.execute('INSERT OR REPLACE INTO users VALUES(?, ?, ?, ?)',
                [user.id, user.cookie, user.uid, user.last_used_time or datetime.now().isoformat()])
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[User]:
        async with self.db.execute('SELECT * FROM users WHERE id=?', [user_id]) as cursor:
            row = await cursor.fetchone()
            return User.fromRow(row) if row else None
    
    async def getAll(self) -> List[User]:
        async with self.db.execute('SELECT * FROM users') as cursor:
            rows = await cursor.fetchall()
            return [User.fromRow(row) for row in rows]
    
    async def remove(self, user_id: int) -> None:
        await self.db.execute('DELETE FROM users WHERE id=?', [user_id])
        await self.db.commit()

    async def update(self, user_id: int, *, cookie: Optional[str] = None, uid: Optional[int] = None, last_used_time: bool = False) -> None:
        if cookie:
            await self.db.execute('UPDATE users SET cookie=? WHERE id=?', [cookie, user_id])
        if uid:
            await self.db.execute('UPDATE users SET uid=? WHERE id=?', [uid, user_id])
        if last_used_time:
            await self.db.execute('UPDATE users SET last_used_time=? WHERE id=?',
                [datetime.now().isoformat(), user_id])
        await self.db.commit()

    async def exist(self, user: Optional[User], *, check_uid = True, update_using_time = True) -> Tuple[bool, Optional[str]]:
        """檢查使用者相關資料是否已保存在資料庫內
        
        ------
        Parameters
        user `database.User | None`: 使用者
        check_uid `bool`: 是否檢查UID
        update_using_time `bool`: 是否更新使用者最後使用時間
        ------
        Returns
        `bool`: `True`檢查成功，資料存在資料庫內；`False`檢查失敗，資料不存在資料庫內
        `str`: 檢查失敗時，回覆給使用者的訊息
        """
        if user == None:
            return False, f'找不到使用者，請先設定Cookie(使用 {getAppCommandMention("cookie設定")} 顯示說明)'
        elif check_uid and user.uid == None:
            return False, f'找不到角色UID，請先設定UID(使用 {getAppCommandMention("uid設定")} 來設定UID)'
        if update_using_time:
            await self.update(user.id, last_used_time=True)
        return True, None
