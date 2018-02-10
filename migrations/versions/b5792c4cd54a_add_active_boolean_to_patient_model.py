"""Add active boolean to patient model

Revision ID: b5792c4cd54a
Revises: f2b42573fb15
Create Date: 2018-02-09 20:33:08.111527

"""
from alembic import op
import sqlalchemy as sa


revision = 'b5792c4cd54a'
down_revision = 'f2b42573fb15'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('patient', sa.Column('active', sa.Boolean(), nullable=False))
    op.add_column('patient_version', sa.Column('active', sa.Boolean(), autoincrement=False, nullable=True))
    op.add_column('patient_version', sa.Column('active_mod', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade():
    op.drop_column('patient_version', 'active_mod')
    op.drop_column('patient_version', 'active')
    op.drop_column('patient', 'active')
