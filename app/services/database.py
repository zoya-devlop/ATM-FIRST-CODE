from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- POSTGRESQL CONNECTION STRING ---
# WARNING: Replace 'zoy7461%40' with your actual PostgreSQL password
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:zoy7461%40@localhost:5432/orbitcloud_db"
# Create the Postgres engine
# Notice: We removed 'check_same_thread' because Postgres handles multi-threading natively!
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()