"""Add versioning to SQLAlchemy models

Revision ID: fad81a7cf95d
Revises: 256b12623621
Create Date: 2017-09-05 08:25:14.433484
Reviewed By: Joseph Neumann
Reviewed On: 2017-09-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fad81a7cf95d'
down_revision = '256b12623621'
branch_labels = None
depends_on = None


def upgrade():
    # address_version
    op.create_table('address_version',
                    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('address1', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('address2', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('city', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('state', sa.String(length=2), autoincrement=False, nullable=True),
                    sa.Column('zipcode', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('primary', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('active', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('patient_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('address_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('row_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
                    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
                    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
                    sa.Column('address1_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('address2_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('city_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('state_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('zipcode_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('primary_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('active_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('patient_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('user_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('created_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('updated_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('address_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('row_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.PrimaryKeyConstraint('id', 'transaction_id')
                    )
    op.create_index(op.f('ix_address_version_end_transaction_id'), 'address_version', ['end_transaction_id'],
                    unique=False)
    op.create_index(op.f('ix_address_version_operation_type'), 'address_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_address_version_patient_id'), 'address_version', ['patient_id'], unique=False)
    op.create_index(op.f('ix_address_version_transaction_id'), 'address_version', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_address_version_user_id'), 'address_version', ['user_id'], unique=False)
    op.create_index(op.f('ix_address_version_zipcode'), 'address_version', ['zipcode'], unique=False)

    # app_group_version
    op.create_table('app_group_version',
                    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('name', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('active', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('default', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
                    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
                    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
                    sa.Column('name_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('active_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('default_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('created_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('updated_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.PrimaryKeyConstraint('id', 'transaction_id')
                    )
    op.create_index(op.f('ix_app_group_version_end_transaction_id'), 'app_group_version', ['end_transaction_id'],
                    unique=False)
    op.create_index(op.f('ix_app_group_version_operation_type'), 'app_group_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_app_group_version_transaction_id'), 'app_group_version', ['transaction_id'], unique=False)

    # email_address_version
    op.create_table('email_address_version',
                    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('email', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('primary', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('active', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('patient_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('avatar_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('row_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
                    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
                    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
                    sa.Column('email_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('primary_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('active_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('patient_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('user_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('avatar_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('created_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('updated_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('row_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.PrimaryKeyConstraint('id', 'transaction_id')
                    )
    op.create_index(op.f('ix_email_address_version_email'), 'email_address_version', ['email'], unique=False)
    op.create_index(op.f('ix_email_address_version_end_transaction_id'), 'email_address_version',
                    ['end_transaction_id'], unique=False)
    op.create_index(op.f('ix_email_address_version_id'), 'email_address_version', ['id'], unique=False)
    op.create_index(op.f('ix_email_address_version_operation_type'), 'email_address_version', ['operation_type'],
                    unique=False)
    op.create_index(op.f('ix_email_address_version_patient_id'), 'email_address_version', ['patient_id'], unique=False)
    op.create_index(op.f('ix_email_address_version_row_hash'), 'email_address_version', ['row_hash'], unique=False)
    op.create_index(op.f('ix_email_address_version_transaction_id'), 'email_address_version', ['transaction_id'],
                    unique=False)
    op.create_index(op.f('ix_email_address_version_user_id'), 'email_address_version', ['user_id'], unique=False)

    # patient_version
    op.create_table('patient_version',
                    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('first_name', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('last_name', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('middle_name', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('prefix', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('suffix', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('sex', sa.String(), autoincrement=False, nullable=True),
                    sa.Column('dob', sa.Date(), autoincrement=False, nullable=True),
                    sa.Column('ssn', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('race', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('ethnicity', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('marital_status', sa.String(length=3), autoincrement=False, nullable=True),
                    sa.Column('deceased', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('deceased_date', sa.Date(), autoincrement=False, nullable=True),
                    sa.Column('multiple_birth', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('preferred_language', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('row_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
                    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
                    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
                    sa.Column('first_name_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('last_name_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('middle_name_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('prefix_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('suffix_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('sex_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('dob_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('ssn_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('race_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('ethnicity_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('marital_status_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('deceased_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('deceased_date_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('multiple_birth_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('preferred_language_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('created_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('updated_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('row_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.PrimaryKeyConstraint('id', 'transaction_id')
                    )
    op.create_index(op.f('ix_patient_version_dob'), 'patient_version', ['dob'], unique=False)
    op.create_index(op.f('ix_patient_version_end_transaction_id'), 'patient_version', ['end_transaction_id'],
                    unique=False)
    op.create_index(op.f('ix_patient_version_first_name'), 'patient_version', ['first_name'], unique=False)
    op.create_index(op.f('ix_patient_version_last_name'), 'patient_version', ['last_name'], unique=False)
    op.create_index(op.f('ix_patient_version_operation_type'), 'patient_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_patient_version_row_hash'), 'patient_version', ['row_hash'], unique=False)
    op.create_index(op.f('ix_patient_version_transaction_id'), 'patient_version', ['transaction_id'], unique=False)

    # phone_number_version
    op.create_table('phone_number_version',
                    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('number', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('type', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('active', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('primary', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('patient_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('row_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
                    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
                    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
                    sa.Column('number_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('type_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('active_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('primary_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('patient_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('user_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('created_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('updated_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('row_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.PrimaryKeyConstraint('id', 'transaction_id')
                    )
    op.create_index(op.f('ix_phone_number_version_end_transaction_id'), 'phone_number_version', ['end_transaction_id'],
                    unique=False)
    op.create_index(op.f('ix_phone_number_version_operation_type'), 'phone_number_version', ['operation_type'],
                    unique=False)
    op.create_index(op.f('ix_phone_number_version_patient_id'), 'phone_number_version', ['patient_id'], unique=False)
    op.create_index(op.f('ix_phone_number_version_row_hash'), 'phone_number_version', ['row_hash'], unique=False)
    op.create_index(op.f('ix_phone_number_version_transaction_id'), 'phone_number_version', ['transaction_id'],
                    unique=False)
    op.create_index(op.f('ix_phone_number_version_user_id'), 'phone_number_version', ['user_id'], unique=False)

    # app_group_version
    op.create_table('user_app_group_version',
                    sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('app_group_id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
                    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
                    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
                    sa.PrimaryKeyConstraint('user_id', 'app_group_id', 'transaction_id')
                    )
    op.create_index(op.f('ix_user_app_group_version_end_transaction_id'), 'user_app_group_version',
                    ['end_transaction_id'], unique=False)
    op.create_index(op.f('ix_user_app_group_version_operation_type'), 'user_app_group_version', ['operation_type'],
                    unique=False)
    op.create_index(op.f('ix_user_app_group_version_transaction_id'), 'user_app_group_version', ['transaction_id'],
                    unique=False)

    # user_version
    op.create_table('user_version',
                    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('username', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('role_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('first_name', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('last_name', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('dob', sa.Date(), autoincrement=False, nullable=True),
                    sa.Column('sex', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('description', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('confirmed', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('active', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('password_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('last_password_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('password_timestamp', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('last_seen', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('row_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
                    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
                    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
                    sa.Column('username_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('role_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('first_name_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('last_name_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('dob_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('sex_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('description_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('confirmed_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('active_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('password_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('last_password_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('password_timestamp_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('last_seen_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('created_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('updated_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('row_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.PrimaryKeyConstraint('id', 'transaction_id')
                    )
    op.create_index(op.f('ix_user_version_dob'), 'user_version', ['dob'], unique=False)
    op.create_index(op.f('ix_user_version_end_transaction_id'), 'user_version', ['end_transaction_id'], unique=False)
    op.create_index(op.f('ix_user_version_first_name'), 'user_version', ['first_name'], unique=False)
    op.create_index(op.f('ix_user_version_last_name'), 'user_version', ['last_name'], unique=False)
    op.create_index(op.f('ix_user_version_operation_type'), 'user_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_user_version_role_id'), 'user_version', ['role_id'], unique=False)
    op.create_index(op.f('ix_user_version_row_hash'), 'user_version', ['row_hash'], unique=False)
    op.create_index(op.f('ix_user_version_transaction_id'), 'user_version', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_user_version_username'), 'user_version', ['username'], unique=False)

    # transaction
    op.create_table('transaction',
                    sa.Column('issued_at', sa.DateTime(), nullable=True),
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('remote_addr', sa.String(length=50), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_transaction_user_id'), 'transaction', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_transaction_user_id'), table_name='transaction')
    op.drop_table('transaction')
    op.drop_index(op.f('ix_user_version_username'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_transaction_id'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_row_hash'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_role_id'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_operation_type'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_last_name'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_first_name'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_end_transaction_id'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_dob'), table_name='user_version')
    op.drop_table('user_version')
    op.drop_index(op.f('ix_user_app_group_version_transaction_id'), table_name='user_app_group_version')
    op.drop_index(op.f('ix_user_app_group_version_operation_type'), table_name='user_app_group_version')
    op.drop_index(op.f('ix_user_app_group_version_end_transaction_id'), table_name='user_app_group_version')
    op.drop_table('user_app_group_version')
    op.drop_index(op.f('ix_phone_number_version_user_id'), table_name='phone_number_version')
    op.drop_index(op.f('ix_phone_number_version_transaction_id'), table_name='phone_number_version')
    op.drop_index(op.f('ix_phone_number_version_row_hash'), table_name='phone_number_version')
    op.drop_index(op.f('ix_phone_number_version_patient_id'), table_name='phone_number_version')
    op.drop_index(op.f('ix_phone_number_version_operation_type'), table_name='phone_number_version')
    op.drop_index(op.f('ix_phone_number_version_end_transaction_id'), table_name='phone_number_version')
    op.drop_table('phone_number_version')
    op.drop_index(op.f('ix_patient_version_transaction_id'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_row_hash'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_operation_type'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_last_name'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_first_name'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_end_transaction_id'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_dob'), table_name='patient_version')
    op.drop_table('patient_version')
    op.drop_index(op.f('ix_email_address_version_user_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_transaction_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_row_hash'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_patient_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_operation_type'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_end_transaction_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_email'), table_name='email_address_version')
    op.drop_table('email_address_version')
    op.drop_index(op.f('ix_app_group_version_transaction_id'), table_name='app_group_version')
    op.drop_index(op.f('ix_app_group_version_operation_type'), table_name='app_group_version')
    op.drop_index(op.f('ix_app_group_version_end_transaction_id'), table_name='app_group_version')
    op.drop_table('app_group_version')
    op.drop_index(op.f('ix_address_version_zipcode'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_user_id'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_transaction_id'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_patient_id'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_operation_type'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_end_transaction_id'), table_name='address_version')
    op.drop_table('address_version')
