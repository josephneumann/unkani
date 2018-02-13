"""initial model migration

Revision ID: 43b2beea5ab3
Revises: 
Create Date: 2018-02-13 14:00:08.690298

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '43b2beea5ab3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('address_version',
                    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('address1', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('address2', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('city', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('state', sa.String(length=2), autoincrement=False, nullable=True),
                    sa.Column('zipcode', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('district', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('country', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('primary', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('is_postal', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('is_physical', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('use', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('active', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('patient_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=True),
                    sa.Column('start_date', sa.Date(), autoincrement=False, nullable=True),
                    sa.Column('end_date', sa.Date(), autoincrement=False, nullable=True),
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
                    sa.Column('district_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('country_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('primary_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('is_postal_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('is_physical_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('use_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('active_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('patient_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('user_id_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('start_date_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('end_date_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
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
    op.create_table('app_group',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=True),
                    sa.Column('default', sa.Boolean(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name')
                    )
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
    op.create_table('app_permission',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name')
                    )
    op.create_table('codesystem',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('resource_id', sa.Text(), nullable=False),
                    sa.Column('version', sa.Text(), nullable=True),
                    sa.Column('url', sa.Text(), nullable=True),
                    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('data_hash', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('resource_id')
                    )
    op.create_index(op.f('ix_codesystem_data_hash'), 'codesystem', ['data_hash'], unique=False)
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
    op.create_table('organization',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('parent_id', sa.Integer(), nullable=True),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.Column('type', sa.Text(), nullable=True),
                    sa.Column('default', sa.Boolean(), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['parent_id'], ['organization.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_organization_parent_id'), 'organization', ['parent_id'], unique=False)
    op.create_index(op.f('ix_organization_type'), 'organization', ['type'], unique=False)
    op.create_table('patient',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('first_name', sa.Text(), nullable=True),
                    sa.Column('last_name', sa.Text(), nullable=True),
                    sa.Column('middle_name', sa.Text(), nullable=True),
                    sa.Column('prefix', sa.Text(), nullable=True),
                    sa.Column('suffix', sa.Text(), nullable=True),
                    sa.Column('sex', sa.String(), nullable=True),
                    sa.Column('dob', sa.Date(), nullable=True),
                    sa.Column('ssn', sa.Text(), nullable=True),
                    sa.Column('race', sa.Text(), nullable=True),
                    sa.Column('ethnicity', sa.Text(), nullable=True),
                    sa.Column('marital_status', sa.String(length=3), nullable=True),
                    sa.Column('deceased', sa.Boolean(), nullable=True),
                    sa.Column('deceased_date', sa.Date(), nullable=True),
                    sa.Column('multiple_birth', sa.Boolean(), nullable=True),
                    sa.Column('preferred_language', sa.Text(), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('row_hash', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('uuid')
                    )
    op.create_index(op.f('ix_patient_dob'), 'patient', ['dob'], unique=False)
    op.create_index(op.f('ix_patient_first_name'), 'patient', ['first_name'], unique=False)
    op.create_index(op.f('ix_patient_id'), 'patient', ['id'], unique=False)
    op.create_index(op.f('ix_patient_last_name'), 'patient', ['last_name'], unique=False)
    op.create_index(op.f('ix_patient_row_hash'), 'patient', ['row_hash'], unique=False)
    op.create_table('patient_version',
                    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('uuid', postgresql.UUID(as_uuid=True), autoincrement=False, nullable=True),
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
                    sa.Column('active', sa.Boolean(), autoincrement=False, nullable=True),
                    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=True),
                    sa.Column('row_hash', sa.Text(), autoincrement=False, nullable=True),
                    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
                    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
                    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
                    sa.Column('uuid_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
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
                    sa.Column('active_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('created_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('updated_at_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('row_hash_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.PrimaryKeyConstraint('id', 'transaction_id')
                    )
    op.create_index(op.f('ix_patient_version_dob'), 'patient_version', ['dob'], unique=False)
    op.create_index(op.f('ix_patient_version_end_transaction_id'), 'patient_version', ['end_transaction_id'],
                    unique=False)
    op.create_index(op.f('ix_patient_version_first_name'), 'patient_version', ['first_name'], unique=False)
    op.create_index(op.f('ix_patient_version_id'), 'patient_version', ['id'], unique=False)
    op.create_index(op.f('ix_patient_version_last_name'), 'patient_version', ['last_name'], unique=False)
    op.create_index(op.f('ix_patient_version_operation_type'), 'patient_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_patient_version_row_hash'), 'patient_version', ['row_hash'], unique=False)
    op.create_index(op.f('ix_patient_version_transaction_id'), 'patient_version', ['transaction_id'], unique=False)
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
    op.create_table('role',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=True),
                    sa.Column('default', sa.Boolean(), nullable=True),
                    sa.Column('level', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_role_level'), 'role', ['level'], unique=False)
    op.create_index(op.f('ix_role_name'), 'role', ['name'], unique=True)
    op.create_table('source_data',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('method', sa.Text(), nullable=True),
                    sa.Column('route', sa.Text(), nullable=True),
                    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                    sa.Column('payload_hash', sa.Text(), nullable=True),
                    sa.Column('response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                    sa.Column('status_code', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_source_data_method'), 'source_data', ['method'], unique=False)
    op.create_index(op.f('ix_source_data_payload_hash'), 'source_data', ['payload_hash'], unique=False)
    op.create_index(op.f('ix_source_data_route'), 'source_data', ['route'], unique=False)
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
                    sa.Column('token', sa.String(length=32), autoincrement=False, nullable=True),
                    sa.Column('token_expiration', sa.DateTime(), autoincrement=False, nullable=True),
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
                    sa.Column('token_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
                    sa.Column('token_expiration_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False),
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
    op.create_index(op.f('ix_user_version_token'), 'user_version', ['token'], unique=False)
    op.create_index(op.f('ix_user_version_transaction_id'), 'user_version', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_user_version_username'), 'user_version', ['username'], unique=False)
    op.create_table('valueset',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('resource_id', sa.Text(), nullable=False),
                    sa.Column('version', sa.Text(), nullable=True),
                    sa.Column('url', sa.Text(), nullable=True),
                    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                    sa.Column('data_hash', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('resource_id')
                    )
    op.create_index(op.f('ix_valueset_data_hash'), 'valueset', ['data_hash'], unique=False)
    op.create_table('role_app_permission',
                    sa.Column('role_id', sa.Integer(), nullable=False),
                    sa.Column('app_permission_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['app_permission_id'], ['app_permission.id'], ),
                    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
                    sa.PrimaryKeyConstraint('role_id', 'app_permission_id')
                    )
    op.create_table('source_data_codesystem',
                    sa.Column('source_data_id', sa.Integer(), nullable=False),
                    sa.Column('codesystem_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['codesystem_id'], ['codesystem.id'], ),
                    sa.ForeignKeyConstraint(['source_data_id'], ['source_data.id'], ),
                    sa.PrimaryKeyConstraint('source_data_id', 'codesystem_id')
                    )
    op.create_table('source_data_valueset',
                    sa.Column('source_data_id', sa.Integer(), nullable=False),
                    sa.Column('valueset_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['source_data_id'], ['source_data.id'], ),
                    sa.ForeignKeyConstraint(['valueset_id'], ['valueset.id'], ),
                    sa.PrimaryKeyConstraint('source_data_id', 'valueset_id')
                    )
    op.create_table('user',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('username', sa.Text(), nullable=True),
                    sa.Column('role_id', sa.Integer(), nullable=True),
                    sa.Column('first_name', sa.Text(), nullable=True),
                    sa.Column('last_name', sa.Text(), nullable=True),
                    sa.Column('dob', sa.Date(), nullable=True),
                    sa.Column('sex', sa.Text(), nullable=True),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('confirmed', sa.Boolean(), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=True),
                    sa.Column('password_hash', sa.Text(), nullable=True),
                    sa.Column('last_password_hash', sa.Text(), nullable=True),
                    sa.Column('password_timestamp', sa.DateTime(), nullable=True),
                    sa.Column('token', sa.String(length=32), nullable=True),
                    sa.Column('token_expiration', sa.DateTime(), nullable=True),
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
    op.create_index(op.f('ix_user_row_hash'), 'user', ['row_hash'], unique=False)
    op.create_index(op.f('ix_user_token'), 'user', ['token'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('address',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('address1', sa.Text(), nullable=True),
                    sa.Column('address2', sa.Text(), nullable=True),
                    sa.Column('city', sa.Text(), nullable=True),
                    sa.Column('state', sa.String(length=2), nullable=True),
                    sa.Column('zipcode', sa.Text(), nullable=True),
                    sa.Column('district', sa.Text(), nullable=True),
                    sa.Column('country', sa.Text(), nullable=True),
                    sa.Column('primary', sa.Boolean(), nullable=True),
                    sa.Column('is_postal', sa.Boolean(), nullable=True),
                    sa.Column('is_physical', sa.Boolean(), nullable=True),
                    sa.Column('use', sa.Text(), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=True),
                    sa.Column('patient_id', sa.Integer(), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.Column('start_date', sa.Date(), nullable=True),
                    sa.Column('end_date', sa.Date(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('address_hash', sa.Text(), nullable=True),
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
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('row_hash', sa.Text(), nullable=True),
                    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_email_address_email'), 'email_address', ['email'], unique=False)
    op.create_index(op.f('ix_email_address_id'), 'email_address', ['id'], unique=False)
    op.create_index(op.f('ix_email_address_patient_id'), 'email_address', ['patient_id'], unique=False)
    op.create_index(op.f('ix_email_address_row_hash'), 'email_address', ['row_hash'], unique=False)
    op.create_index(op.f('ix_email_address_user_id'), 'email_address', ['user_id'], unique=False)
    op.create_table('phone_number',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('number', sa.Text(), nullable=True),
                    sa.Column('type', sa.Text(), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=True),
                    sa.Column('primary', sa.Boolean(), nullable=True),
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
    op.create_index(op.f('ix_phone_number_row_hash'), 'phone_number', ['row_hash'], unique=False)
    op.create_index(op.f('ix_phone_number_user_id'), 'phone_number', ['user_id'], unique=False)
    op.create_table('transaction',
                    sa.Column('issued_at', sa.DateTime(), nullable=True),
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('remote_addr', sa.String(length=50), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_transaction_user_id'), 'transaction', ['user_id'], unique=False)
    op.create_table('user_app_group',
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('app_group_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['app_group_id'], ['app_group.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('user_id', 'app_group_id')
                    )


def downgrade():
    op.drop_table('user_app_group')
    op.drop_index(op.f('ix_transaction_user_id'), table_name='transaction')
    op.drop_table('transaction')
    op.drop_index(op.f('ix_phone_number_user_id'), table_name='phone_number')
    op.drop_index(op.f('ix_phone_number_row_hash'), table_name='phone_number')
    op.drop_index(op.f('ix_phone_number_patient_id'), table_name='phone_number')
    op.drop_table('phone_number')
    op.drop_index(op.f('ix_email_address_user_id'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_row_hash'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_patient_id'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_id'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_email'), table_name='email_address')
    op.drop_table('email_address')
    op.drop_index(op.f('ix_address_zipcode'), table_name='address')
    op.drop_index(op.f('ix_address_user_id'), table_name='address')
    op.drop_index(op.f('ix_address_patient_id'), table_name='address')
    op.drop_table('address')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_token'), table_name='user')
    op.drop_index(op.f('ix_user_row_hash'), table_name='user')
    op.drop_index(op.f('ix_user_role_id'), table_name='user')
    op.drop_index(op.f('ix_user_last_name'), table_name='user')
    op.drop_index(op.f('ix_user_first_name'), table_name='user')
    op.drop_index(op.f('ix_user_dob'), table_name='user')
    op.drop_table('user')
    op.drop_table('source_data_valueset')
    op.drop_table('source_data_codesystem')
    op.drop_table('role_app_permission')
    op.drop_index(op.f('ix_valueset_data_hash'), table_name='valueset')
    op.drop_table('valueset')
    op.drop_index(op.f('ix_user_version_username'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_transaction_id'), table_name='user_version')
    op.drop_index(op.f('ix_user_version_token'), table_name='user_version')
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
    op.drop_index(op.f('ix_source_data_route'), table_name='source_data')
    op.drop_index(op.f('ix_source_data_payload_hash'), table_name='source_data')
    op.drop_index(op.f('ix_source_data_method'), table_name='source_data')
    op.drop_table('source_data')
    op.drop_index(op.f('ix_role_name'), table_name='role')
    op.drop_index(op.f('ix_role_level'), table_name='role')
    op.drop_table('role')
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
    op.drop_index(op.f('ix_patient_version_id'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_first_name'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_end_transaction_id'), table_name='patient_version')
    op.drop_index(op.f('ix_patient_version_dob'), table_name='patient_version')
    op.drop_table('patient_version')
    op.drop_index(op.f('ix_patient_row_hash'), table_name='patient')
    op.drop_index(op.f('ix_patient_last_name'), table_name='patient')
    op.drop_index(op.f('ix_patient_id'), table_name='patient')
    op.drop_index(op.f('ix_patient_first_name'), table_name='patient')
    op.drop_index(op.f('ix_patient_dob'), table_name='patient')
    op.drop_table('patient')
    op.drop_index(op.f('ix_organization_type'), table_name='organization')
    op.drop_index(op.f('ix_organization_parent_id'), table_name='organization')
    op.drop_table('organization')
    op.drop_index(op.f('ix_email_address_version_user_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_transaction_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_row_hash'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_patient_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_operation_type'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_end_transaction_id'), table_name='email_address_version')
    op.drop_index(op.f('ix_email_address_version_email'), table_name='email_address_version')
    op.drop_table('email_address_version')
    op.drop_index(op.f('ix_codesystem_data_hash'), table_name='codesystem')
    op.drop_table('codesystem')
    op.drop_table('app_permission')
    op.drop_index(op.f('ix_app_group_version_transaction_id'), table_name='app_group_version')
    op.drop_index(op.f('ix_app_group_version_operation_type'), table_name='app_group_version')
    op.drop_index(op.f('ix_app_group_version_end_transaction_id'), table_name='app_group_version')
    op.drop_table('app_group_version')
    op.drop_table('app_group')
    op.drop_index(op.f('ix_address_version_zipcode'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_user_id'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_transaction_id'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_patient_id'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_operation_type'), table_name='address_version')
    op.drop_index(op.f('ix_address_version_end_transaction_id'), table_name='address_version')
    op.drop_table('address_version')
