"""m1_portfolio

Revision ID: b879e9664c5e
Revises: 
Create Date: 2019-11-02 15:14:11.838577

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b879e9664c5e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('m1_portfolio',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('gain', sa.Float(), nullable=False),
    sa.Column('rate', sa.Float(), nullable=False),
    sa.Column('start_value', sa.Float(), nullable=False),
    sa.Column('net_cash_flow', sa.Float(), nullable=False),
    sa.Column('capital_gain', sa.Float(), nullable=False),
    sa.Column('dividend_gain', sa.Float(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('date')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('m1_portfolio')
    # ### end Alembic commands ###
