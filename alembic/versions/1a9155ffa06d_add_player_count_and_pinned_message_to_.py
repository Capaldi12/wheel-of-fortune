"""Add player count and pinned message to Round

Revision ID: 1a9155ffa06d
Revises: 1b1571ab623c
Create Date: 2023-03-14 15:12:49.265016

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a9155ffa06d'
down_revision = '1b1571ab623c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('round', sa.Column('player_count', sa.Integer(), nullable=True))
    op.execute("UPDATE round SET player_count = 3")
    op.alter_column('round', 'player_count', nullable=False)

    op.add_column('round', sa.Column('pinned_message', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('round', 'pinned_message')
    op.drop_column('round', 'player_count')
    # ### end Alembic commands ###