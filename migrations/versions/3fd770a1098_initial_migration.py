"""initial migration

Revision ID: 3fd770a1098
Revises: None
Create Date: 2015-11-01 19:11:49.874574

"""

# revision identifiers, used by Alembic.
revision = '3fd770a1098'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('emial', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_users_emial'), 'users', ['emial'], unique=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_emial'), table_name='users')
    op.drop_column('users', 'emial')
    ### end Alembic commands ###