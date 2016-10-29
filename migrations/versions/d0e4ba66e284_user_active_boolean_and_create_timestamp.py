"""User active boolean and create timestamp

Revision ID: d0e4ba66e284
Revises: 1e745461efb2
Create Date: 2016-10-24 09:03:44.845505

"""

# revision identifiers, used by Alembic.
revision = 'd0e4ba66e284'
down_revision = '1e745461efb2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('active', sa.BOOLEAN(), nullable=True))
    op.add_column('user', sa.Column('create_timestamp', sa.TIMESTAMP(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'create_timestamp')
    op.drop_column('user', 'active')
    ### end Alembic commands ###
