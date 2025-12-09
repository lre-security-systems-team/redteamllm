"""
Immutable Hybrid Logger Module for RedTeamLLM
Implements cryptographic log chaining with WORM fallback strategy
Based on NIST SP 800-92 guidelines for log integrity
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from threading import Lock
from dataclasses import asdict, dataclass

from .event_types import SecurityEvent, ComponentType, RiskLevel
from .log_config import LogConfig
from .socarrat_client import SocarratClient
from .queue_manager import QueueManager


@dataclass
class ChainedLogEntry:
    """Represents a single immutable log entry with hash chain"""
    timestamp: str
    component: str
    event_type: str
    description: str
    risk_level: str
    user_context: Optional[str]
    session_id: Optional[str]
    sequence_number: int
    previous_hash: str  # Hash of previous entry (for chaining)
    entry_hash: str  # Hash of this entry
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp,
            'component': self.component,
            'event_type': self.event_type,
            'description': self.description,
            'risk_level': self.risk_level,
            'user_context': self.user_context,
            'session_id': self.session_id,
            'sequence_number': self.sequence_number,
            'previous_hash': self.previous_hash,
            'entry_hash': self.entry_hash
        }
    
    @staticmethod
    def calculate_hash(data: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of entry data"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


class ImmutableLogger:
    """
    Immutable hybrid logging system with cryptographic integrity
    
    Architecture:
    1. WORM Storage (Primary): Attempt to write to external WORM device
    2. Local Disk (Fallback): Write to local disk if WORM fails
    3. Queue System: Maintain retry queue for failed WORM writes
    4. Log Chaining: Each log contains hash of previous log (cryptographic chain)
    
    Thread-safe implementation with proper locking mechanisms.
    """
    
    # Class-level lock for thread safety
    _lock = Lock()
    
    def __init__(self, config: Optional[LogConfig] = None, session_id: Optional[str] = None):
        """
        Initialize the ImmutableLogger
        
        Args:
            config: LogConfig instance with WORM and local storage settings
            session_id: Optional session identifier for log correlation
        """
        self.config = config or LogConfig()
        self.session_id = session_id or self._generate_session_id()
        
        # Initialize WORM client if configured
        self.worm_client = None
        if self.config.worm_endpoint and self.config.worm_api_key:
            self.worm_client = SocarratClient(
                base_url=self.config.worm_endpoint,
                api_key=self.config.worm_api_key,
                secret_key=self.config.worm_secret_key or "",
                verify_ssl=self.config.verify_ssl,
                cert_path=self.config.cert_path
            )
        
        # Initialize queue manager for retries
        self.queue_manager = QueueManager(
            queue_dir=Path(self.config.local_log_path).parent / "retry_queue"
        )
        
        # Initialize local storage
        self._setup_local_storage()
        
        # Sequence counter for log ordering
        self.sequence_number = 0
        
        # Previous hash for chaining (SHA256 of initial state)
        self.previous_hash = self._calculate_initial_hash()
    
    @staticmethod
    def _generate_session_id() -> str:
        """Generate unique session identifier"""
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{timestamp}{os.getpid()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _setup_local_storage(self):
        """Ensure local log storage directory exists"""
        log_dir = Path(self.config.local_log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _calculate_initial_hash() -> str:
        """Calculate the initial hash (genesis block) for the chain"""
        genesis_data = {
            'type': 'GENESIS',
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Log chain initialized'
        }
        return ChainedLogEntry.calculate_hash(genesis_data)
    
    def log_event(self, event: SecurityEvent) -> bool:
        """
        Log a security event with cryptographic integrity
        
        Implements hybrid approach:
        1. Attempt WORM storage
        2. Fallback to local disk
        3. Queue for retry if WORM fails
        
        Args:
            event: SecurityEvent to log
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        with self._lock:
            try:
                # Increment sequence number
                self.sequence_number += 1
                
                # Create chained log entry
                log_entry = self._create_chained_entry(event)
                
                # Try WORM storage (primary)
                worm_success = self._try_worm_storage(log_entry)
                
                # Always write to local storage (fallback)
                local_success = self._write_local_log(log_entry)
                
                # Queue for retry if WORM failed
                if not worm_success and self.worm_client:
                    self.queue_manager.enqueue(log_entry.to_dict())
                
                # Retry queued items periodically
                if self.worm_client:
                    self._process_retry_queue()
                
                # Update previous hash for next entry
                self.previous_hash = log_entry.entry_hash
                
                if self.config.enable_console_output:
                    self._print_log_summary(log_entry, worm_success, local_success)
                
                return local_success  # Return True if at least local storage succeeded
                
            except Exception as e:
                print(f"[LOGGER ERROR] Failed to log event: {e}")
                return False
    
    def _create_chained_entry(self, event: SecurityEvent) -> ChainedLogEntry:
        """Create a chained log entry with hash integrity"""
        
        # Prepare entry data (without the hash itself yet)
        entry_data = {
            'timestamp': event.timestamp.isoformat(),
            'component': event.component.value,
            'event_type': event.event_type,
            'description': event.description,
            'risk_level': event.risk_level.value,
            'user_context': event.user_context,
            'session_id': event.session_id or self.session_id,
            'sequence_number': self.sequence_number,
            'previous_hash': self.previous_hash
        }
        
        # Calculate entry hash
        entry_hash = ChainedLogEntry.calculate_hash(entry_data)
        
        # Create chained entry
        return ChainedLogEntry(
            timestamp=entry_data['timestamp'],
            component=entry_data['component'],
            event_type=entry_data['event_type'],
            description=entry_data['description'],
            risk_level=entry_data['risk_level'],
            user_context=entry_data['user_context'],
            session_id=entry_data['session_id'],
            sequence_number=entry_data['sequence_number'],
            previous_hash=self.previous_hash,
            entry_hash=entry_hash
        )
    
    def _try_worm_storage(self, log_entry: ChainedLogEntry) -> bool:
        """
        Attempt to store log entry in external WORM storage
        
        Args:
            log_entry: ChainedLogEntry to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.worm_client:
            return False
        
        try:
            success = self.worm_client.store_event(log_entry.to_dict())
            return success
        except Exception as e:
            print(f"[LOGGER] WORM storage failed: {e}")
            return False
    
    def _write_local_log(self, log_entry: ChainedLogEntry) -> bool:
        """
        Write log entry to local disk storage
        
        Args:
            log_entry: ChainedLogEntry to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            log_path = Path(self.config.local_log_path)
            
            # Write as JSON line (append)
            with open(log_path, 'a') as f:
                f.write(json.dumps(log_entry.to_dict()) + '\n')
            
            return True
        except Exception as e:
            print(f"[LOGGER] Local storage failed: {e}")
            return False
    
    def _process_retry_queue(self):
        """
        Process queued log entries for WORM retry
        Attempts to send previously failed entries
        """
        try:
            queued_items = self.queue_manager.get_all_queued()
            
            for item_id, item_data in queued_items:
                if self.worm_client.store_event(item_data):
                    # Remove from queue if successful
                    self.queue_manager.dequeue(item_id)
        except Exception as e:
            print(f"[LOGGER] Retry queue processing failed: {e}")
    
    def _print_log_summary(self, log_entry: ChainedLogEntry, 
                          worm_success: bool, local_success: bool):
        """Print a summary of the logged event to console"""
        status = "✓" if (worm_success or local_success) else "✗"
        worm_status = "✓" if worm_success else "✗"
        local_status = "✓" if local_success else "✗"
        
        print(f"[{status}] LOG #{log_entry.sequence_number}: {log_entry.event_type} "
              f"({log_entry.risk_level}) | WORM:{worm_status} Local:{local_status}")
    
    def verify_chain_integrity(self, start_seq: int = 0, end_seq: Optional[int] = None) -> bool:
        """
        Verify the integrity of the log chain from start_seq to end_seq
        
        Uses hash chain to detect tampering:
        - Each entry's previous_hash must match previous entry's entry_hash
        - Recalculates each entry_hash to detect modification
        
        Args:
            start_seq: Starting sequence number
            end_seq: Ending sequence number (None = all)
            
        Returns:
            bool: True if chain is valid, False if tampering detected
        """
        try:
            log_path = Path(self.config.local_log_path)
            
            if not log_path.exists():
                print("[LOGGER] No local log file found")
                return False
            
            previous_hash = self._calculate_initial_hash()
            sequence_count = 0
            
            with open(log_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    entry_data = json.loads(line)
                    seq = entry_data.get('sequence_number', sequence_count + 1)
                    
                    # Check sequence number bounds
                    if seq < start_seq:
                        continue
                    if end_seq and seq > end_seq:
                        break
                    
                    # Verify previous hash
                    if entry_data['previous_hash'] != previous_hash:
                        print(f"[LOGGER] Chain integrity violation at sequence {seq}")
                        return False
                    
                    # Recalculate entry hash
                    entry_copy = entry_data.copy()
                    stored_hash = entry_copy.pop('entry_hash')
                    calculated_hash = ChainedLogEntry.calculate_hash(entry_copy)
                    
                    if stored_hash != calculated_hash:
                        print(f"[LOGGER] Entry hash mismatch at sequence {seq}")
                        return False
                    
                    previous_hash = stored_hash
                    sequence_count += 1
            
            print(f"[LOGGER] Chain integrity verified: {sequence_count} entries valid")
            return True
            
        except Exception as e:
            print(f"[LOGGER] Integrity verification failed: {e}")
            return False
    
    def get_logs(self, session_id: Optional[str] = None, 
                 event_type: Optional[str] = None,
                 risk_level: Optional[str] = None) -> List[ChainedLogEntry]:
        """
        Retrieve logs with optional filtering
        
        Args:
            session_id: Filter by session ID
            event_type: Filter by event type
            risk_level: Filter by risk level
            
        Returns:
            List of matching ChainedLogEntry objects
        """
        logs = []
        log_path = Path(self.config.local_log_path)
        
        if not log_path.exists():
            return logs
        
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    entry_data = json.loads(line)
                    
                    # Apply filters
                    if session_id and entry_data.get('session_id') != session_id:
                        continue
                    if event_type and entry_data.get('event_type') != event_type:
                        continue
                    if risk_level and entry_data.get('risk_level') != risk_level:
                        continue
                    
                    # Convert dict to ChainedLogEntry
                    entry = ChainedLogEntry(**entry_data)
                    logs.append(entry)
            
            return logs
        except Exception as e:
            print(f"[LOGGER] Failed to retrieve logs: {e}")
            return logs
    
    def export_logs_json(self, output_path: str, 
                        session_id: Optional[str] = None) -> bool:
        """
        Export logs to a JSON file for forensic analysis
        
        Args:
            output_path: Path to output JSON file
            session_id: Optional session filter
            
        Returns:
            bool: True if successful
        """
        try:
            logs = self.get_logs(session_id=session_id)
            
            output_data = {
                'export_timestamp': datetime.utcnow().isoformat(),
                'session_id': self.session_id,
                'total_entries': len(logs),
                'entries': [log.to_dict() for log in logs]
            }
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"[LOGGER] Export failed: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged events
        
        Returns:
            Dict with event counts by type and risk level
        """
        logs = self.get_logs()
        
        stats = {
            'total_entries': len(logs),
            'by_event_type': {},
            'by_risk_level': {},
            'by_component': {},
            'session_id': self.session_id
        }
        
        for log in logs:
            # Count by event type
            stats['by_event_type'][log.event_type] = \
                stats['by_event_type'].get(log.event_type, 0) + 1
            
            # Count by risk level
            stats['by_risk_level'][log.risk_level] = \
                stats['by_risk_level'].get(log.risk_level, 0) + 1
            
            # Count by component
            stats['by_component'][log.component] = \
                stats['by_component'].get(log.component, 0) + 1
        
        return stats


# Global logger instance
_global_logger: Optional[ImmutableLogger] = None


def initialize_logger(config: Optional[LogConfig] = None, 
                     session_id: Optional[str] = None) -> ImmutableLogger:
    """
    Initialize and return the global logger instance
    
    Args:
        config: Optional LogConfig instance
        session_id: Optional session identifier
        
    Returns:
        ImmutableLogger instance
    """
    global _global_logger
    _global_logger = ImmutableLogger(config=config, session_id=session_id)
    return _global_logger


def get_logger() -> ImmutableLogger:
    """
    Get the global logger instance
    
    Returns:
        ImmutableLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = ImmutableLogger()
    return _global_logger
