"""
Security Module - Layer 1 Logging and Security Architecture
Provides immutable logging, event classification, and forensic traceability
"""

from .logger import (
    ImmutableLogger,
    ChainedLogEntry,
    initialize_logger,
    get_logger,
    QueueManager,
    SecurityEvent,
    ComponentType,
    RiskLevel,
    SystemEvents,
    EventCategory,
    NISTCategory,
    EventClassification,
    LogConfig,
    SocarratClient
)

__all__ = [
    # Core Logger
    'ImmutableLogger',
    'ChainedLogEntry',
    'initialize_logger',
    'get_logger',
    
    # Queue Management
    'QueueManager',
    
    # Event Types
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
