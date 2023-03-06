"""Declarative base for all models."""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(DeclarativeBase, MappedAsDataclass):
    """Declarative base for all models."""
    pass
