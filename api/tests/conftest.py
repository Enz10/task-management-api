# api/tests/conftest.py
import pytest
from typing import Generator, Any
from app import models # Import your models from top-level app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from main import app  # Import your FastAPI app from top-level main.py
from app.db.base import Base # Import your Base for creating tables
from app.api import deps # To override get_db dependency
from app.core.config import settings
import random
import string

# --- Database Setup for Tests ---
# Using an in-memory SQLite database for testing for speed and isolation.
# Ensure your models are compatible with SQLite or configure a test PostgreSQL DB.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" # In-memory SQLite

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Required for SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create tables once for the session before tests run, drop them after."""
    # Ensure a clean slate
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        print(f"Error dropping tables before test session: {e}")
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("\nTest database tables created.")
    yield # Run tests
    # Optional: Drop tables after tests if desired (or keep test.db for inspection)
    # Base.metadata.drop_all(bind=engine)
    # print("\nTest database tables dropped.")

@pytest.fixture(scope="function")
def db() -> Generator[Session, Any, None]:
    """Fixture to provide a test database session per test function.
    Uses a transaction and rollback to isolate tests.
    """
    connection = engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    # Bind an individual Session to the connection
    session = TestingSessionLocal(bind=connection)
    print("\n Test DB session created")
    try:
        yield session
    finally:
        print(" Test DB session closing and rolling back")
        session.close()
        # Rollback the transaction to ensure test isolation
        transaction.rollback()
        connection.close()


# --- Test Client Setup ---
@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, Any, None]:
    """Fixture to provide a TestClient with overridden database dependency."""
    print("\n Creating TestClient")
    def override_get_db():
        try:
            # print(" Overriding get_db")
            yield db
        finally:
            # print(" Closing overridden db")
            # Session is closed by the 'db' fixture's finally block
            pass 

    app.dependency_overrides[deps.get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    # Clean up override after test function finishes
    print(" Cleaning up TestClient override")
    del app.dependency_overrides[deps.get_db]

# --- Authentication Helper (Basic Example) ---
# You will likely need more sophisticated helpers/fixtures 
# for user creation and token generation based on your app.core.security

@pytest.fixture(scope="function")
def test_user(db: Session) -> models.user.User:
    """Fixture to create a basic test user.
       NOTE: Adapt this based on your User model and creation logic.
    """
    from app.crud import crud_user
    from app.schemas import UserCreate
    from app.core.security import get_password_hash

    email = "test@example.com"
    password = "testpassword"
    user_in = UserCreate(email=email, password=password) 
    user = crud_user.get_user_by_email(db, email=email)
    if not user:
        user = crud_user.create_user(db, user_in=user_in)
    return user

@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: models.user.User) -> dict:
    """Return auth headers for the main test_user."""
    login_data = {
        "username": test_user.email,
        "password": "testpassword" # Use the plain password used in test_user fixture
    }
    r = client.post("/api/v1/login/access-token", data=login_data)
    response_data = r.json()
    assert r.status_code == 200
    assert "access_token" in response_data
    token = response_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers

# --- Fixtures for a Second User (User B) ---
@pytest.fixture(scope="function")
def test_user_b(db: Session) -> models.user.User:
    """Create a second user for integration tests."""
    from app.crud import crud_user
    from app.schemas import UserCreate
    from app.core.security import get_password_hash

    email = f"user_b_{random_lower_string(6)}@example.com"
    user_in = UserCreate(email=email, password="testpass_b")
    user = crud_user.create_user(db=db, user_in=user_in)
    return user

@pytest.fixture(scope="function")
def auth_headers_b(client: TestClient, test_user_b: models.user.User) -> dict:
    """Return auth headers for the second test user (test_user_b)."""
    login_data = {
        "username": test_user_b.email,
        "password": "testpass_b",
    }
    response = client.post("/api/v1/login/access-token", data=login_data)
    assert response.status_code == 200, f"Login failed for user_b: {response.text}"
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

# --- Team Fixtures ---
@pytest.fixture(scope="function")
def test_team(db: Session, test_user: models.user.User) -> models.team.Team:
    """Fixture to create a basic test team with the test_user as a member."""
    from app.crud import crud_team
    from app.schemas import TeamCreate

    team_name = "Test Team One"
    team_in = TeamCreate(name=team_name)
    # Use the correct function and pass the user object
    team = crud_team.create_team_with_creator(db=db, team_in=team_in, creator=test_user)
    return team

@pytest.fixture(scope="function")
def test_task(db: Session, test_team: models.team.Team, test_user: models.user.User) -> models.task.Task:
    """Fixture to create a basic test task associated with test_team and test_user."""
    from app.crud import crud_task
    from app.schemas import TaskCreate
    from datetime import date

    task_in = TaskCreate(
        title="Test Task One",
        description="Description for test task one",
        due_date=date.today(),
        team_id=test_team.id,
        # assignee_id=test_user.id # Optionally assign here if needed for default tests
    )
    task = crud_task.create_task(db=db, task_in=task_in, creator_id=test_user.id)
    return task


print("conftest.py successfully loaded and parsed.") # Confirmation

def random_lower_string(length=6):
    return ''.join(random.choices(string.ascii_lowercase, k=length))
