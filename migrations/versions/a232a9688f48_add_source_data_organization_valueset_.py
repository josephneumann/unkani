"""Add source_data, organization, valueset and codesystem models

Revision ID: a232a9688f48
Revises: fad81a7cf95d
Create Date: 2017-09-11 07:07:12.497593

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a232a9688f48'
down_revision = 'fad81a7cf95d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('codesystem',
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
    op.create_index(op.f('ix_codesystem_data_hash'), 'codesystem', ['data_hash'], unique=False)

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


def downgrade():
    op.drop_table('source_data_valueset')
    op.drop_table('source_data_codesystem')
    op.drop_index(op.f('ix_valueset_data_hash'), table_name='valueset')
    op.drop_table('valueset')
    op.drop_index(op.f('ix_source_data_route'), table_name='source_data')
    op.drop_index(op.f('ix_source_data_payload_hash'), table_name='source_data')
    op.drop_index(op.f('ix_source_data_method'), table_name='source_data')
    op.drop_table('source_data')
    op.drop_index(op.f('ix_organization_type'), table_name='organization')
    op.drop_index(op.f('ix_organization_parent_id'), table_name='organization')
    op.drop_table('organization')
    op.drop_index(op.f('ix_codesystem_data_hash'), table_name='codesystem')
    op.drop_table('codesystem')
