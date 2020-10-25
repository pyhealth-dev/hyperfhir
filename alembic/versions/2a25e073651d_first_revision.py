"""First Revision

Revision ID: 2a25e073651d
Revises:
Create Date: 2020-10-08 09:07:32.910339

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2a25e073651d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('resourcehistory_table',
    sa.Column('id', sa.BIGINT(), nullable=False),
    sa.Column('txid', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('created', 'updated', 'deleted', 'recreated', 'archived', name="resource_transaction_status"), nullable=True),
    sa.Column('resource_version', sa.String(length=8), nullable=False),
    sa.Column('resource_id', sa.CHAR(length=36), nullable=False),
    sa.Column('fhir_version', sa.String(length=8), nullable=False),
    sa.Column('resource_type', sa.String(length=64), nullable=False),
    sa.Column('resource', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('next_txid', sa.Integer(), nullable=True),
    sa.Column('pre_txid', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resourcehistory_table_resource_id'), 'resourcehistory_table', ['resource_id'], unique=False)
    op.create_index(op.f('ix_resourcehistory_table_resource_type'), 'resourcehistory_table', ['resource_type'], unique=False)
    op.create_table('resourcetransaction_table',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('index_id', sa.String(length=127), nullable=False),
    sa.Column('resource_id', sa.CHAR(length=36), nullable=False),
    sa.Column('status', sa.Enum('created', 'updated', 'deleted', 'recreated', 'archived', name="resource_transaction_status"), nullable=True),
    sa.Column('resource_type', sa.String(length=64), nullable=False),
    sa.Column('resource_version', sa.String(length=8), nullable=False),
    sa.Column('resource', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('fhir_version', sa.String(length=8), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('resource_id', 'resource_type')
    )
    op.create_index(op.f('ix_resourcetransaction_table_resource_id'), 'resourcetransaction_table', ['resource_id'], unique=False)
    op.create_index(op.f('ix_resourcetransaction_table_resource_type'), 'resourcetransaction_table', ['resource_type'], unique=False)
    op.create_index(op.f('ix_resourcetransaction_table_status'), 'resourcetransaction_table', ['status'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_resourcetransaction_table_status'), table_name='resourcetransaction_table')
    op.drop_index(op.f('ix_resourcetransaction_table_resource_type'), table_name='resourcetransaction_table')
    op.drop_index(op.f('ix_resourcetransaction_table_resource_id'), table_name='resourcetransaction_table')
    op.drop_table('resourcetransaction_table')
    op.drop_index(op.f('ix_resourcehistory_table_resource_type'), table_name='resourcehistory_table')
    op.drop_index(op.f('ix_resourcehistory_table_resource_id'), table_name='resourcehistory_table')
    op.drop_table('resourcehistory_table')
    # ### end Alembic commands ###
