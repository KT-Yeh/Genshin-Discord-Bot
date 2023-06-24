import datetime as dt
import os
import sys
import zlib

import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import database.legacy as legacy
from utility import LOG

from .app import Database as new_db
from .dataclass import spiral_abyss
from .legacy.database import db as old_db
from .models import *

sys.modules["data.database"] = legacy


async def migrate() -> None:
    """遷移舊版資料庫至新資料庫"""

    # Init
    old_path = "data/bot/bot_old.db"
    new_path = "data/bot/bot.db"
    os.rename(new_path, old_path)

    await old_db.create(old_path)
    new_db.engine = create_async_engine("sqlite+aiosqlite:///" + new_path)
    new_db.sessionmaker = async_sessionmaker(new_db.engine, expire_on_commit=False)
    await new_db.init()

    old_users = await old_db.users.getAll()
    LOG.Info(f"Total users: {len(old_users)}")

    # User
    LOG.Info("Migrating users table...")
    new_users: list[User] = []
    for _u in old_users:
        new_users.append(
            User(
                _u.id,
                _u.last_used_time,
                _u.cookie,
                _u.cookie,
                _u.cookie,
                _u.cookie,
                _u.uid,
                None,
                _u.uid_starrail,
            )
        )
    async with new_db.sessionmaker() as session:
        for new_user in new_users:
            session.add(new_user)
        await session.commit()

    # Schedule Daily Check-in
    LOG.Info("Migrating schedule_daily table...")
    new_schedule_dailys: list[ScheduleDailyCheckin] = []
    for _u in old_users:
        _d = await old_db.schedule_daily.get(_u.id)
        if _d is None:
            continue
        if _d.last_checkin_date:
            next_checkin_time = dt.datetime.combine(_d.last_checkin_date, dt.time(8, 0))
        else:
            next_checkin_time = dt.datetime.combine(dt.date.today(), dt.time(8, 0))
        new_schedule_dailys.append(
            ScheduleDailyCheckin(
                _d.id,
                _d.channel_id,
                _d.is_mention,
                next_checkin_time,
                _d.has_genshin,
                _d.has_honkai,
                _d.has_starrail,
            )
        )
    async with new_db.sessionmaker() as session:
        for new_schedule_daily in new_schedule_dailys:
            session.add(new_schedule_daily)
        await session.commit()

    # Schedule Resin
    LOG.Info("Migrating schedule_resin table...")
    new_schedule_resins: list[GenshinScheduleNotes] = []
    for _u in old_users:
        _r = await old_db.schedule_resin.get(_u.id)
        if _r is None:
            continue
        new_schedule_resins.append(
            GenshinScheduleNotes(
                _r.id,
                _r.channel_id,
                _r.next_check_time,
                _r.threshold_resin,
                _r.threshold_currency,
                _r.threshold_transformer,
                _r.threshold_expedition,
                _r.check_commission_time,
            )
        )
    async with new_db.sessionmaker() as session:
        for new_schedule_resin in new_schedule_resins:
            session.add(new_schedule_resin)
        await session.commit()

    # Spiral Abyss
    LOG.Info("Migrating spiral_abyss table...")
    new_abysses: list[GenshinSpiralAbyss] = []
    for _u in old_users:
        abysses = await old_db.spiral_abyss.get(_u.id)
        for _a in abysses:
            new_abyss = GenshinSpiralAbyss(_a.id, _a.season, _a.abyss)
            if _a.characters is not None:
                new_characters = [spiral_abyss.CharacterData.from_orm(c) for c in _a.characters]
                json_str = ",".join([c.json() for c in new_characters])
                json_str = "[" + json_str + "]"
                new_abyss._characters_raw_data = zlib.compress(json_str.encode("utf-8"), level=5)
            new_abysses.append(new_abyss)
    async with new_db.sessionmaker() as session:
        for abyss in new_abysses:
            session.add(abyss)
        await session.commit()

    # Genshin Showcase
    LOG.Info("Migrating showcase table...")
    uids = []
    datas = []
    async with old_db.db.execute("SELECT uid, data FROM showcase") as cursor:
        rows = await cursor.fetchall()
        for row in rows:
            uids.append(row["uid"])
            datas.append(row["data"])
    async with new_db.sessionmaker() as session:
        for uid, data in zip(uids, datas):
            stmt = sqlalchemy.insert(GenshinShowcase).values(uid=uid, _raw_data=data)
            try:
                await session.execute(stmt)
            except:
                pass
        await session.commit()

    # Starrail Showcase
    LOG.Info("Migrating starrail_showcase table...")
    uids = []
    datas = []
    async with old_db.db.execute("SELECT uid, data FROM starrail_showcase") as cursor:
        rows = await cursor.fetchall()
        for row in rows:
            uids.append(row["uid"])
            datas.append(row["data"])
    async with new_db.sessionmaker() as session:
        for uid, data in zip(uids, datas):
            stmt = sqlalchemy.insert(StarrailShowcase).values(uid=uid, _raw_data=data)
            try:
                await session.execute(stmt)
            except:
                pass
        await session.commit()

    # Close
    await old_db.close()
    await new_db.close()

    LOG.Info("Migration finished.")
