"""清空星穹鐵道展示櫃資料

Revision ID: 2ba9f9c494d7
Revises: 5d2af112b1f5
Create Date: 2024-02-13 14:59:36.015068

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2ba9f9c494d7"
down_revision = "5d2af112b1f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM starrail_showcases")


def downgrade() -> None:
    pass
