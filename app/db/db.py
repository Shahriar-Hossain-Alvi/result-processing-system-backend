from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core import settings
from sqlalchemy.pool import NullPool

# create engine and database session
engine = create_async_engine(
    settings.DATABASE_URL,  # Async DB URL
    # This is the critical fix for Transaction Mode
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    },
    # Highly recommended for Supabase/Render to avoid stale connections
    poolclass=NullPool,
    echo=False,  # False because we will use Logger to print sql queries
    future=True,  # enables sqlalchemy 2.0
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
