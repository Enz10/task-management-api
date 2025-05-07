import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import datetime

from app import models
from app.schemas import TeamCreate, TaskCreate
from app.crud import crud_team, crud_task, crud_user

def test_team_task_lifecycle(
    client: TestClient,
    db: Session,
    test_user: models.user.User, # User A
    auth_headers: dict,         # User A headers
    test_user_b: models.user.User, # User B
    auth_headers_b: dict        # User B headers
):
    """Tests a full workflow: create team, add member, create task, assign, complete, remove member, delete team."""

    # 1. User A creates a team
    team_name = f"Integration Test Team {uuid.uuid4().hex[:6]}"
    team_create_data = {"name": team_name}
    response_create_team = client.post("/api/v1/teams", headers=auth_headers, json=team_create_data)
    assert response_create_team.status_code == 201, f"Failed to create team: {response_create_team.text}"
    team_data = response_create_team.json()
    team_id = team_data["id"]
    assert team_data["name"] == team_name
    # Verify User A is a member in DB
    db_team = crud_team.get_team(db, team_id=uuid.UUID(team_id))
    assert db_team is not None
    assert any(member.id == test_user.id for member in db_team.members), "Creator (User A) not found in team members"

    # 2. User A adds User B to the team
    response_add_member = client.post(f"/api/v1/teams/{team_id}/members/{test_user_b.id}", headers=auth_headers)
    assert response_add_member.status_code == 200, f"Failed to add member: {response_add_member.text}"
    team_data_after_add = response_add_member.json()
    assert any(member['id'] == str(test_user_b.id) for member in team_data_after_add['members']), "User B not found in response members list"
    # Verify User B is a member in DB
    db.refresh(db_team)
    assert any(member.id == test_user_b.id for member in db_team.members), "User B not found in DB team members"

    # Set a due date for the task (e.g., 7 days from now)
    due_date_dt = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).date()
    due_date = due_date_dt.isoformat() # Format as YYYY-MM-DD string

    # 3. User A creates a task and assigns it to User B
    task_create_data = {
        "title": "Integration Task",
        "description": "Complete this workflow task.",
        "team_id": team_id,
        "assignee_id": str(test_user_b.id),
        "due_date": due_date # Add the due date
    }
    response_create_task = client.post("/api/v1/tasks", headers=auth_headers, json=task_create_data)
    assert response_create_task.status_code == 201, f"Failed to create task: {response_create_task.text}"
    task_data = response_create_task.json()
    task_id = task_data["id"]
    assert task_data["title"] == task_create_data["title"]
    assert task_data["assignee_id"] == str(test_user_b.id)
    assert task_data["team_id"] == team_id
    assert not task_data["completed"]
    assert task_data["due_date"] is not None # Check due date is present in response
    assert task_data["due_date"] == due_date # Check due date value

    # 4. User B marks the task as completed
    task_update_data = {"completed": True}
    response_update_task = client.put(f"/api/v1/tasks/{task_id}", headers=auth_headers_b, json=task_update_data)
    assert response_update_task.status_code == 200, f"Failed to update task: {response_update_task.text}"
    task_data_updated = response_update_task.json()
    assert task_data_updated["completed"] == True
    # Verify completion in DB
    db_task = crud_task.get_task(db, task_id=uuid.UUID(task_id))
    assert db_task is not None
    assert db_task.completed == True

    # 5. User A removes User B from the team
    response_remove_member = client.delete(f"/api/v1/teams/{team_id}/members/{test_user_b.id}", headers=auth_headers)
    assert response_remove_member.status_code == 200, f"Failed to remove member: {response_remove_member.text}"
    team_data_after_remove = response_remove_member.json()
    assert all(member['id'] != str(test_user_b.id) for member in team_data_after_remove['members']), "User B still found in response members list after removal"
    # Verify User B is not a member in DB
    db.refresh(db_team)
    assert all(member.id != test_user_b.id for member in db_team.members), "User B still found in DB team members after removal"

    # 6. User A deletes the team (soft delete)
    response_delete_team = client.delete(f"/api/v1/teams/{team_id}", headers=auth_headers)
    # The delete endpoint returns 204 No Content upon success
    assert response_delete_team.status_code == 204, f"Failed to delete team: {response_delete_team.text} (Status: {response_delete_team.status_code})"
    # Verify soft delete in DB
    db_team_deleted = crud_team.get_team(db, team_id=uuid.UUID(team_id), include_deleted=True)
    assert db_team_deleted is not None
    # Verify cannot get team normally (without include_deleted)
    db_team_not_found = crud_team.get_team(db, team_id=uuid.UUID(team_id))
    assert db_team_not_found is None
    # Verify API returns 404 when trying to get the deleted team
    response_get_deleted = client.get(f"/api/v1/teams/{team_id}", headers=auth_headers)
    assert response_get_deleted.status_code == 404
