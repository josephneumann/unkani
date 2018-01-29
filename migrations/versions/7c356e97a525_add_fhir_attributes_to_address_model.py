"""Add FHIR attributes to Address model

Revision ID: 7c356e97a525
Revises: a232a9688f48
Create Date: 2018-01-21 20:56:02.770649

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c356e97a525'
down_revision = 'a232a9688f48'
branch_labels = None
depends_on = None


def upgrade():
    # Address modifications
    op.add_column('address', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('address', sa.Column('end_date', sa.Date(), nullable=True))
    op.add_column('address', sa.Column('is_physical', sa.Boolean(), nullable=True))
    op.add_column('address', sa.Column('is_postal', sa.Boolean(), nullable=True))
    op.add_column('address', sa.Column('use', sa.Text(), nullable=True))

    # Address version modifications
    op.add_column('address_version', sa.Column('end_date', sa.Date(), autoincrement=False, nullable=True))
    op.add_column('address_version', sa.Column('end_date_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('address_version', sa.Column('start_date', sa.Date(), autoincrement=False, nullable=True))
    op.add_column('address_version', sa.Column('start_date_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('address_version', sa.Column('is_physical', sa.Boolean(), autoincrement=False, nullable=True))
    op.add_column('address_version', sa.Column('is_physical_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('address_version', sa.Column('is_postal', sa.Boolean(), autoincrement=False, nullable=True))
    op.add_column('address_version', sa.Column('is_postal_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('address_version', sa.Column('use', sa.Text(), autoincrement=False, nullable=True))
    op.add_column('address_version', sa.Column('use_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade():
    op.drop_column('address_version', 'use_mod')
    op.drop_column('address_version', 'use')
    op.drop_column('address_version', 'start_date_mod')
    op.drop_column('address_version', 'start_date')
    op.drop_column('address_version', 'is_postal_mod')
    op.drop_column('address_version', 'is_postal')
    op.drop_column('address_version', 'is_physical_mod')
    op.drop_column('address_version', 'is_physical')
    op.drop_column('address_version', 'end_date_mod')
    op.drop_column('address_version', 'end_date')

    op.drop_column('address', 'use')
    op.drop_column('address', 'start_date')
    op.drop_column('address', 'is_postal')
    op.drop_column('address', 'is_physical')
    op.drop_column('address', 'end_date')
