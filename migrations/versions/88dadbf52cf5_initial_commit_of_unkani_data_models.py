"""initial commit of unkani data models

Revision ID: 88dadbf52cf5
Revises: 
Create Date: 2017-05-20 21:34:01.610838

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88dadbf52cf5'
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
    op.create_table('patient',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.Text(), nullable=True),
    sa.Column('last_name', sa.Text(), nullable=True),
    sa.Column('middle_name', sa.Text(), nullable=True),
    sa.Column('suffix', sa.Text(), nullable=True),
    sa.Column('sex', sa.String(length=1), nullable=True),
    sa.Column('dob', sa.Date(), nullable=True),
    sa.Column('ssn', sa.Text(), nullable=True),
    sa.Column('race', sa.Text(), nullable=True),
    sa.Column('ethnicity', sa.Text(), nullable=True),
    sa.Column('marital_status', sa.String(length=1), nullable=True),
    sa.Column('deceased', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('row_hash', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
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
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('app_permission_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['app_permission_id'], ['app_permission.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.PrimaryKeyConstraint('role_id', 'app_permission_id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.Text(), nullable=True),
    sa.Column('email', sa.Text(), nullable=True),
    sa.Column('last_email', sa.Text(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('password_hash', sa.Text(), nullable=True),
    sa.Column('last_password_hash', sa.Text(), nullable=True),
    sa.Column('password_timestamp', sa.DateTime(), nullable=True),
    sa.Column('first_name', sa.Text(), nullable=True),
    sa.Column('last_name', sa.Text(), nullable=True),
    sa.Column('dob', sa.Date(), nullable=True),
    sa.Column('phone', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('avatar_hash', sa.Text(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('row_hash', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_last_email'), 'user', ['last_email'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('address',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('address1', sa.Text(), nullable=True),
    sa.Column('address2', sa.Text(), nullable=True),
    sa.Column('city', sa.Text(), nullable=True),
    sa.Column('state', sa.String(length=2), nullable=True),
    sa.Column('zipcode', sa.Text(), nullable=True),
    sa.Column('primary', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('row_hash', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('email_address',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.Text(), nullable=True),
    sa.Column('primary', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('row_hash', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_address_email'), 'email_address', ['email'], unique=True)
    op.create_index(op.f('ix_email_address_id'), 'email_address', ['id'], unique=False)
    op.create_table('phone_number',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('number', sa.Text(), nullable=False),
    sa.Column('type', sa.String(length=1), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('row_hash', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('phone_number')
    op.drop_index(op.f('ix_email_address_id'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_email'), table_name='email_address')
    op.drop_table('email_address')
    op.drop_table('address')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_last_email'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('role_app_permission')
    op.drop_table('role')
    op.drop_table('patient')
    op.drop_table('app_permission')
