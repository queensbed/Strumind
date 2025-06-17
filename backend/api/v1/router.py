"""
Main API router for StruMind Backend v1
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .organizations import router as organizations_router
from .projects import router as projects_router
from .models.router import router as models_router
from .analysis.router import router as analysis_router
from .design.router import router as design_router
from .results.router import router as results_router
from .files.router import router as files_router

api_router = APIRouter()

@api_router.get("/health")
async def api_health():
    """API v1 health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "strumind-api-v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "projects": "/api/v1/projects",
            "models": "/api/v1/models",
            "analysis": "/api/v1/analysis",
            "design": "/api/v1/design",
            "results": "/api/v1/results",
            "files": "/api/v1/files"
        }
    }

# Include all sub-routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    organizations_router,
    prefix="/organizations",
    tags=["Organizations"]
)

api_router.include_router(
    projects_router,
    prefix="/projects",
    tags=["Projects"]
)

api_router.include_router(
    models_router,
    prefix="/models",
    tags=["Structural Models"]
)

api_router.include_router(
    analysis_router,
    prefix="/analysis",
    tags=["Structural Analysis"]
)

api_router.include_router(
    design_router,
    prefix="/design",
    tags=["Structural Design"]
)

api_router.include_router(
    results_router,
    prefix="/results",
    tags=["Results & Visualization"]
)

api_router.include_router(
    files_router,
    prefix="/files",
    tags=["File Management"]
)