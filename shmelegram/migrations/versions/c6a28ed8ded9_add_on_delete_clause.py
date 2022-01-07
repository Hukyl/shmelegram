"""Add ON DELETE clause

Revision ID: c6a28ed8ded9
Revises: e2ba0f83a66a
Create Date: 2022-01-06 15:03:26.571213

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c6a28ed8ded9'
down_revision = 'e2ba0f83a66a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('message_ibfk_3', 'message', type_='foreignkey')
    op.create_foreign_key(None, 'message', 'message', ['reply_to_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'message', type_='foreignkey')
    op.create_foreign_key('message_ibfk_3', 'message', 'message', ['reply_to_id'], ['id'])
    # ### end Alembic commands ###
