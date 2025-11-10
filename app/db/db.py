from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core import settings


# create engine and database session
engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# depndency for db session
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session