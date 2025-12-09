"""
Queue Manager for Log Entry Retry System
Manages persistent queue for failed WORM writes with retry capability
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from threading import Lock


class QueueManager:
    """
    Manages persistent queue for failed WORM log entries
    
    Features:
    - Persistent storage using JSON files
    - Retry timestamp tracking
    - Exponential backoff support
    - Thread-safe operations
    """
    
    _lock = Lock()
    
    def __init__(self, queue_dir: Path = None, 
                 max_retries: int = 5,
                 initial_retry_delay: int = 60):
        """
        Initialize the QueueManager
        
        Args:
            queue_dir: Directory to store queue files
            max_retries: Maximum number of retry attempts
            initial_retry_delay: Initial retry delay in seconds
        """
        self.queue_dir = queue_dir or Path("logs/retry_queue")
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        
        # Create queue directory
        self.queue_dir.mkdir(parents=True, exist_ok=True)
    
    def enqueue(self, log_entry: Dict[str, Any]) -> str:
        """
        Add a log entry to the retry queue
        
        Args:
            log_entry: Dictionary containing log entry data
            
        Returns:
            str: Queue item ID
        """
        with self._lock:
            item_id = str(uuid.uuid4())
            
            queue_item = {
                'id': item_id,
                'timestamp': datetime.utcnow().isoformat(),
                'retry_count': 0,
                'next_retry': datetime.utcnow().isoformat(),
                'last_error': None,
                'log_entry': log_entry
            }
            
            # Save to file
            item_path = self.queue_dir / f"{item_id}.json"
            with open(item_path, 'w') as f:
                json.dump(queue_item, f, indent=2)
            
            return item_id
    
    def dequeue(self, item_id: str) -> bool:
        """
        Remove a log entry from the queue (successful delivery)
        
        Args:
            item_id: ID of the queue item
            
        Returns:
            bool: True if successful
        """
        with self._lock:
            item_path = self.queue_dir / f"{item_id}.json"
            
            try:
                if item_path.exists():
                    item_path.unlink()
                return True
            except Exception as e:
                print(f"[QUEUE] Failed to dequeue {item_id}: {e}")
                return False
    
    def mark_retry(self, item_id: str, error: str = None) -> bool:
        """
        Mark a queue item for retry with exponential backoff
        
        Args:
            item_id: ID of the queue item
            error: Error message from failed attempt
            
        Returns:
            bool: True if marked for retry, False if max retries exceeded
        """
        with self._lock:
            item_path = self.queue_dir / f"{item_id}.json"
            
            try:
                with open(item_path, 'r') as f:
                    queue_item = json.load(f)
                
                # Check max retries
                if queue_item['retry_count'] >= self.max_retries:
                    print(f"[QUEUE] Max retries exceeded for {item_id}")
                    return False
                
                # Increment retry count
                queue_item['retry_count'] += 1
                queue_item['last_error'] = error
                
                # Calculate next retry time (exponential backoff)
                backoff_seconds = self.initial_retry_delay * (2 ** (queue_item['retry_count'] - 1))
                next_retry = datetime.utcnow() + timedelta(seconds=backoff_seconds)
                queue_item['next_retry'] = next_retry.isoformat()
                
                # Update file
                with open(item_path, 'w') as f:
                    json.dump(queue_item, f, indent=2)
                
                return True
            except Exception as e:
                print(f"[QUEUE] Failed to mark retry for {item_id}: {e}")
                return False
    
    def get_pending_retries(self) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get all queue items ready for retry
        
        Returns:
            List of (item_id, log_entry) tuples for items due for retry
        """
        pending = []
        current_time = datetime.utcnow()
        
        try:
            for item_file in self.queue_dir.glob("*.json"):
                with open(item_file, 'r') as f:
                    queue_item = json.load(f)
                
                next_retry = datetime.fromisoformat(queue_item['next_retry'])
                
                if current_time >= next_retry:
                    pending.append((queue_item['id'], queue_item['log_entry']))
        except Exception as e:
            print(f"[QUEUE] Failed to get pending retries: {e}")
        
        return pending
    
    def get_all_queued(self) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get all queued items (regardless of retry status)
        
        Returns:
            List of (item_id, log_entry) tuples for all queued items
        """
        all_items = []
        
        try:
            for item_file in self.queue_dir.glob("*.json"):
                with open(item_file, 'r') as f:
                    queue_item = json.load(f)
                
                all_items.append((queue_item['id'], queue_item['log_entry']))
        except Exception as e:
            print(f"[QUEUE] Failed to get all queued items: {e}")
        
        return all_items
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retry queue
        
        Returns:
            Dictionary with queue statistics
        """
        stats = {
            'total_queued': 0,
            'pending_retry': 0,
            'by_retry_count': {},
            'oldest_item': None
        }
        
        oldest_timestamp = None
        
        try:
            for item_file in self.queue_dir.glob("*.json"):
                with open(item_file, 'r') as f:
                    queue_item = json.load(f)
                
                stats['total_queued'] += 1
                
                # Check if ready for retry
                next_retry = datetime.fromisoformat(queue_item['next_retry'])
                if datetime.utcnow() >= next_retry:
                    stats['pending_retry'] += 1
                
                # Count by retry count
                retry_count = queue_item['retry_count']
                stats['by_retry_count'][retry_count] = \
                    stats['by_retry_count'].get(retry_count, 0) + 1
                
                # Find oldest item
                item_timestamp = datetime.fromisoformat(queue_item['timestamp'])
                if oldest_timestamp is None or item_timestamp < oldest_timestamp:
                    oldest_timestamp = item_timestamp
                    stats['oldest_item'] = {
                        'id': queue_item['id'],
                        'timestamp': queue_item['timestamp'],
                        'retry_count': retry_count
                    }
        except Exception as e:
            print(f"[QUEUE] Failed to get queue stats: {e}")
        
        return stats
    
    def cleanup_failed_items(self, older_than_days: int = 7) -> int:
        """
        Remove items that have exceeded max retries or are too old
        
        Args:
            older_than_days: Remove items older than this many days
            
        Returns:
            Number of items cleaned up
        """
        cleaned = 0
        cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)
        
        with self._lock:
            try:
                for item_file in self.queue_dir.glob("*.json"):
                    with open(item_file, 'r') as f:
                        queue_item = json.load(f)
                    
                    item_timestamp = datetime.fromisoformat(queue_item['timestamp'])
                    
                    # Remove if max retries exceeded or too old
                    if (queue_item['retry_count'] >= self.max_retries or
                        item_timestamp < cutoff_time):
                        item_file.unlink()
                        cleaned += 1
            except Exception as e:
                print(f"[QUEUE] Cleanup failed: {e}")
        
        return cleaned
