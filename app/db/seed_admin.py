from loguru import logger
from app.core import settings
from app.models import User
from app.core.pw_hash import hash_password
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select


# create engine and database session
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # print sql queries
    future=True,  # enables sqlalchemy 2.0
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    # autoflush=False # pending changes are not sent to db (default True), why do we need this?
    # doesn't commit to db without calling session.commit()/db.commit() , default False
    autocommit=False
)


async def create_initial_admin():
    async with AsyncSessionLocal() as session:
        # check if admin exists
        result = await session.execute(
            select(User).where(User.email == "admin@gmail.com")
        )

        admin = result.scalar_one_or_none()

        if admin:
            logger.info("Admin already exists -> skipping creation")
            return

        new_admin = User(
            username="admin@gmail.com",
            email="admin@gmail.com",
            hashed_password=hash_password("adminpassword"),
            role="admin",
            is_active=True,
        )

        session.add(new_admin)
        await session.commit()
        logger.success("Initial admin created successfully")


# create super admin
async def create_initial_super_admin():
    async with AsyncSessionLocal() as session:
        # check if admin exists
        result = await session.execute(
            select(User).where(User.email == "shahriarhossainalvi@gmail.com")
        )

        super_admin = result.scalar_one_or_none()

        if super_admin:
            logger.info("Super admin already exists -> skipping creation")
            return

        new_super_admin = User(
            username="shahriarhossainalvi@gmail.com",
            email="shahriarhossainalvi@gmail.com",
            hashed_password=hash_password("superadminpassword"),
            role="super_admin",
            is_active=True,
        )

        session.add(new_super_admin)
        await session.commit()
        logger.success("Initial admin created successfully")


async def run():
    try:
        await create_initial_admin()
        await create_initial_super_admin()
    except Exception as e:
        logger.error(
            f"Error occurred while creating initial admin or super admin: {e}")

if __name__ == "__main__":
    asyncio.run(run())
