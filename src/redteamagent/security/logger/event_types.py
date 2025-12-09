"""
Security event types, risk levels, and event classification

Compliant with NIST SP 800-92: Guide to Computer Security Log Management
All security events are classified using standardized categories 
with mappings to NIST framework.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

class RiskLevel(Enum):
    """Risk levels for security event classification"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComponentType(Enum):
    """System components that can generate security events"""
    REDTEAM_AGENT = "RedTeamAgent"
    REACT = "ReAct"
    ACT = "Act"
    REASON = "Reason"
    PLANNER = "Planner"
    KILL_SWITCH = "KillSwitch"


class NISTCategory(Enum):
    """NIST SP 800-92 Log Categories"""
    ACCOUNT_LOGON = "Account Logon Events"
    OBJECT_ACCESS = "Object Access"
    PRIVILEGE_USE = "Privilege Use"
    DETAILED_TRACKING = "Detailed Tracking"
    POLICY_CHANGE = "Policy Change"
    SYSTEM_EVENTS = "System Events"
    SECURITY_STATE_CHANGE = "Security State Change"


class EventCategory(Enum):
    """
    Standardized security event categories mapped to NIST SP 800-92 framework
    """
    
    # Authentication & Access Control
    AUTHENTICATION_SUCCESS = "Authentication Success"
    AUTHENTICATION_FAILURE = "Authentication Failure"
    AUTHORIZATION_CHANGE = "Authorization Change"
    ACCOUNT_CREATED = "Account Created"
    ACCOUNT_DELETED = "Account Deleted"
    ACCOUNT_MODIFIED = "Account Modified"
    
    # Execution & Command Events
    PROCESS_CREATION = "Process Creation"
    PROCESS_TERMINATION = "Process Termination"
    COMMAND_EXECUTION = "Command Execution"
    SCRIPT_EXECUTION = "Script Execution"
    EXTERNAL_COMMAND = "External Command"
    
    # File & Object Access
    FILE_ACCESSED = "File Accessed"
    FILE_MODIFIED = "File Modified"
    FILE_DELETED = "File Deleted"
    FILE_CREATED = "File Created"
    REGISTRY_MODIFIED = "Registry Modified"
    
    # Network & Communication
    NETWORK_CONNECTION = "Network Connection"
    DNS_QUERY = "DNS Query"
    NETWORK_TRAFFIC = "Network Traffic"
    API_CALL = "API Call"
    EXTERNAL_COMMUNICATION = "External Communication"
    
    # Security & Policy
    SECURITY_POLICY_CHANGED = "Security Policy Changed"
    FIREWALL_RULE_CHANGED = "Firewall Rule Changed"
    AUDIT_POLICY_CHANGED = "Audit Policy Changed"
    PERMISSION_CHANGED = "Permission Changed"
    SECURITY_GROUP_CHANGED = "Security Group Changed"
    
    # System & Configuration
    SYSTEM_STARTUP = "System Startup"
    SYSTEM_SHUTDOWN = "System Shutdown"
    SYSTEM_RESTART = "System Restart"
    CONFIGURATION_CHANGED = "Configuration Changed"
    SERVICE_STARTED = "Service Started"
    SERVICE_STOPPED = "Service Stopped"
    
    # Security Detection
    ANOMALY_DETECTED = "Anomaly Detected"
    INTRUSION_ATTEMPT = "Intrusion Attempt"
    MALWARE_DETECTED = "Malware Detected"
    SUSPICIOUS_ACTIVITY = "Suspicious Activity"
    POLICY_VIOLATION = "Policy Violation"
    
    # Red Team Operations
    AGENT_INITIALIZED = "Agent Initialized"
    PLAN_GENERATED = "Plan Generated"
    TASK_STARTED = "Task Started"
    TASK_COMPLETED = "Task Completed"
    TASK_FAILED = "Task Failed"
    RECONNAISSANCE = "Reconnaissance"
    EXPLOITATION_ATTEMPT = "Exploitation Attempt"
    PERSISTENCE_ESTABLISHED = "Persistence Established"
    DATA_EXFILTRATION = "Data Exfiltration"
    
    # Operational Events
    OPERATIONAL_EVENT = "Operational Event"
    ERROR_EVENT = "Error Event"
    WARNING_EVENT = "Warning Event"
    INFO_EVENT = "Info Event"
    DEBUG_EVENT = "Debug Event"


class EventClassification:
    """
    Event classification mapping events to NIST categories
    Provides standardized classification for security events
    """
    
    # Mapping from EventCategory to NIST Category
    NIST_MAPPING: Dict[EventCategory, NISTCategory] = {
        # Authentication & Access Control
        EventCategory.AUTHENTICATION_SUCCESS: NISTCategory.ACCOUNT_LOGON,
        EventCategory.AUTHENTICATION_FAILURE: NISTCategory.ACCOUNT_LOGON,
        EventCategory.AUTHORIZATION_CHANGE: NISTCategory.POLICY_CHANGE,
        EventCategory.ACCOUNT_CREATED: NISTCategory.ACCOUNT_LOGON,
        EventCategory.ACCOUNT_DELETED: NISTCategory.ACCOUNT_LOGON,
        EventCategory.ACCOUNT_MODIFIED: NISTCategory.ACCOUNT_LOGON,
        
        # Execution & Command Events
        EventCategory.PROCESS_CREATION: NISTCategory.DETAILED_TRACKING,
        EventCategory.PROCESS_TERMINATION: NISTCategory.DETAILED_TRACKING,
        EventCategory.COMMAND_EXECUTION: NISTCategory.DETAILED_TRACKING,
        EventCategory.SCRIPT_EXECUTION: NISTCategory.DETAILED_TRACKING,
        EventCategory.EXTERNAL_COMMAND: NISTCategory.DETAILED_TRACKING,
        
        # File & Object Access
        EventCategory.FILE_ACCESSED: NISTCategory.OBJECT_ACCESS,
        EventCategory.FILE_MODIFIED: NISTCategory.OBJECT_ACCESS,
        EventCategory.FILE_DELETED: NISTCategory.OBJECT_ACCESS,
        EventCategory.FILE_CREATED: NISTCategory.OBJECT_ACCESS,
        EventCategory.REGISTRY_MODIFIED: NISTCategory.OBJECT_ACCESS,
        
        # Network & Communication
        EventCategory.NETWORK_CONNECTION: NISTCategory.OBJECT_ACCESS,
        EventCategory.DNS_QUERY: NISTCategory.DETAILED_TRACKING,
        EventCategory.NETWORK_TRAFFIC: NISTCategory.OBJECT_ACCESS,
        EventCategory.API_CALL: NISTCategory.OBJECT_ACCESS,
        EventCategory.EXTERNAL_COMMUNICATION: NISTCategory.DETAILED_TRACKING,
        
        # Security & Policy
        EventCategory.SECURITY_POLICY_CHANGED: NISTCategory.POLICY_CHANGE,
        EventCategory.FIREWALL_RULE_CHANGED: NISTCategory.POLICY_CHANGE,
        EventCategory.AUDIT_POLICY_CHANGED: NISTCategory.POLICY_CHANGE,
        EventCategory.PERMISSION_CHANGED: NISTCategory.POLICY_CHANGE,
        EventCategory.SECURITY_GROUP_CHANGED: NISTCategory.POLICY_CHANGE,
        
        # System & Configuration
        EventCategory.SYSTEM_STARTUP: NISTCategory.SYSTEM_EVENTS,
        EventCategory.SYSTEM_SHUTDOWN: NISTCategory.SYSTEM_EVENTS,
        EventCategory.SYSTEM_RESTART: NISTCategory.SYSTEM_EVENTS,
        EventCategory.CONFIGURATION_CHANGED: NISTCategory.SECURITY_STATE_CHANGE,
        EventCategory.SERVICE_STARTED: NISTCategory.SYSTEM_EVENTS,
        EventCategory.SERVICE_STOPPED: NISTCategory.SYSTEM_EVENTS,
        
        # Security Detection
        EventCategory.ANOMALY_DETECTED: NISTCategory.SECURITY_STATE_CHANGE,
        EventCategory.INTRUSION_ATTEMPT: NISTCategory.SECURITY_STATE_CHANGE,
        EventCategory.MALWARE_DETECTED: NISTCategory.SECURITY_STATE_CHANGE,
        EventCategory.SUSPICIOUS_ACTIVITY: NISTCategory.SECURITY_STATE_CHANGE,
        EventCategory.POLICY_VIOLATION: NISTCategory.SECURITY_STATE_CHANGE,
        
        # Red Team Operations
        EventCategory.AGENT_INITIALIZED: NISTCategory.SYSTEM_EVENTS,
        EventCategory.PLAN_GENERATED: NISTCategory.DETAILED_TRACKING,
        EventCategory.TASK_STARTED: NISTCategory.DETAILED_TRACKING,
        EventCategory.TASK_COMPLETED: NISTCategory.DETAILED_TRACKING,
        EventCategory.TASK_FAILED: NISTCategory.DETAILED_TRACKING,
        EventCategory.RECONNAISSANCE: NISTCategory.DETAILED_TRACKING,
        EventCategory.EXPLOITATION_ATTEMPT: NISTCategory.SECURITY_STATE_CHANGE,
        EventCategory.PERSISTENCE_ESTABLISHED: NISTCategory.SECURITY_STATE_CHANGE,
        EventCategory.DATA_EXFILTRATION: NISTCategory.OBJECT_ACCESS,
        
        # Operational Events
        EventCategory.OPERATIONAL_EVENT: NISTCategory.SYSTEM_EVENTS,
        EventCategory.ERROR_EVENT: NISTCategory.SYSTEM_EVENTS,
        EventCategory.WARNING_EVENT: NISTCategory.SYSTEM_EVENTS,
        EventCategory.INFO_EVENT: NISTCategory.SYSTEM_EVENTS,
        EventCategory.DEBUG_EVENT: NISTCategory.DETAILED_TRACKING,
    }
    
    @staticmethod
    def get_nist_category(event_category: EventCategory) -> NISTCategory:
        """Get NIST category for an event"""
        return EventClassification.NIST_MAPPING.get(event_category, NISTCategory.SYSTEM_EVENTS)


@dataclass
class SecurityEvent:
    """Standardized security event representation (NIST SP 800-92 compliant)"""
    timestamp: datetime
    component: ComponentType
    event_type: str
    description: str
    risk_level: RiskLevel
    user_context: Optional[str] = None
    session_id: Optional[str] = None
    event_category: Optional[EventCategory] = None
    nist_category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'component': self.component.value,
            'event_type': self.event_type,
            'description': self.description,
            'risk_level': self.risk_level.value,
            'user_context': self.user_context,
            'session_id': self.session_id,
            'event_category': self.event_category.value if self.event_category else None,
            'nist_category': self.nist_category,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityEvent':
        """Create SecurityEvent from dictionary"""
        event_category = None
        if data.get('event_category'):
            event_category = EventCategory(data['event_category'])
        
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            component=ComponentType(data['component']),
            event_type=data['event_type'],
            description=data['description'],
            risk_level=RiskLevel(data['risk_level']),
            user_context=data.get('user_context'),
            session_id=data.get('session_id'),
            event_category=event_category,
            nist_category=data.get('nist_category'),
            metadata=data.get('metadata', {})
        )
    
    def enrich_with_classification(self, event_category: EventCategory) -> None:
        """
        Enrich event with NIST classification information
        
        Args:
            event_category: EventCategory to classify this event
        """
        self.event_category = event_category
        self.nist_category = EventClassification.get_nist_category(event_category).value
    
    # Backward compatibility alias
    def enrich_with_taxonomy(self, event_category: EventCategory) -> None:
        """Deprecated: use enrich_with_classification() instead"""
        self.enrich_with_classification(event_category)


class SystemEvents:
    """Predefined system event catalog"""
    
    # Startup/shutdown events
    AGENT_START = "AGENT_START"
    AGENT_SHUTDOWN = "AGENT_SHUTDOWN"
    MODULE_INIT = "MODULE_INIT"
    
    # Planning events
    PLANNING_START = "PLANNING_START"
    PLANNING_COMPLETE = "PLANNING_COMPLETE"
    PLANNING_ERROR = "PLANNING_ERROR"
    
    # Execution events
    TASK_EXECUTION_START = "TASK_EXECUTION_START"
    TASK_EXECUTION_COMPLETE = "TASK_EXECUTION_COMPLETE"
    TASK_EXECUTION_ERROR = "TASK_EXECUTION_ERROR"
    
    # Command events
    COMMAND_EXECUTION = "COMMAND_EXECUTION"
    
    # Reasoning events
    REASONING_START = "REASONING_START"
    REASONING_COMPLETE = "REASONING_COMPLETE"
    REASONING_ITERATION = "REASONING_ITERATION"
    
    # Security events
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    RISK_THRESHOLD_EXCEEDED = "RISK_THRESHOLD_EXCEEDED"
    KILLSWITCH_ACTIVATED = "KILLSWITCH_ACTIVATED"
    LOG_INTEGRITY_CHECK = "LOG_INTEGRITY_CHECK"


__all__ = [
    'RiskLevel',
    'ComponentType',
    'NISTCategory',
    'EventCategory',
    'EventClassification',
    'SecurityEvent',
    'SystemEvents',
]