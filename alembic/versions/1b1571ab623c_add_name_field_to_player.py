"""Add name field to player

Revision ID: 1b1571ab623c
Revises: aef1b84e35ff
Create Date: 2023-03-12 23:25:35.426296

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b1571ab623c'
down_revision = 'aef1b84e35ff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('player', sa.Column('name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('player', 'name')
    # ### end Alembic commands ###
