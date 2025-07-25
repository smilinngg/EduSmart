"""Added marks column to Question

Revision ID: 419075dfd3bd
Revises: 
Create Date: 2025-07-24 00:14:28.516302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '419075dfd3bd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.add_column(sa.Column('marks', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.drop_column('marks')

    # ### end Alembic commands ###
