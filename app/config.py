"""Configuration classes for the application."""
__all__ = ['Config', 'BotConfig', 'DatabaseConfig',
           'AdminConfig', 'SessionConfig']

from typing import Optional
from dataclasses import dataclass, field

import yaml
import json


class BaseConfig:
    """Config that can read itself from files."""

    @classmethod
    def from_dict(cls, d: dict):
        """Create a config object from a dictionary."""

        args = {}
        for attr, type_ in cls.__annotations__.items():
            # I know we'd miss things like Optional[SomeConfig]
            # It's not that important in this application
            if attr in d and isinstance(type_, type) \
                    and issubclass(type_, BaseConfig):
                args[attr] = type_.from_dict(d[attr])
            else:
                if (value := d.get(attr)) is not None:
                    args[attr] = value

        return cls(**args)  # type: ignore

    @classmethod
    def from_yaml(cls, path: str):
        """Read config from a YAML/YML file."""

        with open(path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)

        return cls.from_dict(raw_config)

    @classmethod
    def from_json(cls, path):
        """Read config from a JSON file."""

        with open(path, 'r', encoding='utf-8') as f:
            raw_config = json.load(f)

        return cls.from_dict(raw_config)


@dataclass
class DatabaseConfig(BaseConfig):
    """Configuration for the database."""

    host: str = 'localhost'
    port: int = 5432
    user: str = 'postgres'
    password: str = 'postgres'
    database: str = 'kts'
    echo: Optional[bool] = False

    @property
    def url(self):
        """Connection url."""

        return f'postgresql+asyncpg://{self.user}:{self.password}' \
               f'@{self.host}:{self.port}/{self.database}'


@dataclass
class SessionConfig(BaseConfig):
    """Configuration for the session storage."""
    key: str


@dataclass
class AdminConfig(BaseConfig):
    """Configuration for the admin module."""

    email: str
    password: str


@dataclass
class BotConfig(BaseConfig):
    """Configuration for vk bot."""

    token: str
    group_id: int
    debug: bool
    app_id: int
    chats: list[str] = field(default_factory=list)


@dataclass
class Config(BaseConfig):
    """Main application configuration."""

    database: DatabaseConfig
    session: SessionConfig
    admin: AdminConfig
    bot: BotConfig
