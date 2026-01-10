from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core import settings

sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    future=True
)


SyncSessionLocal = sessionmaker(
    sync_engine,
    # expire_on_commit=False,
    autoflush=False,  # pending changes are not sent to db
    # doesn't commit to db without calling session.commit()/db.commit() , default False
    autocommit=False
)
