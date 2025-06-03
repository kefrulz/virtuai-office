# VirtuAI Office - Core Backend Module
"""
Core backend module initialization for VirtuAI Office.
This module contains shared utilities, configurations, and base classes.
"""

from .config import settings, get_settings
from .database import Base, engine, SessionLocal, get_db
from .logging import setup_logging, get_logger
from .exceptions import VirtuAIException, AgentException, TaskException

__version__ = "1.0.0"
__all__ = [
    "settings",
    "get_settings",
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "setup_logging",
    "get_logger",
    "VirtuAIException",
    "AgentException",
    "TaskException"
]
