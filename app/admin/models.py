"""Database models of the admin module."""
__all__ = ['Admin']

from dataclasses import InitVar
from hashlib import sha256

from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Admin(Base):
    """Application admin."""

    __tablename__ = 'admin'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    email: Mapped[str] = mapped_column(unique=True)

    password: InitVar[str]  # To initially set the password
    password_hash: Mapped[str] = mapped_column(init=False, nullable=False)

    def __post_init__(self, password: str):
        self.password_hash: str = sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Check if the password is correct."""

        return sha256(password.encode()).hexdigest() == self.password_hash
