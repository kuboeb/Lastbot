"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Создаем все таблицы через SQLAlchemy models
    # База данных будет создана автоматически при первом запуске
    pass

def downgrade() -> None:
    # Удаление таблиц
    pass
