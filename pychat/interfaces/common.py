"""
Shared interface code for PyChat
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any

from pychat.common.message import Message
from pychat.core.chat_manager import get_chat_manager, ChatManager
from pychat.core.user import User


class ChatInterface(ABC):
    """
    Abstract base class for chat interfaces
    """
    def __init__(self, username: str = "", session_id: str = ""):
        """
        Initialize a chat interface
        
        Args:
            username: Username for this interface (if already authenticated)
            session_id: Session ID (if already authenticated)
        """
        self.chat_manager: ChatManager = get_chat_manager()
        self.username = username
        self.session_id = session_id
        self.user: Optional[User] = None
        
        # If session_id is provided, validate it
        if session_id:
            if self.chat_manager.validate_session(session_id):
                self.user = self.chat_manager.get_user(username)
                # Register callback for message delivery
                self.chat_manager.register_message_callback(
                    session_id, self._receive_message
                )
    
    def login(self, username: str, password: str) -> bool:
        """
        Login with username and password
        
        Args:
            username: The username to login with
            password: The password to check
            
        Returns:
            True if login successful, False otherwise
        """
        user, session_id = self.chat_manager.login(username, password)
        if not user or not session_id:
            return False
        
        self.user = user
        self.username = username
        self.session_id = session_id
        
        # Register callback for message delivery
        self.chat_manager.register_message_callback(
            session_id, self._receive_message
        )
        
        return True
    
    def register(self, username: str, password: str, display_name: Optional[str] = None,
                email: Optional[str] = None) -> bool:
        """
        Register a new user
        
        Args:
            username: The username to register
            password: The password to set
            display_name: Optional display name
            email: Optional email address
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            self.chat_manager.register_user(username, password, display_name, email)
            return True
        except ValueError:
            return False
    
    def logout(self) -> None:
        """Logout the current session"""
        if self.session_id:
            self.chat_manager.logout(self.session_id)
            self.session_id = ""
            self.username = ""
            self.user = None
    
    def update_status(self, status: str) -> bool:
        """
        Update the user's status
        
        Args:
            status: New status (online, away, busy, offline)
            
        Returns:
            True if update successful, False otherwise
        """
        if not self.session_id:
            return False
        
        user = self.chat_manager.update_user_status(self.session_id, status)
        if user:
            self.user = user
            return True
        return False
    
    @abstractmethod
    def _receive_message(self, message: Message) -> None:
        """
        Handle received messages
        
        Args:
            message: The received message
        """
        pass
    
    def send_message(self, content: str, recipient: Optional[str] = None) -> bool:
        """
        Send a message
        
        Args:
            content: The message content
            recipient: Optional recipient username (None for broadcast)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.session_id or not self.username:
            return False
        
        message = Message(content=content, sender=self.username, recipient=recipient)
        return self.chat_manager.send_message(message, self.session_id)
    
    def get_message_history(self, limit: int = 100) -> List[Message]:
        """
        Get message history
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of Message objects
        """
        if not self.username:
            return []
        
        return self.chat_manager.get_message_history(self.username, limit)
    
    def get_conversations(self) -> List[Tuple[User, str]]:
        """
        Get private conversations for the current user
        
        Returns:
            List of tuples (User, last_message_time_string)
        """
        if not self.username:
            return []
        
        conversations = self.chat_manager.get_conversations(self.username)
        return [(user, last_time.strftime('%Y-%m-%d %H:%M')) for user, last_time in conversations]
    
    def get_active_users(self) -> List[User]:
        """
        Get active users
        
        Returns:
            List of active User objects
        """
        return self.chat_manager.get_active_users()
    
    def get_user_profile(self, username: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a user profile
        
        Args:
            username: The username to look up (current user if None)
            
        Returns:
            Dictionary with user profile information
        """
        if not username and self.user:
            username = self.username
        
        if not username:
            return None
        
        user = self.chat_manager.get_user(username)
        if not user:
            return None
        
        return {
            'username': user.username,
            'display_name': user.display_name,
            'email': user.email,
            'status': user.status,
            'last_seen': user.last_seen.strftime('%Y-%m-%d %H:%M') if user.last_seen else 'Never'
        }
    
    def is_authenticated(self) -> bool:
        """
        Check if the interface is authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.session_id:
            return False
        
        return self.chat_manager.validate_session(self.session_id)
    
    def shutdown(self) -> None:
        """Shut down the interface"""
        self.logout()
