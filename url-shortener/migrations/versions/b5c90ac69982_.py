"""empty message

Revision ID: b5c90ac69982
Revises: 5f92514b99f6
Create Date: 2021-03-18 18:52:37.659709

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5c90ac69982'
down_revision = '5f92514b99f6'
branch_labels = None
depends_on = None


def upgrade():
	# ### commands auto generated by Alembic - please adjust! ###
	op.create_table('shorturl',
	sa.Column('id', sa.Integer(), nullable=False),
	sa.Column('created_at', sa.DateTime(), nullable=True),
	sa.Column('updated_at', sa.DateTime(), nullable=True),
	sa.Column('owner_id', sa.Integer(), nullable=False),
	sa.Column('full_url', sa.Text(), nullable=False),
	sa.Column('clicks', sa.Integer(), nullable=False),
	sa.Column('slug', sa.String(length=4), nullable=False),
	sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
	sa.PrimaryKeyConstraint('id')
	)
	op.create_index(op.f('ix_shorturl_full_url'), 'shorturl', ['full_url'], unique=False)
	op.create_index(op.f('ix_shorturl_slug'), 'shorturl', ['slug'], unique=True)
	# ### end Alembic commands ###


def downgrade():
	# ### commands auto generated by Alembic - please adjust! ###
	op.drop_index(op.f('ix_shorturl_slug'), table_name='shorturl')
	op.drop_index(op.f('ix_shorturl_full_url'), table_name='shorturl')
	op.drop_table('shorturl')
	# ### end Alembic commands ###