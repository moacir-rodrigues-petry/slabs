"""
Shared interface code for PyChat
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from pychat.common.message import Message
from pychat.core.chat_manager import get_chat_manager, ChatManager
from pychat.core.user import User


class ChatInterface(ABC):
    """
    Abstract base class for chat interfaces
    """
    def __init__(self, username: str, display_name: Optional[str] = None):
        """
        Initialize a chat interface
        
        Args:
            username: Username for this interface
            display_name: Display name (defaults to username)
        """
        self.chat_manager: ChatManager = get_chat_manager()
        self.username = username
        self.user = self.chat_manager.register_user(username, display_name)
        
        # Register callback for message delivery
        self.chat_manager.register_message_callback(
            username, self._receive_message
        )
    
    @abstractmethod
    def _receive_message(self, message: Message) -> None:
        """
        Handle received messages
        
        Args:
            message: The received message
        """
        pass
    
    def send_message(self, content: str, recipient: Optional[str] = None) -> None:
        """
        Send a message
        
        Args:
            content: The message content
            recipient: Optional recipient username (None for broadcast)
        """
        message = Message(content=content, sender=self.username, recipient=recipient)
        self.chat_manager.send_message(message)
    
    def get_message_history(self, limit: int = 100) -> List[Message]:
        """
        Get message history
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of Message objects
        """
        return self.chat_manager.get_message_history(limit, self.username)
    
    def get_active_users(self) -> List[User]:
        """
        Get active users
        
        Returns:
            List of active User objects
        """
        return self.chat_manager.get_active_users()
    
    def shutdown(self) -> None:
        """Shut down the interface"""
        self.chat_manager.unregister_user(self.username)
