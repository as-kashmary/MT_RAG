# Admin Routes Package
# This package contains all admin portal API routes

from .AdminAuth_routes import router as auth_router
from .AdminDocument_routes import router as document_router
from .AdminProduct_routes import router as product_router
from .AdminAnalytics_routes import router as analytics_router

__all__ = [
    'auth_router',
    'document_router', 
    'product_router',
    'analytics_router'
]
