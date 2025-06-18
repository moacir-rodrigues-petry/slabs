"""
Main chat logic implementation for PyChat
"""
import queue
import threading
import time
from typing import Dict, List, Callable, Optional, Set

from pychat.common.message import Message
from pychat.core.storage import Storage
from pychat.core.user import UserManager, User


class ChatManager:
    """
    Central chat manager that handles message distribution and user sessions
    """
    def __init__(self):
        """Initialize the chat manager"""
        self.storage = Storage()
        self.user_manager = UserManager(self.storage)
        
        # Message queue for internal distribution
        self.message_queue: queue.Queue = queue.Queue()
        
        # Callbacks for message delivery to interfaces
        self.message_callbacks: Dict[str, List[Callable[[Message], None]]] = {}
        
        # Start message distribution thread
        self.running = True
        self.distribution_thread = threading.Thread(
            target=self._message_distribution_loop,
            daemon=True
        )
        self.distribution_thread.start()
    
    def register_user(self, username: str, display_name: Optional[str] = None) -> User:
        """
        Register a new user or update an existing one
        
        Args:
            username: The username to register
            display_name: Optional display name
            
        Returns:
            The registered User object
        """
        return self.user_manager.add_user(username, display_name)
    
    def unregister_user(self, username: str) -> None:
        """
        Unregister a user
        
        Args:
            username: The username to unregister
        """
        self.user_manager.remove_user(username)
        
        # Remove any callbacks for this user
        if username in self.message_callbacks:
            del self.message_callbacks[username]
    
    def send_message(self, message: Message) -> None:
        """
        Send a message to the chat
        
        Args:
            message: The message to send
        """
        # Add to message queue for distribution
        self.message_queue.put(message)
        
        # Save to storage
        self.storage.save_message(message)
    
    def get_message_history(self, limit: int = 100, username: Optional[str] = None) -> List[Message]:
        """
        Get message history
        
        Args:
            limit: Maximum number of messages to retrieve
            username: Username to filter messages for
            
        Returns:
            List of Message objects
        """
        return self.storage.get_messages(limit, username)
    
    def register_message_callback(self, username: str, callback: Callable[[Message], None]) -> None:
        """
        Register a callback for message delivery
        
        Args:
            username: The username to register the callback for
            callback: Function to call when a message is received
        """
        if username not in self.message_callbacks:
            self.message_callbacks[username] = []
        
        self.message_callbacks[username].append(callback)
    
    def _message_distribution_loop(self) -> None:
        """
        Internal message distribution loop
        Runs in a separate thread
        """
        while self.running:
            try:
                # Get message from queue (with timeout to allow clean shutdown)
                message = self.message_queue.get(timeout=0.5)
                
                # Distribute message to appropriate callbacks
                self._distribute_message(message)
                
                # Mark as done
                self.message_queue.task_done()
            except queue.Empty:
                # No messages, just continue
                continue
            except Exception as e:
                print(f"Error in message distribution: {e}")
    
    def _distribute_message(self, message: Message) -> None:
        """
        Distribute a message to appropriate callbacks
        
        Args:
            message: The message to distribute
        """
        # If message has a specific recipient, only send to that recipient
        if message.recipient:
            if message.recipient in self.message_callbacks:
                for callback in self.message_callbacks[message.recipient]:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"Error delivering message to {message.recipient}: {e}")
            
            # Also send to the sender (so they can see their own messages)
            if message.sender in self.message_callbacks and message.sender != message.recipient:
                for callback in self.message_callbacks[message.sender]:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"Error delivering message to {message.sender}: {e}")
        
        # If broadcast message, send to all registered callbacks
        else:
            for username, callbacks in self.message_callbacks.items():
                for callback in callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"Error delivering message to {username}: {e}")
    
    def get_active_users(self) -> List[User]:
        """
        Get list of active users
        
        Returns:
            List of active User objects
        """
        return self.user_manager.get_active_users()
    
    def shutdown(self) -> None:
        """Shut down the chat manager"""
        self.running = False
        if self.distribution_thread.is_alive():
            self.distribution_thread.join(timeout=2.0)
        self.storage.close()


# Singleton instance for easy access
_chat_manager_instance = None

def get_chat_manager() -> ChatManager:
    """
    Get the singleton instance of the chat manager
    
    Returns:
        ChatManager instance
    """
    global _chat_manager_instance
    if _chat_manager_instance is None:
        _chat_manager_instance = ChatManager()
    return _chat_manager_instance
