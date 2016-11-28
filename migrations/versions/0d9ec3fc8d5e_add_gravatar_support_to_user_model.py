"""Add gravatar support to user model

Revision ID: 0d9ec3fc8d5e
Revises: 52a9e98b3105
Create Date: 2016-11-27 20:00:26.965859

"""

# revision identifiers, used by Alembic.
revision = '0d9ec3fc8d5e'
down_revision = '52a9e98b3105'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('avatar_hash', sa.String(length=128), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'avatar_hash')
    ### end Alembic commands ###
