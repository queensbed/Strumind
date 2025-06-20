"""
Collaboration and team management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from db.database import get_db
from db.models import User, Project, Organization
from auth.auth import get_current_user
from auth.rbac import require_permission, Permission, RBACManager, AuditLogger

router = APIRouter(prefix="/collaboration", tags=["collaboration"])

# Pydantic models
class ProjectMember(BaseModel):
    user_id: str
    role: str = Field(..., description="Role in project: owner, admin, engineer, designer, viewer")
    permissions: List[str] = Field(default_factory=list)
    added_at: datetime
    added_by: str

class ProjectMemberCreate(BaseModel):
    user_id: str
    role: str = Field(..., regex="^(owner|admin|engineer|designer|viewer)$")
    permissions: List[str] = Field(default_factory=list)

class ProjectMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, regex="^(owner|admin|engineer|designer|viewer)$")
    permissions: Optional[List[str]] = None

class ProjectInvitation(BaseModel):
    id: str
    project_id: str
    email: str
    role: str
    invited_by: str
    invited_at: datetime
    expires_at: datetime
    status: str = Field(..., description="pending, accepted, declined, expired")

class ProjectInvitationCreate(BaseModel):
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    role: str = Field(..., regex="^(admin|engineer|designer|viewer)$")
    message: Optional[str] = None

class ActivityLog(BaseModel):
    id: str
    project_id: str
    user_id: str
    action: str
    resource: str
    details: Dict[str, Any]
    timestamp: datetime

class ProjectVersion(BaseModel):
    id: str
    project_id: str
    version_number: str
    description: str
    created_by: str
    created_at: datetime
    file_size: int
    checksum: str

class ProjectVersionCreate(BaseModel):
    description: str
    auto_increment: bool = True

# In-memory storage for demo (would use database in production)
project_members = {}
project_invitations = {}
activity_logs = {}
project_versions = {}

@router.get("/projects/{project_id}/members", response_model=List[ProjectMember])
async def get_project_members(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all members of a project"""
    
    # Check if user has access to project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not RBACManager.can_access_project(current_user, project):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get project members
    members = project_members.get(project_id, [])
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="VIEW_PROJECT_MEMBERS",
        resource=f"project:{project_id}"
    )
    
    return members

@router.post("/projects/{project_id}/members", response_model=ProjectMember)
async def add_project_member(
    project_id: str,
    member_data: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a member to a project"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.UPDATE_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user exists
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is already a member
    if project_id in project_members:
        existing_member = next(
            (m for m in project_members[project_id] if m['user_id'] == member_data.user_id),
            None
        )
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a project member")
    
    # Create new member
    new_member = ProjectMember(
        user_id=member_data.user_id,
        role=member_data.role,
        permissions=member_data.permissions,
        added_at=datetime.utcnow(),
        added_by=str(current_user.id)
    )
    
    # Add to project members
    if project_id not in project_members:
        project_members[project_id] = []
    project_members[project_id].append(new_member.dict())
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="ADD_PROJECT_MEMBER",
        resource=f"project:{project_id}",
        details={"added_user": member_data.user_id, "role": member_data.role}
    )
    
    # Add to activity log
    activity = ActivityLog(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=str(current_user.id),
        action="MEMBER_ADDED",
        resource="project_member",
        details={"user_id": member_data.user_id, "role": member_data.role},
        timestamp=datetime.utcnow()
    )
    
    if project_id not in activity_logs:
        activity_logs[project_id] = []
    activity_logs[project_id].append(activity.dict())
    
    return new_member

@router.put("/projects/{project_id}/members/{user_id}", response_model=ProjectMember)
async def update_project_member(
    project_id: str,
    user_id: str,
    member_update: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project member's role and permissions"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.UPDATE_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Find and update member
    if project_id not in project_members:
        raise HTTPException(status_code=404, detail="Project has no members")
    
    member = next(
        (m for m in project_members[project_id] if m['user_id'] == user_id),
        None
    )
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Update member data
    if member_update.role:
        member['role'] = member_update.role
    if member_update.permissions is not None:
        member['permissions'] = member_update.permissions
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="UPDATE_PROJECT_MEMBER",
        resource=f"project:{project_id}",
        details={"updated_user": user_id, "changes": member_update.dict(exclude_unset=True)}
    )
    
    return ProjectMember(**member)

@router.delete("/projects/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from a project"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.UPDATE_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Find and remove member
    if project_id not in project_members:
        raise HTTPException(status_code=404, detail="Project has no members")
    
    member_index = next(
        (i for i, m in enumerate(project_members[project_id]) if m['user_id'] == user_id),
        None
    )
    
    if member_index is None:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Remove member
    removed_member = project_members[project_id].pop(member_index)
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="REMOVE_PROJECT_MEMBER",
        resource=f"project:{project_id}",
        details={"removed_user": user_id}
    )
    
    return {"message": "Member removed successfully"}

@router.post("/projects/{project_id}/invite", response_model=ProjectInvitation)
async def invite_user_to_project(
    project_id: str,
    invitation_data: ProjectInvitationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join a project"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.UPDATE_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create invitation
    invitation = ProjectInvitation(
        id=str(uuid.uuid4()),
        project_id=project_id,
        email=invitation_data.email,
        role=invitation_data.role,
        invited_by=str(current_user.id),
        invited_at=datetime.utcnow(),
        expires_at=datetime.utcnow().replace(day=datetime.utcnow().day + 7),  # 7 days
        status="pending"
    )
    
    # Store invitation
    if project_id not in project_invitations:
        project_invitations[project_id] = []
    project_invitations[project_id].append(invitation.dict())
    
    # Send invitation email (background task)
    background_tasks.add_task(
        send_invitation_email,
        invitation.email,
        project.name,
        current_user.email,
        invitation_data.message
    )
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="INVITE_USER",
        resource=f"project:{project_id}",
        details={"email": invitation_data.email, "role": invitation_data.role}
    )
    
    return invitation

@router.get("/projects/{project_id}/invitations", response_model=List[ProjectInvitation])
async def get_project_invitations(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending invitations for a project"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.READ_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    invitations = project_invitations.get(project_id, [])
    return [ProjectInvitation(**inv) for inv in invitations]

@router.post("/invitations/{invitation_id}/accept")
async def accept_project_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a project invitation"""
    
    # Find invitation
    invitation = None
    project_id = None
    
    for pid, invitations in project_invitations.items():
        for inv in invitations:
            if inv['id'] == invitation_id:
                invitation = inv
                project_id = pid
                break
        if invitation:
            break
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Invitation is not pending")
    
    if invitation['email'] != current_user.email:
        raise HTTPException(status_code=403, detail="Invitation is not for this user")
    
    # Check if invitation is expired
    if datetime.fromisoformat(invitation['expires_at']) < datetime.utcnow():
        invitation['status'] = 'expired'
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Add user to project
    new_member = ProjectMember(
        user_id=str(current_user.id),
        role=invitation['role'],
        permissions=[],
        added_at=datetime.utcnow(),
        added_by=invitation['invited_by']
    )
    
    if project_id not in project_members:
        project_members[project_id] = []
    project_members[project_id].append(new_member.dict())
    
    # Update invitation status
    invitation['status'] = 'accepted'
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="ACCEPT_INVITATION",
        resource=f"project:{project_id}"
    )
    
    return {"message": "Invitation accepted successfully"}

@router.get("/projects/{project_id}/activity", response_model=List[ActivityLog])
async def get_project_activity(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project activity log"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.READ_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    activities = activity_logs.get(project_id, [])
    
    # Sort by timestamp (newest first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Apply pagination
    paginated_activities = activities[offset:offset + limit]
    
    return [ActivityLog(**activity) for activity in paginated_activities]

@router.post("/projects/{project_id}/versions", response_model=ProjectVersion)
async def create_project_version(
    project_id: str,
    version_data: ProjectVersionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new version of the project"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.UPDATE_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get current versions
    versions = project_versions.get(project_id, [])
    
    # Generate version number
    if version_data.auto_increment:
        version_number = f"v{len(versions) + 1}.0"
    else:
        version_number = f"v{len(versions) + 1}.0"  # Simplified for demo
    
    # Create new version
    new_version = ProjectVersion(
        id=str(uuid.uuid4()),
        project_id=project_id,
        version_number=version_number,
        description=version_data.description,
        created_by=str(current_user.id),
        created_at=datetime.utcnow(),
        file_size=0,  # Would calculate actual file size
        checksum="dummy_checksum"  # Would calculate actual checksum
    )
    
    # Store version
    if project_id not in project_versions:
        project_versions[project_id] = []
    project_versions[project_id].append(new_version.dict())
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="CREATE_VERSION",
        resource=f"project:{project_id}",
        details={"version": version_number, "description": version_data.description}
    )
    
    # Add to activity log
    activity = ActivityLog(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=str(current_user.id),
        action="VERSION_CREATED",
        resource="project_version",
        details={"version": version_number, "description": version_data.description},
        timestamp=datetime.utcnow()
    )
    
    if project_id not in activity_logs:
        activity_logs[project_id] = []
    activity_logs[project_id].append(activity.dict())
    
    return new_version

@router.get("/projects/{project_id}/versions", response_model=List[ProjectVersion])
async def get_project_versions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all versions of a project"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.READ_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    versions = project_versions.get(project_id, [])
    
    # Sort by creation date (newest first)
    versions.sort(key=lambda x: x['created_at'], reverse=True)
    
    return [ProjectVersion(**version) for version in versions]

@router.post("/projects/{project_id}/versions/{version_id}/restore")
async def restore_project_version(
    project_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restore a project to a specific version"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.UPDATE_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Find version
    versions = project_versions.get(project_id, [])
    version = next((v for v in versions if v['id'] == version_id), None)
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # In a real implementation, this would restore the project data
    # For demo, we'll just log the action
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="RESTORE_VERSION",
        resource=f"project:{project_id}",
        details={"version_id": version_id, "version_number": version['version_number']}
    )
    
    # Add to activity log
    activity = ActivityLog(
        id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=str(current_user.id),
        action="VERSION_RESTORED",
        resource="project_version",
        details={"version_id": version_id, "version_number": version['version_number']},
        timestamp=datetime.utcnow()
    )
    
    if project_id not in activity_logs:
        activity_logs[project_id] = []
    activity_logs[project_id].append(activity.dict())
    
    return {"message": f"Project restored to version {version['version_number']}"}

# Helper functions
async def send_invitation_email(email: str, project_name: str, inviter_email: str, message: str = None):
    """Send invitation email (background task)"""
    
    # In a real implementation, this would send an actual email
    # For demo, we'll just log it
    print(f"Sending invitation email to {email} for project {project_name}")
    print(f"Invited by: {inviter_email}")
    if message:
        print(f"Message: {message}")

# Real-time collaboration endpoints (WebSocket would be used in production)
@router.get("/projects/{project_id}/online-users")
async def get_online_users(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users currently online in the project"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.READ_PROJECT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # In a real implementation, this would track online users via WebSocket connections
    # For demo, return mock data
    online_users = [
        {
            "user_id": str(current_user.id),
            "name": current_user.full_name,
            "email": current_user.email,
            "last_activity": datetime.utcnow().isoformat(),
            "current_view": "3d_model"
        }
    ]
    
    return online_users

@router.post("/projects/{project_id}/lock-element")
async def lock_element(
    project_id: str,
    element_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lock an element for editing (collaborative editing)"""
    
    # Check permissions
    if not RBACManager.has_permission(current_user.role, Permission.UPDATE_MODEL):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    element_id = element_data.get('element_id')
    element_type = element_data.get('element_type')
    
    # In a real implementation, this would manage element locks in a database
    # For demo, just return success
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="LOCK_ELEMENT",
        resource=f"project:{project_id}",
        details={"element_id": element_id, "element_type": element_type}
    )
    
    return {
        "message": "Element locked successfully",
        "locked_by": str(current_user.id),
        "locked_at": datetime.utcnow().isoformat()
    }

@router.post("/projects/{project_id}/unlock-element")
async def unlock_element(
    project_id: str,
    element_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlock an element (collaborative editing)"""
    
    element_id = element_data.get('element_id')
    element_type = element_data.get('element_type')
    
    # Log activity
    AuditLogger.log_event(
        user_id=str(current_user.id),
        action="UNLOCK_ELEMENT",
        resource=f"project:{project_id}",
        details={"element_id": element_id, "element_type": element_type}
    )
    
    return {"message": "Element unlocked successfully"}