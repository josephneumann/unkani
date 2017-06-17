"""Initial unkani model migration for app

Revision ID: 70571daae080
Revises: 
Create Date: 2017-05-25 08:37:58.315072
Reviewer: Joe Neumann
Review Passed: 05/25/2017
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70571daae080'
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

    op.create_index(op.f('ix_patient_dob'), 'patient', ['dob'], unique=False)
    op.create_index(op.f('ix_patient_first_name'), 'patient', ['first_name'], unique=False)
    op.create_index(op.f('ix_patient_last_name'), 'patient', ['last_name'], unique=False)
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_level'), 'role', ['level'], unique=False)
    op.create_index(op.f('ix_role_name'), 'role', ['name'], unique=True)

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
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('first_name', sa.Text(), nullable=True),
    sa.Column('last_name', sa.Text(), nullable=True),
    sa.Column('dob', sa.Date(), nullable=True),
    sa.Column('sex', sa.String(length=1), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('password_hash', sa.Text(), nullable=True),
    sa.Column('last_password_hash', sa.Text(), nullable=True),
    sa.Column('password_timestamp', sa.DateTime(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('row_hash', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_dob'), 'user', ['dob'], unique=False)
    op.create_index(op.f('ix_user_first_name'), 'user', ['first_name'], unique=False)
    op.create_index(op.f('ix_user_last_name'), 'user', ['last_name'], unique=False)
    op.create_index(op.f('ix_user_role_id'), 'user', ['role_id'], unique=False)
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
    op.create_index(op.f('ix_address_patient_id'), 'address', ['patient_id'], unique=False)
    op.create_index(op.f('ix_address_user_id'), 'address', ['user_id'], unique=False)
    op.create_index(op.f('ix_address_zipcode'), 'address', ['zipcode'], unique=False)

    op.create_table('email_address',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.Text(), nullable=True),
    sa.Column('primary', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('avatar_hash', sa.Text(), nullable=True),
    sa.Column('row_hash', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_address_email'), 'email_address', ['email'], unique=False)
    op.create_index(op.f('ix_email_address_id'), 'email_address', ['id'], unique=False)
    op.create_index(op.f('ix_email_address_patient_id'), 'email_address', ['patient_id'], unique=False)
    op.create_index(op.f('ix_email_address_user_id'), 'email_address', ['user_id'], unique=False)

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
    op.create_index(op.f('ix_phone_number_patient_id'), 'phone_number', ['patient_id'], unique=False)
    op.create_index(op.f('ix_phone_number_user_id'), 'phone_number', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_phone_number_user_id'), table_name='phone_number')
    op.drop_index(op.f('ix_phone_number_patient_id'), table_name='phone_number')
    op.drop_table('phone_number')
    op.drop_index(op.f('ix_email_address_user_id'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_patient_id'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_id'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_email'), table_name='email_address')
    op.drop_table('email_address')
    op.drop_index(op.f('ix_address_zipcode'), table_name='address')
    op.drop_index(op.f('ix_address_user_id'), table_name='address')
    op.drop_index(op.f('ix_address_patient_id'), table_name='address')
    op.drop_table('address')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_role_id'), table_name='user')
    op.drop_index(op.f('ix_user_last_name'), table_name='user')
    op.drop_index(op.f('ix_user_first_name'), table_name='user')
    op.drop_index(op.f('ix_user_dob'), table_name='user')
    op.drop_table('user')
    op.drop_table('role_app_permission')
    op.drop_index(op.f('ix_role_name'), table_name='role')
    op.drop_index(op.f('ix_role_level'), table_name='role')
    op.drop_table('role')
    op.drop_index(op.f('ix_patient_last_name'), table_name='patient')
    op.drop_index(op.f('ix_patient_first_name'), table_name='patient')
    op.drop_index(op.f('ix_patient_dob'), table_name='patient')
    op.drop_table('patient')
    op.drop_table('app_permission')
