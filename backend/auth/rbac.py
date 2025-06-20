"""
Role-Based Access Control (RBAC) system for StruMind
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from functools import wraps
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User, Organization, Project
import jwt
from core.config import settings

class Role(str, Enum):
    """User roles in the system"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ENGINEER = "engineer"
    DESIGNER = "designer"
    VIEWER = "viewer"

class Permission(str, Enum):
    """System permissions"""
    # User management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Organization management
    CREATE_ORGANIZATION = "create_organization"
    READ_ORGANIZATION = "read_organization"
    UPDATE_ORGANIZATION = "update_organization"
    DELETE_ORGANIZATION = "delete_organization"
    
    # Project management
    CREATE_PROJECT = "create_project"
    READ_PROJECT = "read_project"
    UPDATE_PROJECT = "update_project"
    DELETE_PROJECT = "delete_project"
    
    # Model management
    CREATE_MODEL = "create_model"
    READ_MODEL = "read_model"
    UPDATE_MODEL = "update_model"
    DELETE_MODEL = "delete_model"
    
    # Analysis
    RUN_ANALYSIS = "run_analysis"
    READ_ANALYSIS = "read_analysis"
    
    # Design
    RUN_DESIGN = "run_design"
    READ_DESIGN = "read_design"
    
    # Export/Import
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    
    # System administration
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"

# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.SUPER_ADMIN: [
        # All permissions
        Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER, Permission.DELETE_USER,
        Permission.CREATE_ORGANIZATION, Permission.READ_ORGANIZATION, Permission.UPDATE_ORGANIZATION, Permission.DELETE_ORGANIZATION,
        Permission.CREATE_PROJECT, Permission.READ_PROJECT, Permission.UPDATE_PROJECT, Permission.DELETE_PROJECT,
        Permission.CREATE_MODEL, Permission.READ_MODEL, Permission.UPDATE_MODEL, Permission.DELETE_MODEL,
        Permission.RUN_ANALYSIS, Permission.READ_ANALYSIS,
        Permission.RUN_DESIGN, Permission.READ_DESIGN,
        Permission.EXPORT_DATA, Permission.IMPORT_DATA,
        Permission.MANAGE_SYSTEM, Permission.VIEW_LOGS
    ],
    
    Role.ADMIN: [
        # Organization and project management
        Permission.READ_USER, Permission.UPDATE_USER,
        Permission.READ_ORGANIZATION, Permission.UPDATE_ORGANIZATION,
        Permission.CREATE_PROJECT, Permission.READ_PROJECT, Permission.UPDATE_PROJECT, Permission.DELETE_PROJECT,
        Permission.CREATE_MODEL, Permission.READ_MODEL, Permission.UPDATE_MODEL, Permission.DELETE_MODEL,
        Permission.RUN_ANALYSIS, Permission.READ_ANALYSIS,
        Permission.RUN_DESIGN, Permission.READ_DESIGN,
        Permission.EXPORT_DATA, Permission.IMPORT_DATA
    ],
    
    Role.ENGINEER: [
        # Full engineering capabilities
        Permission.READ_USER,
        Permission.READ_ORGANIZATION,
        Permission.CREATE_PROJECT, Permission.READ_PROJECT, Permission.UPDATE_PROJECT,
        Permission.CREATE_MODEL, Permission.READ_MODEL, Permission.UPDATE_MODEL,
        Permission.RUN_ANALYSIS, Permission.READ_ANALYSIS,
        Permission.RUN_DESIGN, Permission.READ_DESIGN,
        Permission.EXPORT_DATA, Permission.IMPORT_DATA
    ],
    
    Role.DESIGNER: [
        # Design and modeling
        Permission.READ_USER,
        Permission.READ_ORGANIZATION,
        Permission.READ_PROJECT, Permission.UPDATE_PROJECT,
        Permission.CREATE_MODEL, Permission.READ_MODEL, Permission.UPDATE_MODEL,
        Permission.READ_ANALYSIS,
        Permission.RUN_DESIGN, Permission.READ_DESIGN,
        Permission.EXPORT_DATA
    ],
    
    Role.VIEWER: [
        # Read-only access
        Permission.READ_USER,
        Permission.READ_ORGANIZATION,
        Permission.READ_PROJECT,
        Permission.READ_MODEL,
        Permission.READ_ANALYSIS,
        Permission.READ_DESIGN
    ]
}

class RBACManager:
    """Role-Based Access Control Manager"""
    
    @staticmethod
    def get_user_permissions(user_role: Role) -> List[Permission]:
        """Get permissions for a user role"""
        return ROLE_PERMISSIONS.get(user_role, [])
    
    @staticmethod
    def has_permission(user_role: Role, required_permission: Permission) -> bool:
        """Check if user role has required permission"""
        user_permissions = RBACManager.get_user_permissions(user_role)
        return required_permission in user_permissions
    
    @staticmethod
    def can_access_organization(user: User, organization_id: str) -> bool:
        """Check if user can access organization"""
        if user.role == Role.SUPER_ADMIN:
            return True
        
        # Check if user belongs to the organization
        return str(user.organization_id) == organization_id
    
    @staticmethod
    def can_access_project(user: User, project: Project) -> bool:
        """Check if user can access project"""
        if user.role == Role.SUPER_ADMIN:
            return True
        
        # Check if user belongs to the same organization as the project
        if str(user.organization_id) != str(project.organization_id):
            return False
        
        # Check if user is the project owner or has appropriate role
        if str(user.id) == str(project.created_by_id):
            return True
        
        # Admin and Engineer can access all projects in their organization
        if user.role in [Role.ADMIN, Role.ENGINEER]:
            return True
        
        # Designer and Viewer need to be explicitly granted access
        # This would be implemented with a project_members table
        return False

def require_permission(required_permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current user from kwargs or dependencies
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not RBACManager.has_permission(current_user.role, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{required_permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(required_roles: List[Role]):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role must be one of: {[role.value for role in required_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_organization_access(organization_id_param: str = "organization_id"):
    """Decorator to require organization access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            organization_id = kwargs.get(organization_id_param)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not RBACManager.can_access_organization(current_user, organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to organization denied"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_project_access():
    """Decorator to require project access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            project_id = kwargs.get('project_id')
            db = kwargs.get('db')
            
            if not current_user or not project_id or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get project from database
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )
            
            if not RBACManager.can_access_project(current_user, project):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to project denied"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Input validation and sanitization
class InputValidator:
    """Input validation and sanitization utilities"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        
        # Remove potentially dangerous characters
        sanitized = value.strip()
        
        # Check length
        if len(sanitized) > max_length:
            raise ValueError(f"String too long (max {max_length} characters)")
        
        # Basic XSS prevention
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            if char in sanitized:
                sanitized = sanitized.replace(char, '')
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        import re
        
        email = InputValidator.sanitize_string(email, 254)
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email.lower()
    
    @staticmethod
    def validate_numeric(value: Any, min_val: float = None, max_val: float = None) -> float:
        """Validate numeric input"""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValueError("Value must be numeric")
        
        if min_val is not None and num_value < min_val:
            raise ValueError(f"Value must be >= {min_val}")
        
        if max_val is not None and num_value > max_val:
            raise ValueError(f"Value must be <= {max_val}")
        
        return num_value
    
    @staticmethod
    def validate_uuid(value: str) -> str:
        """Validate UUID format"""
        import uuid
        
        try:
            uuid_obj = uuid.UUID(value)
            return str(uuid_obj)
        except ValueError:
            raise ValueError("Invalid UUID format")

# Rate limiting
class RateLimiter:
    """Simple rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        import time
        
        current_time = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < window
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(current_time)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit: int = 100, window: int = 3600):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user identifier (IP or user ID)
            current_user = kwargs.get('current_user')
            key = str(current_user.id) if current_user else "anonymous"
            
            if not rate_limiter.is_allowed(key, limit, window):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Audit logging
class AuditLogger:
    """Audit logging for security events"""
    
    @staticmethod
    def log_event(user_id: str, action: str, resource: str, details: Dict[str, Any] = None):
        """Log security event"""
        import logging
        from datetime import datetime
        
        logger = logging.getLogger("audit")
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {}
        }
        
        logger.info(f"AUDIT: {event}")
    
    @staticmethod
    def log_login(user_id: str, success: bool, ip_address: str = None):
        """Log login attempt"""
        AuditLogger.log_event(
            user_id=user_id,
            action="LOGIN",
            resource="AUTH",
            details={
                "success": success,
                "ip_address": ip_address
            }
        )
    
    @staticmethod
    def log_permission_denied(user_id: str, action: str, resource: str):
        """Log permission denied event"""
        AuditLogger.log_event(
            user_id=user_id,
            action="PERMISSION_DENIED",
            resource=resource,
            details={"attempted_action": action}
        )