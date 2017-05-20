"""Patient, Address, Email model creation

Revision ID: e31b9244084b
Revises: 30eb77cfd650
Create Date: 2017-05-19 17:55:55.477447

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e31b9244084b'
down_revision = '30eb77cfd650'
branch_labels = None
depends_on = None


# Reviewed by Joseph Neumann on 2017-05-19

def upgrade():
    op.create_table('patient',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('first_name', sa.Text(), nullable=True),
                    sa.Column('last_name', sa.Text(), nullable=True),
                    sa.Column('middle_name', sa.Text(), nullable=True),
                    sa.Column('suffix', sa.Text(), nullable=True),
                    sa.Column('sex', sa.String(length=1), nullable=True),
                    sa.Column('dob', sa.Date(), nullable=True),
                    sa.Column('ssn', sa.Text(), nullable=True),
                    sa.Column('home_phone', sa.Text(), nullable=True),
                    sa.Column('cell_phone', sa.Text(), nullable=True),
                    sa.Column('work_phone', sa.Text(), nullable=True),
                    sa.Column('deceased', sa.Boolean(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('row_hash', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('address',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('_address1', sa.Text(), nullable=True),
                    sa.Column('_address2', sa.Text(), nullable=True),
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


def downgrade():
    op.drop_index(op.f('ix_email_address_id'), table_name='email_address')
    op.drop_index(op.f('ix_email_address_email'), table_name='email_address')
    op.drop_table('email_address')
    op.drop_table('address')
    op.drop_table('patient')
