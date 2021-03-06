"""empty message

Revision ID: 754f274b52e3
Revises: 4e1420f7558b
Create Date: 2020-05-16 21:09:05.537170

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '754f274b52e3'
down_revision = '4e1420f7558b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('website', sa.String(), nullable=True))
    op.add_column('Venue', sa.Column('seeking_description', sa.String(), nullable=True))
    op.add_column('Venue', sa.Column('website', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'website')
    op.drop_column('Venue', 'seeking_description')
    op.drop_column('Artist', 'website')
    # ### end Alembic commands ###
