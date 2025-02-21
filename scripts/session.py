import os
import time
import threading
from datetime import datetime, timedelta
import secrets
from typing import Optional
from . import logging

logger = logging.logger

class Session:
    def __init__(self):
        self.token: Optional[str] = None
        self.username: Optional[str] = None
        self.last_activity: Optional[float] = None
        self.lock = threading.Lock()
        self.timeout_minutes = 5
        
    def generate_token(self) -> str:
        """Generate a cryptographically secure session token"""
        return secrets.token_hex(32)
        
    def create(self, username: str) -> str:
        """Create a new session for a user"""
        with self.lock:
            self.token = self.generate_token()
            self.username = username
            self.last_activity = time.time()
            logger.info(f"New session created for user: {username}")
            return self.token
            
    def validate(self, token: str) -> bool:
        """Validate a session token"""
        with self.lock:
            if not self.token or not self.username:
                return False
            if token != self.token:
                return False
            if self.is_expired():
                self.clear()
                return False
            return True
            
    def update_activity(self):
        """Update the last activity timestamp"""
        with self.lock:
            self.last_activity = time.time()
            
    def is_expired(self) -> bool:
        """Check if the session has expired"""
        if not self.last_activity:
            return True
        elapsed = time.time() - self.last_activity
        return elapsed > (self.timeout_minutes * 60)
        
    def clear(self):
        """Clear the session data"""
        with self.lock:
            if self.username:
                logger.info(f"Session cleared for user: {self.username}")
            self.token = None
            self.username = None
            self.last_activity = None
            
    def get_remaining_time(self) -> int:
        """Get remaining session time in seconds"""
        if not self.last_activity:
            return 0
        elapsed = time.time() - self.last_activity
        remaining = (self.timeout_minutes * 60) - elapsed
        return max(0, int(remaining))

# Global session instance
current_session = Session()
