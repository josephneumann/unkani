"""Initial migration of Unkani DB

Revision ID: 30eb77cfd650
Revises: 
Create Date: 2017-05-11 18:51:24.807027

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30eb77cfd650'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('app_permission',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('role_app_permission',
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('app_permission_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['app_permission_id'], ['app_permission.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], )
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.Text(), nullable=True),
    sa.Column('email', sa.Text(), nullable=True),
    sa.Column('last_email', sa.Text(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('password_hash', sa.Text(), nullable=True),
    sa.Column('last_password_hash', sa.Text(), nullable=True),
    sa.Column('password_timestamp', sa.TIMESTAMP(), nullable=True),
    sa.Column('first_name', sa.Text(), nullable=True),
    sa.Column('last_name', sa.Text(), nullable=True),
    sa.Column('dob', sa.Date(), nullable=True),
    sa.Column('phone', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('active', sa.BOOLEAN(), nullable=True),
    sa.Column('create_timestamp', sa.TIMESTAMP(), nullable=True),
    sa.Column('last_seen', sa.TIMESTAMP(), nullable=True),
    sa.Column('avatar_hash', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_last_email'), 'user', ['last_email'])
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_last_email'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('role_app_permission')
    op.drop_table('role')
    op.drop_table('app_permission')
