import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
import uuid

from app import models, schemas
from app.crud import crud_user, crud_team, crud_task

# --- Test Create Task --- 

def test_create_task_success(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User):
    """Test creating a task successfully."""
    task_data = {
        "title": "New Test Task via API",
        "description": "API test description",
        "due_date": date.today().isoformat(),
        "team_id": str(test_team.id)
    }
    response = client.post("/api/v1/tasks/", headers=auth_headers, json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["creator_id"] == str(test_user.id)
    assert data["team_id"] == str(test_team.id)
    assert not data["completed"]
    # Verify in DB
    db_task = crud_task.get_task(db, task_id=uuid.UUID(data["id"]))
    assert db_task is not None
    assert db_task.title == task_data["title"]

def test_create_task_unauthorized(client: TestClient):
    """Test creating a task without authentication."""
    task_data = {
        "title": "Unauthorized Task",
        "description": "Should fail",
        "due_date": date.today().isoformat(),
        "team_id": str(uuid.uuid4()) # Dummy team ID
    }
    response = client.post("/api/v1/tasks/", json=task_data)
    assert response.status_code == 401 # Unauthorized

def test_create_task_forbidden(client: TestClient, db: Session, auth_headers: dict):
    """Test creating a task for a team the user is not a member of."""
    # Create a team owned by someone else (simulate)
    other_user_in = schemas.UserCreate(email="other@example.com", password="otherpass")
    other_user = crud_user.create_user(db, user_in=other_user_in)
    other_team_in = schemas.TeamCreate(name="Other Team")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=other_user)

    task_data = {
        "title": "Forbidden Task",
        "description": "Should fail",
        "due_date": date.today().isoformat(),
        "team_id": str(other_team.id)
    }
    response = client.post("/api/v1/tasks/", headers=auth_headers, json=task_data)
    assert response.status_code == 403 # Forbidden

def test_create_task_invalid_team(client: TestClient, auth_headers: dict):
    """Test creating a task for a non-existent team."""
    task_data = {
        "title": "Invalid Team Task",
        "description": "Should fail",
        "due_date": date.today().isoformat(),
        "team_id": str(uuid.uuid4()) # Non-existent team ID
    }
    response = client.post("/api/v1/tasks/", headers=auth_headers, json=task_data)
    assert response.status_code == 404 # Not Found

# --- Test Read Tasks --- 

def test_read_tasks_success(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_task: models.task.Task, test_user: models.user.User):
    """Test reading tasks for a team the user is a member of."""
    # Create another task to test pagination/listing
    task2_in = schemas.TaskCreate(title="Task Two", team_id=test_team.id, due_date=date.today())
    task2 = crud_task.create_task(db, task_in=task2_in, creator_id=test_user.id)

    response = client.get(f"/api/v1/tasks/?team_id={test_team.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] >= 2 # We created test_task and task2
    assert len(data["items"]) > 0
    assert data["items"][0]["title"] in [test_task.title, task2.title]

def test_read_tasks_pagination(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User):
    """Test pagination for reading tasks."""
    # Create several tasks
    for i in range(5):
        crud_task.create_task(db, task_in=schemas.TaskCreate(title=f"Pag Task {i}", team_id=test_team.id, due_date=date.today()), creator_id=test_user.id)
    
    # Get page 1 (limit 2)
    response1 = client.get(f"/api/v1/tasks/?team_id={test_team.id}&skip=0&limit=2", headers=auth_headers)
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["items"]) == 2
    assert data1["total_items"] >= 5 # Should be at least 5 total
    assert data1["page_number"] == 1
    assert data1["page_size"] == 2

    # Get page 2 (limit 2, skip 2)
    response2 = client.get(f"/api/v1/tasks/?team_id={test_team.id}&skip=2&limit=2", headers=auth_headers)
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) == 2
    assert data2["total_items"] >= 5
    assert data2["page_number"] == 2
    assert data2["page_size"] == 2

    # Check if item IDs differ between pages (simple check)
    assert data1["items"][0]["id"] != data2["items"][0]["id"]

def test_read_tasks_filter_by_assignee(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User):
    """Test filtering tasks by assignee."""
    # Create another user and assign a task to them
    assignee_in = schemas.UserCreate(email="assignee@example.com", password="assignpass")
    assignee_user = crud_user.create_user(db, user_in=assignee_in)
    crud_team.add_user_to_team(db, db_team=test_team, db_user=assignee_user)

    task_assigned = crud_task.create_task(db, task_in=schemas.TaskCreate(title="Assigned Task", team_id=test_team.id, due_date=date.today(), assignee_id=assignee_user.id), creator_id=test_user.id)
    task_unassigned = crud_task.create_task(db, task_in=schemas.TaskCreate(title="Unassigned Task", team_id=test_team.id, due_date=date.today()), creator_id=test_user.id)

    response = client.get(f"/api/v1/tasks/?team_id={test_team.id}&assignee_id={assignee_user.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(task_assigned.id)
    assert data["items"][0]["assignee_id"] == str(assignee_user.id)

def test_read_tasks_filter_by_completed(client: TestClient, db: Session, auth_headers: dict, test_team: models.team.Team, test_user: models.user.User):
    """Test filtering tasks by completion status."""
    task_pending = crud_task.create_task(db, task_in=schemas.TaskCreate(title="Pending Task", team_id=test_team.id, due_date=date.today()), creator_id=test_user.id)
    task_completed_in = schemas.TaskCreate(title="Completed Task", team_id=test_team.id, due_date=date.today(), completed=True)
    task_completed = crud_task.create_task(db, task_in=task_completed_in, creator_id=test_user.id)

    # Filter by completed=true
    response_true = client.get(f"/api/v1/tasks/?team_id={test_team.id}&completed=true", headers=auth_headers)
    assert response_true.status_code == 200
    data_true = response_true.json()
    # Note: This count might include completed tasks from other tests if DB isn't fully isolated per test.
    # Asserting >= 1 is safer unless isolation is perfect.
    assert data_true["total_items"] >= 1 
    assert any(t["id"] == str(task_completed.id) for t in data_true["items"]), "Completed task not found in completed=true filter"
    assert all(t["completed"] for t in data_true["items"])

    # Filter by completed=false
    response_false = client.get(f"/api/v1/tasks/?team_id={test_team.id}&completed=false", headers=auth_headers)
    assert response_false.status_code == 200
    data_false = response_false.json()
    assert data_false["total_items"] >= 1 # Includes test_task fixture task + task_pending
    assert any(t["id"] == str(task_pending.id) for t in data_false["items"]), "Pending task not found in completed=false filter"
    assert all(not t["completed"] for t in data_false["items"])

def test_read_tasks_forbidden(client: TestClient, db: Session, auth_headers: dict):
    """Test reading tasks for a team the user is not a member of."""
    # Create a team owned by someone else
    other_user_in = schemas.UserCreate(email="other2@example.com", password="otherpass2")
    other_user = crud_user.create_user(db, user_in=other_user_in)
    other_team_in = schemas.TeamCreate(name="Other Team 2")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=other_user)

    response = client.get(f"/api/v1/tasks/?team_id={other_team.id}", headers=auth_headers)
    assert response.status_code == 403 # Forbidden

# --- Test Read Single Task --- 

def test_read_single_task_success(client: TestClient, auth_headers: dict, test_task: models.task.Task):
    """Test reading a specific task successfully."""
    response = client.get(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_task.id)
    assert data["title"] == test_task.title

def test_read_single_task_not_found(client: TestClient, auth_headers: dict):
    """Test reading a non-existent task."""
    non_existent_id = uuid.uuid4()
    response = client.get(f"/api/v1/tasks/{non_existent_id}", headers=auth_headers)
    assert response.status_code == 404

def test_read_single_task_forbidden(client: TestClient, db: Session, auth_headers: dict):
    """Test reading a task belonging to a team the user is not part of."""
    # Create a task in another team
    other_user_in = schemas.UserCreate(email="other3@example.com", password="otherpass3")
    other_user = crud_user.create_user(db, user_in=other_user_in)
    other_team_in = schemas.TeamCreate(name="Other Team 3")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=other_user)
    other_task_in = schemas.TaskCreate(title="Other Task", team_id=other_team.id, due_date=date.today())
    other_task = crud_task.create_task(db, task_in=other_task_in, creator_id=other_user.id)

    response = client.get(f"/api/v1/tasks/{other_task.id}", headers=auth_headers)
    assert response.status_code == 403 # Forbidden

# --- Test Update Task --- 

def test_update_task_success(client: TestClient, db: Session, auth_headers: dict, test_task: models.task.Task):
    """Test updating a task successfully."""
    update_data = {
        "title": "Updated Task Title",
        "description": "Updated description.",
        "completed": True
    }
    response = client.put(f"/api/v1/tasks/{test_task.id}", headers=auth_headers, json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_task.id)
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]
    assert data["completed"] == True
    # Verify in DB
    db.refresh(test_task)
    assert test_task.title == update_data["title"]
    assert test_task.completed == True

def test_update_task_assignee_valid(client: TestClient, db: Session, auth_headers: dict, test_task: models.task.Task, test_team: models.team.Team):
    """Test updating task assignee to a valid team member."""
    # Create another user and add to team
    assignee_in = schemas.UserCreate(email="assignee_update@example.com", password="assignpass_upd")
    assignee_user = crud_user.create_user(db, user_in=assignee_in)
    crud_team.add_user_to_team(db, db_team=test_team, db_user=assignee_user)

    update_data = {"assignee_id": str(assignee_user.id)}
    response = client.put(f"/api/v1/tasks/{test_task.id}", headers=auth_headers, json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["assignee_id"] == str(assignee_user.id)
    db.refresh(test_task)
    assert test_task.assignee_id == assignee_user.id

def test_update_task_assignee_invalid_user(client: TestClient, auth_headers: dict, test_task: models.task.Task):
    """Test updating task assignee to a non-existent user."""
    update_data = {"assignee_id": str(uuid.uuid4())}
    response = client.put(f"/api/v1/tasks/{test_task.id}", headers=auth_headers, json=update_data)
    assert response.status_code == 404 # Should be caught by assignee validation

def test_update_task_assignee_not_member(client: TestClient, db: Session, auth_headers: dict, test_task: models.task.Task):
    """Test updating task assignee to a user not in the task's team."""
    # Create another user NOT in the team
    non_member_in = schemas.UserCreate(email="nonmember@example.com", password="nonmemberpass")
    non_member_user = crud_user.create_user(db, user_in=non_member_in)

    update_data = {"assignee_id": str(non_member_user.id)}
    response = client.put(f"/api/v1/tasks/{test_task.id}", headers=auth_headers, json=update_data)
    assert response.status_code == 400 # Bad Request (assignee not member)

def test_update_task_not_found(client: TestClient, auth_headers: dict):
    """Test updating a non-existent task."""
    non_existent_id = uuid.uuid4()
    update_data = {"title": "Won't Update"}
    response = client.put(f"/api/v1/tasks/{non_existent_id}", headers=auth_headers, json=update_data)
    assert response.status_code == 404

def test_update_task_forbidden(client: TestClient, db: Session, auth_headers: dict):
    """Test updating a task in a team the user is not part of."""
    # Create a task in another team
    other_user_in = schemas.UserCreate(email="other4@example.com", password="otherpass4")
    other_user = crud_user.create_user(db, user_in=other_user_in)
    other_team_in = schemas.TeamCreate(name="Other Team 4")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=other_user)
    other_task_in = schemas.TaskCreate(title="Other Task To Update", team_id=other_team.id, due_date=date.today())
    other_task = crud_task.create_task(db, task_in=other_task_in, creator_id=other_user.id)

    update_data = {"title": "Forbidden Update"}
    response = client.put(f"/api/v1/tasks/{other_task.id}", headers=auth_headers, json=update_data)
    assert response.status_code == 403 # Forbidden

# --- Test Delete Task --- 

def test_delete_task_success(client: TestClient, db: Session, auth_headers: dict, test_task: models.task.Task):
    """Test deleting a task successfully."""
    response = client.delete(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
    assert response.status_code == 204
    # Verify soft delete in DB
    db.expire(test_task) # Expire to force reload from DB
    deleted_task = crud_task.get_task(db, task_id=test_task.id, include_deleted=True)
    assert deleted_task is not None
    assert deleted_task.is_deleted == True
    # Verify it doesn't show up in normal get
    active_task = crud_task.get_task(db, task_id=test_task.id)
    assert active_task is None

def test_delete_task_not_found(client: TestClient, auth_headers: dict):
    """Test deleting a non-existent task."""
    non_existent_id = uuid.uuid4()
    response = client.delete(f"/api/v1/tasks/{non_existent_id}", headers=auth_headers)
    assert response.status_code == 404

def test_delete_task_forbidden(client: TestClient, db: Session, auth_headers: dict):
    """Test deleting a task in a team the user is not part of."""
    # Create a task in another team
    other_user_in = schemas.UserCreate(email="other5@example.com", password="otherpass5")
    other_user = crud_user.create_user(db, user_in=other_user_in)
    other_team_in = schemas.TeamCreate(name="Other Team 5")
    other_team = crud_team.create_team_with_creator(db, team_in=other_team_in, creator=other_user)
    other_task_in = schemas.TaskCreate(title="Other Task To Delete", team_id=other_team.id, due_date=date.today())
    other_task = crud_task.create_task(db, task_in=other_task_in, creator_id=other_user.id)

    response = client.delete(f"/api/v1/tasks/{other_task.id}", headers=auth_headers)
    assert response.status_code == 403 # Forbidden


print("test_tasks.py loaded")
