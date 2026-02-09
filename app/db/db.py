import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core import settings
from sqlalchemy.pool import NullPool

# Determine if we need SSL (Neon/Supabase need it, local usually doesn't)
# We can check if local db name "edutrack_db" or "db" (Docker) is in the URL
is_local = "edutrack_db" in settings.DATABASE_URL or "@db:" in settings.DATABASE_URL

# This is the critical fix for Transaction Mode, Highly recommended for Supabase/Render to avoid stale connections
connect_args = {
    "statement_cache_size": 0,
    "prepared_statement_cache_size": 0,
}

# Only add SSL if we aren't local
if not is_local:
    connect_args["ssl"] = True

# create engine and database session
engine = create_async_engine(
    settings.DATABASE_URL,  # Async DB URL
    poolclass=NullPool,
    connect_args=connect_args,
    future=True,  # enables sqlalchemy 2.0
    echo=False,  # False because we will use Logger to print sql queries

)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    # autoflush=False # pending changes are not sent to db (default True), why do we need this?
    # doesn't commit to db without calling session.commit()/db.commit() , default False
    autocommit=False
)


# dependency for db session
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
