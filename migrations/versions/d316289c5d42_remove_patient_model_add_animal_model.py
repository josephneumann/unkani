"""Remove patient model add animal model

Revision ID: d316289c5d42
Revises: f0653dcbdcc6
Create Date: 2016-08-11 19:48:32.575267

"""

# revision identifiers, used by Alembic.
revision = 'd316289c5d42'
down_revision = 'f0653dcbdcc6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('animal',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('family_name', sa.String(length=128), nullable=True),
    sa.Column('dob', sa.Date(), nullable=True),
    sa.Column('species', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('patient')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('patient',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('first_name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('last_name', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('middle_initial', sa.VARCHAR(length=1), autoincrement=False, nullable=True),
    sa.Column('dob', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('gender', sa.VARCHAR(length=1), autoincrement=False, nullable=True),
    sa.Column('address1', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    sa.Column('address2', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    sa.Column('city', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('state', sa.VARCHAR(length=2), autoincrement=False, nullable=True),
    sa.Column('zip', sa.VARCHAR(length=9), autoincrement=False, nullable=True),
    sa.Column('ssn', sa.VARCHAR(length=9), autoincrement=False, nullable=True),
    sa.Column('phone_mobile', sa.VARCHAR(length=16), autoincrement=False, nullable=True),
    sa.Column('phone_home', sa.VARCHAR(length=16), autoincrement=False, nullable=True),
    sa.Column('email', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='patient_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='patient_pkey')
    )
    op.drop_table('animal')
    ### end Alembic commands ###
