"""
Logger Module - Immutable Hybrid Logging System
Provides cryptographically secure logging with WORM fallback
"""

from .logger import (
    ImmutableLogger,
    ChainedLogEntry,
    initialize_logger,
    get_logger
)

from .queue_manager import QueueManager

from .event_types import (
    SecurityEvent,
    ComponentType,
    RiskLevel,
    SystemEvents,
    EventCategory,
    NISTCategory,
    EventClassification,
)

from .log_config import LogConfig

from .socarrat_client import SocarratClient

__all__ = [
    # Logger
    'ImmutableLogger',
    'ChainedLogEntry',
    'initialize_logger',
    'get_logger',
    
    # Queue
    'QueueManager',
    
    # Events
    'SecurityEvent',
    'ComponentType',
    'RiskLevel',
    'SystemEvents',
    'EventCategory',
    'NISTCategory',
    'EventClassification',
    
    # Configuration
    'LogConfig',
    
    # WORM Client
    'SocarratClient',
]
