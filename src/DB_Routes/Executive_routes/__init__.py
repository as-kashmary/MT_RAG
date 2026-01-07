# Executive Routes Package
# This package contains all executive portal API routes

from .Executive_routes import router as executive_router
from .Analytics_routes import router as analytics_router

__all__ = [
    'executive_router',
    'analytics_router'
]
