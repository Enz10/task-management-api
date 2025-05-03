import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# Add api directory to sys.path
# This assumes env.py is in alembic/ and the app is in ../app
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Import Base from your project structure
from app.db.base import Base  # Import from the file that loads models
from app.models.user import User
from app.models.task import Task

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# --- Get Database URL directly from Environment ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable not set.")
# You might want to print it here for debugging (masking password)
# from urllib.parse import urlparse, urlunparse
# parsed = urlparse(DATABASE_URL)
# print(f"Alembic env.py using DATABASE_URL: {urlunparse(parsed._replace(netloc=f'{parsed.username}:*****@{parsed.hostname}:{parsed.port}'))}")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL, # Use the variable directly
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Create engine directly using the DATABASE_URL from environment
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
