import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app import models, schemas
from app.crud import crud_user, crud_team

# --- Test Create Team --- 

def test_create_team_success(client: TestClient, db: Session, auth_headers: dict, test_user: models.user.User):
    """Test creating a team successfully."""
    team_data = {"name": "New Team API Test"}
    response = client.post("/api/v1/teams/", headers=auth_headers, json=team_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == team_data["name"]
    assert "id" in data
    assert "created_at" in data
    # Verify in DB
    db_team = crud_team.get_team(db, team_id=uuid.UUID(data["id"]))
    assert db_team is not None
    assert db_team.name == team_data["name"]
    # Verify owner is a member
    assert crud_team.is_user_member_of_team(db, team_id=db_team.id, user_id=test_user.id)

def test_create_team_unauthorized(client: TestClient):
    """Test creating a team without authentication."""
    team_data = {"name": "Unauthorized Team"}
    response = client.post("/api/v1/teams/", json=team_data)
    assert response.status_code == 401 # Unauthorized

# --- Test Read Teams (User is Member Of) --- 

def test_read_user_teams_success(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User):
    """Test reading teams the current user is a member of."""
    # Create another team user is part of
    team2_data = {"name": "Second Team User Is In"}
    response_create = client.post("/api/v1/teams/", headers=auth_headers, json=team2_data)
    assert response_create.status_code == 201
    team2_id = response_create.json()["id"]

    response = client.get("/api/v1/teams/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2 # Should include test_team and team2
    team_ids = [t["id"] for t in data]
    assert str(test_team.id) in team_ids
    assert team2_id in team_ids

def test_read_user_teams_empty(client: TestClient, db: Session, auth_headers: dict):
    """Test reading teams when user is not part of any (after setup)."""
    # This test assumes the test_user fixture doesn't automatically create/add to teams
    # other than the one created in test_team fixture (which is scoped per function).
    # Let's create a new user with no teams for this test.
    isolated_user_in = schemas.UserCreate(email="isolated@example.com", password="isolatepass")
    isolated_user = crud_user.create_user(db, user_in=isolated_user_in)
    # Login as isolated user
    login_data = {"username": isolated_user.email, "password": "isolatepass"}
    r_login = client.post("/api/v1/login/access-token", data=login_data)
    token = r_login.json()["access_token"]
    isolated_auth_headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/teams/", headers=isolated_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

# --- Test Read Single Team --- 

def test_read_single_team_success(client: TestClient, auth_headers: dict, test_team: models.team.Team):
    """Test reading a specific team the user is a member of."""
    response = client.get(f"/api/v1/teams/{test_team.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_team.id)
    assert data["name"] == test_team.name

def test_read_single_team_not_found(client: TestClient, auth_headers: dict):
    """Test reading a non-existent team."""
    non_existent_id = uuid.uuid4()
    response = client.get(f"/api/v1/teams/{non_existent_id}", headers=auth_headers)
    assert response.status_code == 404

def test_read_single_team_forbidden(client: TestClient, db: Session, auth_headers: dict):
    """Test reading a team the user is not a member of."""
    # Create a team user is not part of
    other_user_in = schemas.UserCreate(email="other_team_owner@example.com", password="otherpass")
    other_user = crud_user.create_user(db, user_in=other_user_in)
    other_team_in = schemas.TeamCreate(name="Forbidden Team")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=other_user)

    response = client.get(f"/api/v1/teams/{other_team.id}", headers=auth_headers)
    assert response.status_code == 403 # Forbidden

# --- Test Update Team --- 

def test_update_team_success(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User):
    """Test updating a team successfully (user must be member)."""
    update_data = {"name": "Updated Team Name API"}
    response = client.put(f"/api/v1/teams/{test_team.id}", headers=auth_headers, json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_team.id)
    assert data["name"] == update_data["name"]
    # Verify in DB
    db.refresh(test_team)
    assert test_team.name == update_data["name"]

def test_update_team_not_owner(client: TestClient, db: Session, auth_headers: dict, test_user: models.user.User):
    """Test updating a team when the user is a member but not the owner."""
    # Create a team owned by someone else, add test_user as member
    owner_in = schemas.UserCreate(email="owner@example.com", password="ownerpass")
    owner_user = crud_user.create_user(db, user_in=owner_in)
    team_to_update_in = schemas.TeamCreate(name="Team To Fail Update")
    team_to_update = crud_team.create_team_with_creator(db, team_in=team_to_update_in, creator=owner_user)
    crud_team.add_user_to_team(db, db_team=team_to_update, db_user=test_user)

    update_data = {"name": "Updated by Member"}
    response = client.put(f"/api/v1/teams/{team_to_update.id}", headers=auth_headers, json=update_data)
    assert response.status_code == 200 # Should succeed as user is a member

def test_update_team_not_found(client: TestClient, auth_headers: dict):
    """Test updating a non-existent team."""
    non_existent_id = uuid.uuid4()
    update_data = {"name": "Won't Update"}
    response = client.put(f"/api/v1/teams/{non_existent_id}", headers=auth_headers, json=update_data)
    assert response.status_code == 404

# --- Test Delete Team --- 

def test_delete_team_success(client: TestClient, db: Session, auth_headers: dict, test_user: models.user.User):
    """Test deleting a team successfully (user must be owner)."""
    # Create a team specifically for this test to ensure ownership
    team_to_delete_in = schemas.TeamCreate(name="Team To Delete")
    team_to_delete = crud_team.create_team_with_creator(db, team_in=team_to_delete_in, creator=test_user)
    team_id_to_delete = team_to_delete.id

    response = client.delete(f"/api/v1/teams/{team_id_to_delete}", headers=auth_headers)
    assert response.status_code == 204 # Successful deletion, no content
    # Verify soft delete in DB
    db.expire(team_to_delete) # Expire to force reload
    deleted_team = crud_team.get_team(db, team_id=team_id_to_delete, include_deleted=True)
    assert deleted_team is not None
    # Verify it doesn't show up in normal get
    active_team = crud_team.get_team(db, team_id=team_id_to_delete)
    assert active_team is None

def test_delete_team_not_owner(client: TestClient, db: Session, auth_headers: dict, test_user: models.user.User):
    """Test deleting a team when the user is a member but not the owner."""
    # Create a team owned by someone else, add test_user as member
    owner_in = schemas.UserCreate(email="owner2@example.com", password="ownerpass2")
    owner_user = crud_user.create_user(db, user_in=owner_in)
    team_to_fail_delete_in = schemas.TeamCreate(name="Team To Fail Delete")
    team_to_fail_delete = crud_team.create_team_with_creator(db, team_in=team_to_fail_delete_in, creator=owner_user)
    crud_team.add_user_to_team(db, db_team=team_to_fail_delete, db_user=test_user)

    response = client.delete(f"/api/v1/teams/{team_to_fail_delete.id}", headers=auth_headers)
    assert response.status_code == 204 # Should succeed as user is a member

def test_delete_team_not_found(client: TestClient, auth_headers: dict):
    """Test deleting a non-existent team."""
    non_existent_id = uuid.uuid4()
    response = client.delete(f"/api/v1/teams/{non_existent_id}", headers=auth_headers)
    assert response.status_code == 404

# --- Test Manage Team Members --- 

@pytest.fixture(scope="function")
def member_to_add(db: Session) -> models.user.User:
    """Fixture to create a user who can be added as a team member."""
    user_in = schemas.UserCreate(email=f"member_to_add_{uuid.uuid4().hex[:6]}@example.com", password="addmepass")
    # Check if user already exists (in case tests run multiple times without db cleanup)
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if not user:
        user = crud_user.create_user(db, user_in=user_in)
    return user

def test_add_member_to_team_success(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User, member_to_add: models.user.User):
    """Test adding a member to a team successfully (any member can add)."""
    response = client.post(f"/api/v1/teams/{test_team.id}/members/{member_to_add.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert any(member['id'] == str(member_to_add.id) for member in data['members'])
    # Verify in DB
    assert crud_team.is_user_member_of_team(db, team_id=test_team.id, user_id=member_to_add.id)

def test_add_member_to_team_not_owner(client: TestClient, db: Session, auth_headers: dict, test_user: models.user.User, member_to_add: models.user.User):
    """Test adding a member when the user is not the team owner."""
    # Create team owned by someone else, add test_user as member
    owner_in = schemas.UserCreate(email="owner3@example.com", password="ownerpass3")
    owner_user = crud_user.create_user(db, user_in=owner_in)
    other_team_in = schemas.TeamCreate(name="Team NonOwner Add")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=owner_user)
    crud_team.add_user_to_team(db, db_team=other_team, db_user=test_user)

    response = client.post(f"/api/v1/teams/{other_team.id}/members/{member_to_add.id}", headers=auth_headers)
    assert response.status_code == 200 # Should succeed, test_user is a member

def test_add_member_already_member(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User, member_to_add: models.user.User):
    """Test adding a member who is already in the team."""
    # Add member first
    crud_team.add_user_to_team(db, db_team=test_team, db_user=member_to_add)

    response = client.post(f"/api/v1/teams/{test_team.id}/members/{member_to_add.id}", headers=auth_headers)
    assert response.status_code == 200 # OK (idempotent)

    # Optionally: verify member count hasn't changed if needed

def test_add_member_invalid_user(client: TestClient, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User):
    """Test adding a non-existent user to a team."""
    non_existent_user_id = uuid.uuid4()
    response = client.post(f"/api/v1/teams/{test_team.id}/members/{non_existent_user_id}", headers=auth_headers)
    assert response.status_code == 404 # Not Found (user)

def test_remove_member_from_team_success(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User, member_to_add: models.user.User):
    """Test removing a member from a team successfully (user must be owner)."""
    # Add member first
    crud_team.add_user_to_team(db, db_team=test_team, db_user=member_to_add)
    assert crud_team.is_user_member_of_team(db, team_id=test_team.id, user_id=member_to_add.id)

    response = client.delete(f"/api/v1/teams/{test_team.id}/members/{member_to_add.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(member['id'] != str(member_to_add.id) for member in data['members'])
    # Verify in DB
    assert not crud_team.is_user_member_of_team(db, team_id=test_team.id, user_id=member_to_add.id)

def test_remove_member_not_owner(client: TestClient, db: Session, auth_headers: dict, test_user: models.user.User, member_to_add: models.user.User):
    """Test removing a member when the user is not the team owner."""
    # Create team owned by someone else, add test_user and member_to_add
    owner_in = schemas.UserCreate(email="owner4@example.com", password="ownerpass4")
    owner_user = crud_user.create_user(db, user_in=owner_in)
    other_team_in = schemas.TeamCreate(name="Team NonOwner Remove")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=owner_user)
    crud_team.add_user_to_team(db, db_team=other_team, db_user=test_user)
    crud_team.add_user_to_team(db, db_team=other_team, db_user=member_to_add)

    response = client.delete(f"/api/v1/teams/{other_team.id}/members/{member_to_add.id}", headers=auth_headers)
    assert response.status_code == 200 # Should succeed, test_user is a member

def test_remove_member_not_member(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User, member_to_add: models.user.User):
    """Test removing a user who is not a member of the team."""
    # Ensure member_to_add is NOT a member
    assert not crud_team.is_user_member_of_team(db, team_id=test_team.id, user_id=member_to_add.id)

    response = client.delete(f"/api/v1/teams/{test_team.id}/members/{member_to_add.id}", headers=auth_headers)
    assert response.status_code == 200 # OK (idempotent)

def test_remove_self_from_team(client: TestClient, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User):
    """Test removing oneself from a team successfully."""
    response = client.delete(f"/api/v1/teams/{test_team.id}/members/{test_user.id}", headers=auth_headers)
    assert response.status_code == 200 # OK (user removes self)

# --- Test List Team Members --- 

@pytest.mark.skip(reason="GET /teams/{team_id}/members endpoint not implemented yet")
def test_list_team_members_success(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User, member_to_add: models.user.User):
    """Test listing members of a team successfully."""
    # Ensure both test_user (owner) and member_to_add are members
    if test_team.owner_id == test_user.id:
        crud_team.add_user_to_team(db, db_team=test_team, db_user=member_to_add)
    else: # If test_user isn't owner, need to ensure they are at least a member
        if not crud_team.is_user_member_of_team(db, team_id=test_team.id, user_id=test_user.id):
             crud_team.add_user_to_team(db, db_team=test_team, db_user=test_user)
        # Can't add member_to_add in this case as not owner

    response = client.get(f"/api/v1/teams/{test_team.id}/members", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    member_ids = [m["id"] for m in data]
    assert str(test_user.id) in member_ids
    if test_team.owner_id == test_user.id:
        assert str(member_to_add.id) in member_ids
        assert len(data) >= 2
    else:
        assert len(data) >= 1

@pytest.mark.skip(reason="GET /teams/{team_id}/members endpoint not implemented yet")
def test_list_team_members_forbidden(client: TestClient, db: Session, auth_headers: dict):
    """Test listing members of a team the user is not part of."""
    # Create team user is not part of
    owner_in = schemas.UserCreate(email="owner5@example.com", password="ownerpass5")
    owner_user = crud_user.create_user(db, user_in=owner_in)
    other_team_in = schemas.TeamCreate(name="Team Forbidden List")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=owner_user)

    response = client.get(f"/api/v1/teams/{other_team.id}/members", headers=auth_headers)
    assert response.status_code == 403 # Forbidden

print("test_teams.py loaded")
