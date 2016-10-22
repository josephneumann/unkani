"""Remove Animal Model

Revision ID: 1d66c16f620e
Revises: 7bc6255e6fad
Create Date: 2016-09-24 10:39:39.941753

"""

# revision identifiers, used by Alembic.
revision = '1d66c16f620e'
down_revision = '7bc6255e6fad'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('animal')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('animal',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('family_name', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('dob', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('species', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='animal_pkey')
    )
    ### end Alembic commands ###
