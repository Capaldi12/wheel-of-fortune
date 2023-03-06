"""Custom middlewares for the application."""

from .auth import auth_middleware, auth_required
from .error_handling import error_handling_middleware
