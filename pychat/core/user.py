"""
User profile management for PyChat
"""
import datetime
from typing import Dict, Optional, List

from pychat.core.storage import Storage


class User:
    """
    Represents a user in the PyChat application
    """
    def __init__(self, username: str, display_name: Optional[str] = None):
        """
        Initialize a user
        
        Args:
            username: Unique identifier for the user
            display_name: Human-readable name (defaults to username)
        """
        self.username = username
        self.display_name = display_name if display_name else username
        self.last_seen = datetime.datetime.now()
    
    def __str__(self) -> str:
        """String representation of the user"""
        return f"{self.display_name} ({self.username})"


class UserManager:
    """
    Manages user profiles for the chat application
    """
    def __init__(self, storage: Storage):
        """
        Initialize the user manager
        
        Args:
            storage: Storage instance for persistence
        """
        self.storage = storage
        self.active_users: Dict[str, User] = {}
    
    def add_user(self, username: str, display_name: Optional[str] = None) -> User:
        """
        Add a new user or update an existing one
        
        Args:
            username: The username to add
            display_name: Optional display name
            
        Returns:
            The created/updated User object
        """
        # For Phase 1, we'll just store users in memory
        # In Phase 2, we'll add persistent storage for users
        user = User(username, display_name)
        self.active_users[username] = user
        return user
    
    def remove_user(self, username: str) -> None:
        """
        Remove a user from active users
        
        Args:
            username: The username to remove
        """
        if username in self.active_users:
            del self.active_users[username]
    
    def get_user(self, username: str) -> Optional[User]:
        """
        Get a user by username
        
        Args:
            username: The username to look up
            
        Returns:
            User object if found, None otherwise
        """
        return self.active_users.get(username)
    
    def get_active_users(self) -> List[User]:
        """
        Get all active users
        
        Returns:
            List of active User objects
        """
        return list(self.active_users.values())
