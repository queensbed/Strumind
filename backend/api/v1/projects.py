from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from api.v1.auth import get_current_user
import uuid

router = APIRouter()

# Pydantic models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    building_type: Optional[str] = None
    location: Optional[str] = None
    code_standard: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    building_type: Optional[str] = None
    location: Optional[str] = None
    code_standard: Optional[str] = None
    owner_email: str
    created_at: datetime
    updated_at: datetime

# In-memory project storage
fake_projects_db = {}

@router.get('/', response_model=List[ProjectResponse])
async def list_projects(current_user: dict = Depends(get_current_user)):
    """List all projects for the current user"""
    user_projects = [
        project for project in fake_projects_db.values() 
        if project["owner_email"] == current_user["email"]
    ]
    return user_projects

@router.get('/{project_id}', response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific project"""
    project = fake_projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user owns the project
    if project["owner_email"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return project

@router.post('/', response_model=ProjectResponse)
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Create a new project"""
    project_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    project_data = {
        "id": project_id,
        "name": project.name,
        "description": project.description,
        "building_type": project.building_type,
        "location": project.location,
        "code_standard": project.code_standard,
        "owner_email": current_user["email"],
        "created_at": now,
        "updated_at": now
    }
    
    fake_projects_db[project_id] = project_data
    return project_data

@router.put('/{project_id}', response_model=ProjectResponse)
async def update_project(project_id: str, project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Update a project"""
    existing_project = fake_projects_db.get(project_id)
    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user owns the project
    if existing_project["owner_email"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update project data
    existing_project.update({
        "name": project.name,
        "description": project.description,
        "building_type": project.building_type,
        "location": project.location,
        "code_standard": project.code_standard,
        "updated_at": datetime.utcnow()
    })
    
    return existing_project

@router.delete('/{project_id}')
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a project"""
    project = fake_projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user owns the project
    if project["owner_email"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del fake_projects_db[project_id]
    return {"message": "Project deleted successfully"} 