"""
Client for WORM (Write Once Read Many) storage
Implements communication with immutable storage system using HMAC-SHA256 signatures
"""

import requests
import json
import hmac
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
import ssl


class SocarratClient:
    """Client for external WORM storage system with cryptographic authentication"""
    
    def __init__(self, base_url: str, api_key: str, secret_key: str, 
                 verify_ssl: bool = True, cert_path: Optional[str] = None):
        """
        Initialize WORM storage client
        
        Args:
            base_url: Base URL of WORM storage endpoint
            api_key: API key for authentication
            secret_key: Secret key for HMAC signing
            verify_ssl: Whether to verify SSL certificates
            cert_path: Path to client certificate for mTLS
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.secret_key = secret_key
        self.verify_ssl = verify_ssl
        self.cert_path = cert_path
        
        # SSL configuration for mTLS
        self.ssl_context = ssl.create_default_context()
        if cert_path:
            self.ssl_context.load_cert_chain(
                f"{cert_path}/client.crt",
                f"{cert_path}/client.key"
            )
        if not verify_ssl:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def _generate_signature(self, data: str, timestamp: str) -> str:
        """
        Generate HMAC-SHA256 signature for authentication
        
        Args:
            data: Data to sign
            timestamp: ISO format timestamp
            
        Returns:
            HMAC-SHA256 signature hex digest
        """
        message = f"{timestamp}{data}"
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def store_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Store a security event in WORM storage
        
        Args:
            event_data: Event data to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.base_url}/store_event"
        timestamp = datetime.utcnow().isoformat() + 'Z'
        data_json = json.dumps(event_data)
        signature = self._generate_signature(data_json, timestamp)
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key,
            'X-TIMESTAMP': timestamp,
            'X-SIGNATURE': signature
        }
        
        try:
            response = requests.post(
                url,
                data=data_json,
                headers=headers,
                verify=self.verify_ssl,
                cert=(f"{self.cert_path}/client.crt", f"{self.cert_path}/client.key") if self.cert_path else None,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"[WORM] Error storing event: {e}")
            return False
