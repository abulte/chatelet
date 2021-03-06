"""add secret column

Revision ID: 23eb6546d797
Revises: 2762be5c1c08
Create Date: 2021-02-28 09:26:46.700861

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23eb6546d797'
down_revision = '2762be5c1c08'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('subscriptions', sa.Column('secret', sa.Unicode(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('subscriptions', 'secret')
    # ### end Alembic commands ###
