"""
User profile management for PyChat
"""
import datetime
import hashlib
import os
from typing import Dict, Optional, List, Any

from pychat.core.storage import Storage


class User:
    """
    Represents a user in the PyChat application
    """
    def __init__(self, username: str, display_name: Optional[str] = None, 
                 email: Optional[str] = None, status: str = "online",
                 user_id: Optional[str] = None):
        """
        Initialize a user
        
        Args:
            username: Unique identifier for the user
            display_name: Human-readable name (defaults to username)
            email: User's email address
            status: Current user status (online, away, busy, offline)
            user_id: Internal ID for the user
        """
        self.username = username
        self.display_name = display_name if display_name else username
        self.email = email
        self.status = status
        self.user_id = user_id
        self.last_seen = datetime.datetime.now()
    
    def __str__(self) -> str:
        """String representation of the user"""
        return f"{self.display_name} ({self.username}) - {self.status}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for storage"""
        return {
            'username': self.username,
            'display_name': self.display_name,
            'email': self.email,
            'status': self.status,
            'user_id': self.user_id,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create a user from dictionary"""
        user = cls(
            username=data['username'],
            display_name=data['display_name'],
            email=data.get('email'),
            status=data.get('status', 'offline'),
            user_id=data.get('user_id')
        )
        if data.get('last_seen'):
            user.last_seen = datetime.datetime.fromisoformat(data['last_seen'])
        return user


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
        self._load_active_users()
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash a password with a salt
        
        Args:
            password: The password to hash
            salt: Optional salt (generated if None)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = os.urandom(32).hex()
        
        # Create hash with salt
        hash_obj = hashlib.sha256()
        hash_obj.update(salt.encode() + password.encode())
        hashed_password = hash_obj.hexdigest()
        
        return hashed_password, salt
    
    def _load_active_users(self) -> None:
        """Load active users from storage"""
        users = self.storage.get_users()
        for user in users:
            if user.status != 'offline':
                self.active_users[user.username] = user
    
    def register_user(self, username: str, password: str, display_name: Optional[str] = None, 
                    email: Optional[str] = None) -> User:
        """
        Register a new user
        
        Args:
            username: The username for the new user
            password: The password for the new user
            display_name: Optional display name
            email: Optional email address
            
        Returns:
            The created User object
            
        Raises:
            ValueError: If username already exists
        """
        # Check if user exists
        if self.storage.user_exists(username):
            raise ValueError(f"Username '{username}' is already taken")
        
        # Create new user
        user = User(username, display_name, email)
        
        # Hash the password
        hashed_password, salt = self._hash_password(password)
        
        # Save to storage
        self.storage.save_user(user, hashed_password, salt)
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password
        
        Args:
            username: The username to authenticate
            password: The password to check
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Get user from storage
        user_data = self.storage.get_user_auth_data(username)
        if not user_data:
            return None
        
        # Check password
        stored_hash = user_data.get('password_hash')
        salt = user_data.get('password_salt')
        
        if not stored_hash or not salt:
            return None
        
        # Verify password
        hash_check, _ = self._hash_password(password, salt)
        if hash_check != stored_hash:
            return None
        
        # Get full user data
        user = self.storage.get_user(username)
        if user:
            # Update last seen and status
            user.last_seen = datetime.datetime.now()
            user.status = 'online'
            self.storage.update_user(user)
            self.active_users[username] = user
        
        return user
    
    def add_user(self, username: str, display_name: Optional[str] = None, 
                email: Optional[str] = None, status: str = 'online') -> User:
        """
        Add a new user or update an existing one (for internal use)
        
        Args:
            username: The username to add
            display_name: Optional display name
            email: Optional email address
            status: User status
            
        Returns:
            The created/updated User object
        """
        # Check if user exists in storage
        user = self.storage.get_user(username)
        
        if user:
            # Update existing user
            user.display_name = display_name or user.display_name
            user.email = email or user.email
            user.status = status
            user.last_seen = datetime.datetime.now()
            self.storage.update_user(user)
        else:
            # Create new user (should not happen normally)
            user = User(username, display_name, email, status)
            self.storage.save_user(user)
        
        # Add to active users if online
        if status != 'offline':
            self.active_users[username] = user
        
        return user
    
    def update_user_status(self, username: str, status: str) -> Optional[User]:
        """
        Update a user's status
        
        Args:
            username: The username to update
            status: New status (online, away, busy, offline)
            
        Returns:
            Updated User object if found, None otherwise
        """
        user = self.get_user(username)
        if not user:
            return None
        
        user.status = status
        user.last_seen = datetime.datetime.now()
        
        # Update in storage
        self.storage.update_user(user)
        
        # Update active users
        if status == 'offline':
            if username in self.active_users:
                del self.active_users[username]
        else:
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
        # Check active users first
        if username in self.active_users:
            return self.active_users[username]
        
        # Check storage
        return self.storage.get_user(username)
    
    def get_active_users(self) -> List[User]:
        """
        Get all active users
        
        Returns:
            List of active User objects
        """
        return list(self.active_users.values())
    
    def get_all_users(self) -> List[User]:
        """
        Get all users (active and inactive)
        
        Returns:
            List of all User objects
        """
        return self.storage.get_users()
