import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient

from app.database.base import Base
from app.database.dependencies import get_db
from app.main import app

from app.models.file import File
from app.models.file_share import FileShare
from app.models.file_version import FileVersion
from app.models.user import User

# Load the test database URL from environment variables
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

# Validate that the test database environment variable is explicitly set
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is not configured. Add it to your .env file."
    )

# Safeguard to prevent running tests against development or production databases
if "arcafs_test_db" not in TEST_DATABASE_URL:
    raise RuntimeError(
        "Tests must use a dedicated test database."
    )

# Initialize the SQLAlchemy database engine for the test suite
test_engine = create_engine(TEST_DATABASE_URL)

# Create a scoped session factory configured for synchronous test operations
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

# Automated fixture to wipe database data and reset sequences before each test case
@pytest.fixture(autouse=True)
def clean_test_database():
    # Ensure that all tables exists (temporary)
    Base.metadata.create_all(bind=test_engine)

    # Build a comma-separated list of table names in reverse dependency order
    table_names = ", ".join(
        f'"{table.name}"'
        for table in reversed(Base.metadata.sorted_tables)
    )

    # Execute a truncate command to purge all tables and reset primary key auto-increments
    if table_names:
        with test_engine.begin() as connection:
            connection.execute(
                text(
                    f"TRUNCATE TABLE {table_names} "
                    "RESTART IDENTITY CASCADE"
                )
            )

    yield

# Fixture to provide a configured TestClient with overridden database dependencies
@pytest.fixture
def client() -> Generator[TestClient, None, None]:

    # Local dependency override function to yield an isolated test database session
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()
    
    # Override the application's core database dependency with the test database session
    app.dependency_overrides[get_db] = override_get_db

    # Initialize the Starlette TestClient context manager to process incoming requests
    with TestClient(app) as test_client:
        yield test_client

    # Clear all dependency overrides after the test scenario completes to ensure isolation
    app.dependency_overrides.clear()
