"""修正星穹鐵道忘卻之庭歷史資料

Revision ID: 23942a12b637
Revises: 2ba9f9c494d7
Create Date: 2024-02-16 20:52:09.745027

"""

import json
import zlib

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "23942a12b637"
down_revision = "2ba9f9c494d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    result = connection.execute(
        sa.text("SELECT discord_id, season, _raw_data FROM starrail_forgotten_hall")
    )
    for row in result:
        # 解壓縮 _raw_data 欄位
        raw_data = zlib.decompress(row[2]).decode("utf-8")
        data = json.loads(raw_data)

        for floor in data["floors"]:
            # 處理快速通關
            if "is_fast" not in floor:
                if floor["star_num"] > 0 and len(floor["node_1"]["avatars"]) == 0:
                    floor["is_fast"] = True
                else:
                    floor["is_fast"] = False
            if "id" not in floor:
                floor["id"] = 0

        # 壓縮處理後的資料
        compressed_data = zlib.compress(json.dumps(data).encode("utf-8"), level=5)

        # 更新資料庫中的資料
        update_stmt = sa.text(
            "UPDATE starrail_forgotten_hall SET _raw_data = :raw_data "
            "WHERE discord_id = :discord_id AND season = :season"
        ).bindparams(
            raw_data=compressed_data,
            discord_id=row[0],
            season=row[1],
        )
        connection.execute(update_stmt)


def downgrade() -> None:
    pass
