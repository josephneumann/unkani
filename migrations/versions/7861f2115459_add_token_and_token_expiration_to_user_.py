"""Add token and token_expiration to User model

Revision ID: 7861f2115459
Revises: b5792c4cd54a
Create Date: 2018-02-10 14:22:42.313423

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7861f2115459'
down_revision = 'b5792c4cd54a'
branch_labels = None
depends_on = None


def upgrade():
    # Add token and token_expiration columns and indexes
    op.add_column('user', sa.Column('token', sa.String(length=32), nullable=True))
    op.add_column('user', sa.Column('token_expiration', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_user_token'), 'user', ['token'], unique=True)
    op.add_column('user_version', sa.Column('token', sa.String(length=32), autoincrement=False, nullable=True))
    op.add_column('user_version', sa.Column('token_expiration', sa.DateTime(), autoincrement=False, nullable=True))
    op.add_column('user_version', sa.Column('token_expiration_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('user_version', sa.Column('token_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.create_index(op.f('ix_user_version_token'), 'user_version', ['token'], unique=False)


def downgrade():
    # Drop token and token_expiration columns and indexes
    op.drop_index(op.f('ix_user_version_token'), table_name='user_version')
    op.drop_column('user_version', 'token_mod')
    op.drop_column('user_version', 'token_expiration_mod')
    op.drop_column('user_version', 'token_expiration')
    op.drop_column('user_version', 'token')
    op.drop_index(op.f('ix_user_token'), table_name='user')
    op.drop_column('user', 'token_expiration')
    op.drop_column('user', 'token')
