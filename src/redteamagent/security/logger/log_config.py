"""
Logging system configuration
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LogConfig:
    """Configuration for immutable logging system with WORM storage"""
    
    # WORM storage configuration
    worm_endpoint: Optional[str] = None  # e.g., "https://worm.example.com"
    worm_api_key: Optional[str] = None
    worm_secret_key: Optional[str] = None
    
    # Local storage configuration
    local_log_path: Optional[str] = "logs/security_audit.log"
    
    # Security settings
    verify_ssl: bool = True
    cert_path: Optional[str] = None
    key_path: Optional[str] = "keys"
    
    # Behavior settings
    enable_console_output: bool = True
    max_local_logs: int = 10000
    
    # Signature algorithm
    signing_algorithm: str = "RS256"
    
    def __post_init__(self):
        """Configuration validation"""
        if self.worm_endpoint and not self.worm_api_key:
            raise ValueError("API key required for WORM endpoint")


# Default configuration instance
DEFAULT_CONFIG = LogConfig()
