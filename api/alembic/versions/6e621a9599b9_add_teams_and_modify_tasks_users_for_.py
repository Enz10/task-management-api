"""Add teams and modify tasks/users for collaboration

Revision ID: 6e621a9599b9
Revises: 6ea72e02df3e
Create Date: 2025-05-03 17:36:00.425324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e621a9599b9'
down_revision: Union[str, None] = '6ea72e02df3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - START ###
    op.create_table('teams',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teams_name'), 'teams', ['name'], unique=True)
    op.create_table('team_members',
    sa.Column('team_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('team_id', 'user_id')
    )
    # ### commands auto generated by Alembic - END ###

    # --- Manual Adjustments Start ---
    # 1. Add new columns allowing NULLs initially
    op.add_column('tasks', sa.Column('team_id', sa.UUID(), nullable=True))
    op.add_column('tasks', sa.Column('creator_id', sa.UUID(), nullable=True))

    # 2. Populate creator_id from existing owner_id
    #    Use op.execute for raw SQL
    #    Ensure table/column names match your actual schema if different
    op.execute('UPDATE tasks SET creator_id = owner_id WHERE owner_id IS NOT NULL')

    # 3. Now that creator_id is populated, make it NOT NULL
    op.alter_column('tasks', 'creator_id', nullable=False)
    # Note: We leave team_id as nullable in the DB for existing tasks.
    #       New tasks should enforce team_id at the application level.

    # 4. Drop the old foreign key constraint *before* dropping the column
    op.drop_constraint('tasks_owner_id_fkey', 'tasks', type_='foreignkey')

    # 5. Drop the old owner_id column
    op.drop_column('tasks', 'owner_id')

    # 6. Create the new foreign keys
    #    Using explicit constraint names for clarity and easier downgrades
    op.create_foreign_key('fk_tasks_team_id_teams', 'tasks', 'teams', ['team_id'], ['id'])
    op.create_foreign_key('fk_tasks_creator_id_users', 'tasks', 'users', ['creator_id'], ['id'])
    # --- Manual Adjustments End ---


def downgrade() -> None:
    """Downgrade schema."""
    # --- Manual Adjustments Start (Reverse Order) ---
    # 6. Drop the new foreign keys
    op.drop_constraint('fk_tasks_creator_id_users', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_tasks_team_id_teams', 'tasks', type_='foreignkey')

    # 5. Add back owner_id, allowing NULLs initially
    op.add_column('tasks', sa.Column('owner_id', sa.UUID(), autoincrement=False, nullable=True))

    # 4. Create the old foreign key constraint *after* adding the column
    #    Note: We need the original constraint name 'tasks_owner_id_fkey'
    op.create_foreign_key('tasks_owner_id_fkey', 'tasks', 'users', ['owner_id'], ['id'])

    # 3. Populate owner_id from creator_id (reverse of upgrade)
    op.execute('UPDATE tasks SET owner_id = creator_id WHERE creator_id IS NOT NULL')

    # 2. Make owner_id NOT NULL again
    op.alter_column('tasks', 'owner_id', nullable=False)

    # 1. Drop the new columns
    op.drop_column('tasks', 'creator_id')
    op.drop_column('tasks', 'team_id')
    # --- Manual Adjustments End ---


    # ### commands auto generated by Alembic - START ###
    op.drop_table('team_members')
    op.drop_index(op.f('ix_teams_name'), table_name='teams')
    op.drop_table('teams')
    # ### commands auto generated by Alembic - END ###
