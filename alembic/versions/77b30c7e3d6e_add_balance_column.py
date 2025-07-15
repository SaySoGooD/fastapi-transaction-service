"""описание_изменения

Revision ID: 77b30c7e3d6e
Revises: dc6c941683bc
Create Date: 2025-07-13 15:58:15.235313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77b30c7e3d6e'
down_revision: Union[str, Sequence[str], None] = 'dc6c941683bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
