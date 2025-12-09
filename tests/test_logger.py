"""
Comprehensive Unit Tests for ImmutableLogger Module

Tests cover:
- Cryptographic hash chaining (SHA256)
- WORM fallback to local storage
- Retry queue mechanism
- Event taxonomy classification
- Chain integrity verification
- Thread safety
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import logger components
from src.redteamagent.security.logger.logger import (
    ImmutableLogger, ChainedLogEntry, initialize_logger, get_logger
)
from src.redteamagent.security.logger.queue_manager import QueueManager
from src.redteamagent.security.logger.event_types import (
    SecurityEvent, ComponentType, RiskLevel, SystemEvents, EventCategory, NISTCategory, EventClassification
)
from src.redteamagent.security.logger.log_config import LogConfig


class TestChainedLogEntry:
    """Test ChainedLogEntry hash calculation and structure"""
    
    def test_calculate_hash(self):
        """Test SHA256 hash calculation"""
        data = {
            'timestamp': '2024-01-01T00:00:00',
            'component': 'RedTeamAgent',
            'event_type': 'AGENT_START'
        }
        
        hash1 = ChainedLogEntry.calculate_hash(data)
        hash2 = ChainedLogEntry.calculate_hash(data)
        
        # Same data should produce same hash
        assert hash1 == hash2
        
        # Hash should be 64 characters (SHA256 hex)
        assert len(hash1) == 64
    
    def test_hash_deterministic(self):
        """Test that hash is deterministic"""
        data = {'key': 'value', 'number': 42}
        
        hashes = [ChainedLogEntry.calculate_hash(data) for _ in range(5)]
        
        # All hashes should be identical
        assert all(h == hashes[0] for h in hashes)
    
    def test_hash_sensitive_to_changes(self):
        """Test that hash changes with data modification"""
        data1 = {'timestamp': '2024-01-01T00:00:00'}
        data2 = {'timestamp': '2024-01-01T00:00:01'}
        
        hash1 = ChainedLogEntry.calculate_hash(data1)
        hash2 = ChainedLogEntry.calculate_hash(data2)
        
        assert hash1 != hash2
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        entry = ChainedLogEntry(
            timestamp='2024-01-01T00:00:00',
            component='RedTeamAgent',
            event_type='AGENT_START',
            description='Agent initialization',
            risk_level='LOW',
            user_context='test_user',
            session_id='sess123',
            sequence_number=1,
            previous_hash='hash0',
            entry_hash='hash1'
        )
        
        entry_dict = entry.to_dict()
        
        assert entry_dict['component'] == 'RedTeamAgent'
        assert entry_dict['event_type'] == 'AGENT_START'
        assert entry_dict['sequence_number'] == 1
        assert 'previous_hash' in entry_dict
        assert 'entry_hash' in entry_dict


class TestQueueManager:
    """Test retry queue management"""
    
    @pytest.fixture
    def temp_queue_dir(self):
        """Create temporary queue directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_enqueue(self, temp_queue_dir):
        """Test adding items to queue"""
        qm = QueueManager(queue_dir=Path(temp_queue_dir))
        
        log_entry = {
            'timestamp': '2024-01-01T00:00:00',
            'event_type': 'TEST_EVENT'
        }
        
        item_id = qm.enqueue(log_entry)
        
        assert item_id is not None
        assert (Path(temp_queue_dir) / f"{item_id}.json").exists()
    
    def test_dequeue(self, temp_queue_dir):
        """Test removing items from queue"""
        qm = QueueManager(queue_dir=Path(temp_queue_dir))
        
        log_entry = {'event_type': 'TEST'}
        item_id = qm.enqueue(log_entry)
        
        assert (Path(temp_queue_dir) / f"{item_id}.json").exists()
        
        result = qm.dequeue(item_id)
        assert result is True
        assert not (Path(temp_queue_dir) / f"{item_id}.json").exists()
    
    def test_mark_retry_with_backoff(self, temp_queue_dir):
        """Test exponential backoff for retries"""
        qm = QueueManager(queue_dir=Path(temp_queue_dir), initial_retry_delay=10)
        
        log_entry = {'event_type': 'TEST'}
        item_id = qm.enqueue(log_entry)
        
        # First retry
        qm.mark_retry(item_id, error="Connection failed")
        
        item_file = Path(temp_queue_dir) / f"{item_id}.json"
        with open(item_file, 'r') as f:
            queue_item = json.load(f)
        
        assert queue_item['retry_count'] == 1
        
        # Second retry (backoff should double)
        qm.mark_retry(item_id, error="Still failed")
        
        with open(item_file, 'r') as f:
            queue_item = json.load(f)
        
        assert queue_item['retry_count'] == 2
    
    def test_max_retries_exceeded(self, temp_queue_dir):
        """Test max retries limit"""
        qm = QueueManager(queue_dir=Path(temp_queue_dir), max_retries=2)
        
        log_entry = {'event_type': 'TEST'}
        item_id = qm.enqueue(log_entry)
        
        # Mark multiple retries
        qm.mark_retry(item_id)
        qm.mark_retry(item_id)
        
        # Next retry should fail
        result = qm.mark_retry(item_id)
        assert result is False
    
    def test_get_queue_stats(self, temp_queue_dir):
        """Test queue statistics"""
        qm = QueueManager(queue_dir=Path(temp_queue_dir))
        
        # Enqueue multiple items
        id1 = qm.enqueue({'event_type': 'TEST1'})
        id2 = qm.enqueue({'event_type': 'TEST2'})
        
        stats = qm.get_queue_stats()
        
        assert stats['total_queued'] == 2
        assert stats['pending_retry'] == 2


class TestEventClassification:
    """Test NIST SP 800-92 event classification"""
    
    def test_nist_mapping(self):
        """Test NIST SP 800-92 category mapping"""
        auth_event = EventCategory.AUTHENTICATION_SUCCESS
        nist_cat = EventClassification.NIST_MAPPING.get(auth_event)
        
        assert nist_cat == NISTCategory.ACCOUNT_LOGON.value
    
    def test_command_execution_mapping(self):
        """Test COMMAND_EXECUTION classification"""
        command_event = EventCategory.COMMAND_EXECUTION
        nist_cat = EventClassification.NIST_MAPPING.get(command_event)
        
        assert nist_cat == NISTCategory.DETAILED_TRACKING.value
    
    def test_get_events_by_nist_category(self):
        """Test filtering by NIST category"""
        # Get all events in ACCOUNT_LOGON category
        events = [k for k, v in EventClassification.NIST_MAPPING.items() 
                 if v == NISTCategory.ACCOUNT_LOGON.value]
        
        assert len(events) > 0
        assert EventCategory.AUTHENTICATION_SUCCESS in events
    
    def test_event_classification_enum(self):
        """Test EventClassification enum attributes"""
        assert hasattr(EventClassification, 'NIST_MAPPING')
        assert len(EventClassification.NIST_MAPPING) > 30


class TestSecurityEventEnhancement:
    """Test SecurityEvent with classification support"""
    
    def test_enrich_with_classification(self):
        """Test enriching event with NIST classification"""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='AGENT_START',
            description='Agent started',
            risk_level=RiskLevel.LOW
        )
        
        # Enrich with classification
        event.enrich_with_classification(EventCategory.AGENT_INITIALIZED)
        
        assert event.event_category == EventCategory.AGENT_INITIALIZED
        assert event.nist_category == NISTCategory.SYSTEM_EVENTS.value
    
    def test_security_event_to_dict(self):
        """Test event serialization with classification"""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.ACT,
            event_type='COMMAND_EXECUTION',
            description='Shell command executed',
            risk_level=RiskLevel.MEDIUM
        )
        
        event.enrich_with_classification(EventCategory.COMMAND_EXECUTION)
        event_dict = event.to_dict()
        
        assert event_dict['event_category'] == EventCategory.COMMAND_EXECUTION.value
        assert event_dict['nist_category'] == NISTCategory.DETAILED_TRACKING.value
    
    def test_backward_compatibility_enrich_with_taxonomy(self):
        """Test backward compatibility with enrich_with_taxonomy alias"""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.ACT,
            event_type='COMMAND_EXECUTION',
            description='Shell command executed',
            risk_level=RiskLevel.MEDIUM
        )
        
        # Old method name should still work
        event.enrich_with_taxonomy(EventCategory.COMMAND_EXECUTION)
        
        assert event.event_category == EventCategory.COMMAND_EXECUTION
        assert event.nist_category == NISTCategory.DETAILED_TRACKING.value


class TestImmutableLogger:
    """Test core ImmutableLogger functionality"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def logger_with_temp_storage(self, temp_log_dir):
        """Create logger with temporary storage"""
        config = LogConfig(
            local_log_path=f"{temp_log_dir}/security_audit.log",
            enable_console_output=False
        )
        logger = ImmutableLogger(config=config)
        return logger
    
    def test_logger_initialization(self, logger_with_temp_storage):
        """Test logger initialization"""
        logger = logger_with_temp_storage
        
        assert logger.session_id is not None
        assert logger.sequence_number == 0
        assert logger.previous_hash is not None
    
    def test_log_event(self, logger_with_temp_storage):
        """Test logging a security event"""
        logger = logger_with_temp_storage
        
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='AGENT_START',
            description='Agent initialized',
            risk_level=RiskLevel.LOW
        )
        
        success = logger.log_event(event)
        
        assert success is True
        assert logger.sequence_number == 1
        
        # Verify log file exists
        log_path = Path(logger.config.local_log_path)
        assert log_path.exists()
        assert log_path.stat().st_size > 0
    
    def test_hash_chaining(self, logger_with_temp_storage):
        """Test that logs are properly chained"""
        logger = logger_with_temp_storage
        
        # Log two events
        event1 = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='AGENT_START',
            description='Start',
            risk_level=RiskLevel.LOW
        )
        
        event2 = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='PLAN_GENERATED',
            description='Plan',
            risk_level=RiskLevel.MEDIUM
        )
        
        logger.log_event(event1)
        first_hash = logger.previous_hash
        
        logger.log_event(event2)
        
        # Read logs and verify chain
        log_path = Path(logger.config.local_log_path)
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        entry1_data = json.loads(lines[0])
        entry2_data = json.loads(lines[1])
        
        # Second entry's previous_hash should match first entry's hash
        assert entry2_data['previous_hash'] == entry1_data['entry_hash']
    
    def test_verify_chain_integrity(self, logger_with_temp_storage):
        """Test chain integrity verification"""
        logger = logger_with_temp_storage
        
        # Log multiple events
        for i in range(3):
            event = SecurityEvent(
                timestamp=datetime.utcnow(),
                component=ComponentType.REDTEAM_AGENT,
                event_type=f'EVENT_{i}',
                description=f'Event {i}',
                risk_level=RiskLevel.LOW
            )
            logger.log_event(event)
        
        # Verify chain integrity
        is_valid = logger.verify_chain_integrity()
        assert is_valid is True
    
    def test_verify_chain_detects_tampering(self, logger_with_temp_storage):
        """Test that chain integrity detects tampering"""
        logger = logger_with_temp_storage
        
        # Log event
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='AGENT_START',
            description='Start',
            risk_level=RiskLevel.LOW
        )
        
        logger.log_event(event)
        
        # Tamper with log file
        log_path = Path(logger.config.local_log_path)
        with open(log_path, 'r') as f:
            log_data = json.loads(f.read())
        
        # Modify event description
        log_data['description'] = 'TAMPERED'
        
        with open(log_path, 'w') as f:
            f.write(json.dumps(log_data))
        
        # Verify should detect tampering
        is_valid = logger.verify_chain_integrity()
        assert is_valid is False
    
    def test_get_logs_with_filtering(self, logger_with_temp_storage):
        """Test retrieving logs with filters"""
        logger = logger_with_temp_storage
        
        # Log events with different types
        for event_type in ['AGENT_START', 'PLAN_GENERATED', 'AGENT_START']:
            event = SecurityEvent(
                timestamp=datetime.utcnow(),
                component=ComponentType.REDTEAM_AGENT,
                event_type=event_type,
                description=f'{event_type} event',
                risk_level=RiskLevel.LOW
            )
            logger.log_event(event)
        
        # Filter by event type
        logs = logger.get_logs(event_type='AGENT_START')
        
        assert len(logs) == 2
        assert all(log.event_type == 'AGENT_START' for log in logs)
    
    def test_export_logs_json(self, logger_with_temp_storage):
        """Test exporting logs to JSON"""
        logger = logger_with_temp_storage
        
        # Log event
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='AGENT_START',
            description='Start',
            risk_level=RiskLevel.LOW
        )
        
        logger.log_event(event)
        
        # Export to JSON
        export_path = logger.config.local_log_path.replace('.log', '_export.json')
        success = logger.export_logs_json(export_path)
        
        assert success is True
        assert Path(export_path).exists()
        
        # Verify export content
        with open(export_path, 'r') as f:
            export_data = json.load(f)
        
        assert 'entries' in export_data
        assert len(export_data['entries']) == 1
    
    def test_get_statistics(self, logger_with_temp_storage):
        """Test log statistics collection"""
        logger = logger_with_temp_storage
        
        # Log events with different risk levels
        for risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.LOW]:
            event = SecurityEvent(
                timestamp=datetime.utcnow(),
                component=ComponentType.REDTEAM_AGENT,
                event_type='TEST_EVENT',
                description='Test',
                risk_level=risk_level
            )
            logger.log_event(event)
        
        stats = logger.get_statistics()
        
        assert stats['total_entries'] == 4
        assert stats['by_risk_level']['LOW'] == 2
        assert stats['by_risk_level']['MEDIUM'] == 1
        assert stats['by_risk_level']['HIGH'] == 1
    
    def test_thread_safety(self, logger_with_temp_storage):
        """Test thread-safe logging"""
        import threading
        
        logger = logger_with_temp_storage
        results = []
        
        def log_events(thread_id):
            for i in range(5):
                event = SecurityEvent(
                    timestamp=datetime.utcnow(),
                    component=ComponentType.REDTEAM_AGENT,
                    event_type=f'THREAD_{thread_id}_EVENT_{i}',
                    description=f'From thread {thread_id}',
                    risk_level=RiskLevel.LOW
                )
                success = logger.log_event(event)
                results.append(success)
        
        threads = [threading.Thread(target=log_events, args=(i,)) for i in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(results)
        assert len(logger.get_logs()) == 15


class TestWORMIntegration:
    """Test WORM storage integration and fallback"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @patch('src.redteamagent.security.logger.logger.SocarratClient')
    def test_worm_fallback_on_failure(self, mock_worm, temp_log_dir):
        """Test fallback to local storage when WORM fails"""
        # Configure mock to fail
        mock_worm.return_value.store_event.return_value = False
        
        config = LogConfig(
            local_log_path=f"{temp_log_dir}/security_audit.log",
            worm_endpoint="https://worm.example.com",
            worm_api_key="test_key",
            worm_secret_key="test_secret",
            enable_console_output=False
        )
        
        logger = ImmutableLogger(config=config)
        
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            component=ComponentType.REDTEAM_AGENT,
            event_type='AGENT_START',
            description='Start',
            risk_level=RiskLevel.LOW
        )
        
        success = logger.log_event(event)
        
        # Should succeed because local storage fallback works
        assert success is True
        assert Path(config.local_log_path).exists()


class TestGlobalLoggerInstance:
    """Test global logger initialization and retrieval"""
    
    def test_initialize_logger(self, tmp_path):
        """Test initializing global logger"""
        config = LogConfig(
            local_log_path=str(tmp_path / "test.log"),
            enable_console_output=False
        )
        
        logger = initialize_logger(config=config)
        
        assert logger is not None
        assert logger.session_id is not None
    
    def test_get_logger_singleton(self, tmp_path):
        """Test getting global logger instance"""
        config = LogConfig(
            local_log_path=str(tmp_path / "test.log"),
            enable_console_output=False
        )
        
        logger1 = initialize_logger(config=config)
        logger2 = get_logger()
        
        # Should be same instance
        assert logger1.session_id == logger2.session_id


# Integration Tests
class TestIntegration:
    """Integration tests for complete logging workflow"""
    
    @pytest.fixture
    def integration_env(self):
        """Set up integration test environment"""
        temp_dir = tempfile.mkdtemp()
        config = LogConfig(
            local_log_path=f"{temp_dir}/security_audit.log",
            enable_console_output=False
        )
        logger = ImmutableLogger(config=config)
        
        yield logger, temp_dir
        
        shutil.rmtree(temp_dir)
    
    def test_complete_logging_workflow(self, integration_env):
        """Test complete logging workflow"""
        logger, _ = integration_env
        
        # Simulate agent execution
        events = [
            (ComponentType.REDTEAM_AGENT, 'AGENT_START', 'Agent initialized', RiskLevel.LOW, EventCategory.AGENT_INITIALIZED),
            (ComponentType.PLANNER, 'PLANNING_START', 'Planning started', RiskLevel.LOW, EventCategory.PLAN_GENERATED),
            (ComponentType.ACT, 'COMMAND_EXECUTION', 'Execute shell command', RiskLevel.HIGH, EventCategory.COMMAND_EXECUTION),
            (ComponentType.REDTEAM_AGENT, 'TASK_COMPLETED', 'Task finished', RiskLevel.MEDIUM, EventCategory.TASK_COMPLETED),
        ]
        
        for component, event_type, description, risk_level, event_category in events:
            event = SecurityEvent(
                timestamp=datetime.utcnow(),
                component=component,
                event_type=event_type,
                description=description,
                risk_level=risk_level
            )
            event.enrich_with_taxonomy(event_category)
            
            success = logger.log_event(event)
            assert success is True
        
        # Verify logs
        logs = logger.get_logs()
        assert len(logs) == 4
        
        # Verify chain integrity
        assert logger.verify_chain_integrity() is True
        
        # Verify statistics
        stats = logger.get_statistics()
        assert stats['total_entries'] == 4
        assert 'COMMAND_EXECUTION' in stats['by_event_type']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
