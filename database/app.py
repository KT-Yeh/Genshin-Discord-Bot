from typing import Sequence, TypeVar

import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.sql._typing import ColumnExpressionArgument

from .models import *

DatabaseModel = Base
T_DatabaseModel = TypeVar("T_DatabaseModel", bound=Base)


_engine = create_async_engine("sqlite+aiosqlite:///data/bot/bot.db")
_sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)


class Database:
    """資料庫方法類別，提供類別方法來操作資料庫，包含了：初始化、關閉、插入、選擇、刪除"""

    engine = _engine
    sessionmaker = _sessionmaker

    @classmethod
    async def init(cls) -> None:
        """初始化資料庫，在 bot 最初運行時需要呼叫一次"""
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @classmethod
    async def close(cls) -> None:
        """關閉資料庫，在 bot 關閉前需要呼叫一次"""
        await cls.engine.dispose()

    @classmethod
    async def insert_or_replace(cls, instance: DatabaseModel) -> None:
        """插入物件到資料庫，若已存在相同 Primary Key，則以新物件取代舊物件，
        Example: `Database.insert_or_replace(User(discord_id=123))`

        Paramaters:
        ------
        instance: `DatabaseModel`
            資料庫 Table (ORM) 的實例物件
        """
        async with cls.sessionmaker() as session:
            await session.merge(instance)
            await session.commit()

    @classmethod
    async def select_one(
        cls,
        table: type[T_DatabaseModel],
        whereclause: ColumnExpressionArgument[bool] | None = None,
    ) -> T_DatabaseModel | None:
        """指定資料庫 Table 與選擇條件，從資料庫選擇一項物件，
        Example: `Database.select_one(User, User.discord_id.is_(id))`

        Parameters
        ------
        table: `type[T_DatabaseModel]`
            要選擇的資料庫 Table (ORM) Class，Ex: `User`
        whereclause: `ColumnExpressionArgument[bool]` | `None`
            ORM Column 的 Where 選擇條件，Ex: `User.discord_id.is_(123456)`

        Returns
        ------
        `T_DatabaseModel` | `None`:
            根據參數所選擇出該 Table 符合條件的物件，若無任何符合則回傳 `None`
        """
        async with cls.sessionmaker() as session:
            stmt = sqlalchemy.select(table)
            if whereclause is not None:
                stmt = stmt.where(whereclause)
            result = await session.execute(stmt)
            return result.scalar()

    @classmethod
    async def select_all(
        cls,
        table: type[T_DatabaseModel],
        whereclause: ColumnExpressionArgument[bool] | None = None,
    ) -> Sequence[T_DatabaseModel]:
        """指定資料庫 Table 與選擇條件，從資料庫選擇符合條件的全部物件

        Parameters
        ------
        table: `type[T_DatabaseModel]`
            要選擇的資料庫 Table (ORM) Class，Ex: `GenshinSpiralAbyss`
        whereclause: `ColumnExpressionArgument[bool]` | `None`
            - ORM Column 的 Where 選擇條件，若為 `None` 則表示選擇該 Table 內全部資料
            - Ex: `GenshinSpiralAbyss.discord_id.is_(123456)`

        Returns
        ------
        `Sequence[T_DatabaseModel]`:
            根據參數所選擇出該 Table 符合條件的全部物件
        """
        async with cls.sessionmaker() as session:
            stmt = sqlalchemy.select(table)
            if whereclause is not None:
                stmt = stmt.where(whereclause)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def delete_instance(cls, instance: DatabaseModel) -> None:
        """從資料庫內刪除該物件，使用方式是先使用 `select_one` 或 `select_all` 方法取得物件實例後，傳入本方法進行刪除

        Paramaters:
        ------
        instance: `DatabaseModel`
            資料庫 Table (ORM) 的實例物件
        """
        async with cls.sessionmaker() as session:
            await session.delete(instance)
            await session.commit()

    @classmethod
    async def delete(
        cls, table: type[T_DatabaseModel], whereclause: ColumnExpressionArgument[bool]
    ) -> None:
        """指定資料庫 Table 與 where 條件，從資料庫刪除符合條件的物件，
        Example: `Database.delete(User, User.discord_id.is_(id))`

        Parameters
        ------
        table: `type[T_DatabaseModel]`
            要選擇的資料庫 Table (ORM) Class，Ex: `User`
        whereclause: `ColumnExpressionArgument[bool]` | `None`
            ORM Column 的 Where 選擇條件，Ex: `User.discord_id.is_(123456)`
        """
        instances = await cls.select_all(table, whereclause)
        for instance in instances:
            await cls.delete_instance(instance)

    @classmethod
    async def delete_all(cls, discord_id: int) -> None:
        """指定使用者 discord_id，刪除此使用者在資料庫內的所有資料

        Parameters
        ------
        discord_id: `int`
            使用者 Discord ID
        """
        user = await cls.select_one(User, User.discord_id.is_(discord_id))
        if user is None:
            return
        await cls.delete(User, User.discord_id.is_(discord_id))
        await cls.delete(ScheduleDailyCheckin, ScheduleDailyCheckin.discord_id.is_(discord_id))
        await cls.delete(GenshinScheduleNotes, GenshinScheduleNotes.discord_id.is_(discord_id))
        await cls.delete(GenshinSpiralAbyss, GenshinSpiralAbyss.discord_id.is_(discord_id))
        await cls.delete(GenshinShowcase, GenshinShowcase.uid.is_(user.uid_genshin))
        await cls.delete(StarrailShowcase, StarrailShowcase.uid.is_(user.uid_starrail))
        await cls.delete(User, User.discord_id.is_(discord_id))
