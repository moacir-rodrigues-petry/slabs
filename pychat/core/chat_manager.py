"""
Main chat logic implementation for PyChat
"""
import queue
import threading
import time
import datetime
from typing import Dict, List, Callable, Optional, Set, Tuple
import datetime

from pychat.common.message import Message
from pychat.core.storage import Storage
from pychat.core.user import UserManager, User


class ChatSession:
    """
    Represents a user's active chat session
    """
    def __init__(self, user: User, session_id: str):
        """
        Initialize a chat session
        
        Args:
            user: The user associated with the session
            session_id: Unique session identifier
        """
        self.user = user
        self.session_id = session_id
        self.is_active = True
        self.last_activity = time.time()
        self.callbacks: List[Callable[[Message], None]] = []
    
    def add_callback(self, callback: Callable[[Message], None]) -> None:
        """
        Add a message callback to the session
        
        Args:
            callback: Function to call when a message is received
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Message], None]) -> None:
        """
        Remove a message callback from the session
        
        Args:
            callback: Function to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def update_activity(self) -> None:
        """Update the last activity timestamp"""
        self.last_activity = time.time()


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
        
        # User sessions
        self.sessions: Dict[str, ChatSession] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # username -> list of session_ids
        
        # Start message distribution thread
        self.running = True
        self.distribution_thread = threading.Thread(
            target=self._message_distribution_loop,
            daemon=True
        )
        self.distribution_thread.start()
        
        # Start session cleanup thread
        self.session_cleanup_thread = threading.Thread(
            target=self._session_cleanup_loop,
            daemon=True
        )
        self.session_cleanup_thread.start()
    
    def register_user(self, username: str, password: str, display_name: Optional[str] = None,
                     email: Optional[str] = None) -> User:
        """
        Register a new user
        
        Args:
            username: The username to register
            password: The user's password
            display_name: Optional display name
            email: Optional email address
            
        Returns:
            The registered User object
            
        Raises:
            ValueError: If username already exists
        """
        return self.user_manager.register_user(username, password, display_name, email)
    
    def login(self, username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Login a user with username and password
        
        Args:
            username: The username to login
            password: The password to check
            
        Returns:
            Tuple of (User, session_id) if login successful, (None, None) otherwise
        """
        user = self.user_manager.authenticate_user(username, password)
        if not user:
            return None, None
        
        # Create a new session
        session_id = self.storage.create_session(username)
        session = ChatSession(user, session_id)
        self.sessions[session_id] = session
        
        # Add to user sessions
        if username not in self.user_sessions:
            self.user_sessions[username] = []
        self.user_sessions[username].append(session_id)
        
        return user, session_id
    
    def logout(self, session_id: str) -> None:
        """
        Logout a user session
        
        Args:
            session_id: The session ID to logout
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            username = session.user.username
            
            # Update user status if this is their last session
            user_sessions = self.user_sessions.get(username, [])
            if len(user_sessions) <= 1:
                self.user_manager.update_user_status(username, 'offline')
            
            # Invalidate session
            self.storage.invalidate_session(session_id)
            
            # Remove from local tracking
            del self.sessions[session_id]
            if username in self.user_sessions:
                if session_id in self.user_sessions[username]:
                    self.user_sessions[username].remove(session_id)
                if not self.user_sessions[username]:
                    del self.user_sessions[username]
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate a session
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        if session_id not in self.sessions:
            # Check in storage
            username = self.storage.validate_session(session_id)
            if not username:
                return False
            
            # Session exists in storage but not in memory
            user = self.user_manager.get_user(username)
            if not user:
                return False
            
            # Create session in memory
            session = ChatSession(user, session_id)
            self.sessions[session_id] = session
            
            if username not in self.user_sessions:
                self.user_sessions[username] = []
            self.user_sessions[username].append(session_id)
        
        # Update session activity
        self.sessions[session_id].update_activity()
        return True
    
    def update_user_status(self, session_id: str, status: str) -> Optional[User]:
        """
        Update a user's status
        
        Args:
            session_id: The session ID of the user
            status: New status (online, away, busy, offline)
            
        Returns:
            Updated User object if successful, None otherwise
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        username = session.user.username
        
        return self.user_manager.update_user_status(username, status)
    
    def register_message_callback(self, session_id: str, callback: Callable[[Message], None]) -> bool:
        """
        Register a callback for message delivery
        
        Args:
            session_id: The session ID to register the callback for
            callback: Function to call when a message is received
            
        Returns:
            True if registration successful, False otherwise
        """
        if not self.validate_session(session_id):
            return False
        
        session = self.sessions[session_id]
        session.add_callback(callback)
        return True
    
    def unregister_message_callback(self, session_id: str, callback: Callable[[Message], None]) -> None:
        """
        Unregister a callback for message delivery
        
        Args:
            session_id: The session ID to unregister the callback from
            callback: Function to remove
        """
        if session_id in self.sessions:
            self.sessions[session_id].remove_callback(callback)
    
    def send_message(self, message: Message, session_id: Optional[str] = None) -> bool:
        """
        Send a message to the chat
        
        Args:
            message: The message to send
            session_id: Optional session ID for authentication
            
        Returns:
            True if message sent successfully, False otherwise
        """
        # Validate session if provided
        if session_id and not self.validate_session(session_id):
            return False
        
        # Add to message queue for distribution
        self.message_queue.put(message)
        
        # Save to storage
        self.storage.save_message(message)
        return True
    
    def get_message_history(self, username: Optional[str] = None, limit: int = 100) -> List[Message]:
        """
        Get message history
        
        Args:
            username: Username to filter messages for
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of Message objects
        """
        return self.storage.get_messages(limit, username)
    
    def get_conversations(self, username: str) -> List[Tuple[User, datetime.datetime]]:
        """
        Get private conversations for a user
        
        Args:
            username: The username to get conversations for
            
        Returns:
            List of tuples (User, last_message_time)
        """
        conversations = self.storage.get_private_conversations(username)
        result = []
        
        for other_username, last_time in conversations:
            user = self.user_manager.get_user(other_username)
            if user:
                result.append((user, last_time))
        
        return result
    
    def get_user(self, username: str) -> Optional[User]:
        """
        Get a user by username
        
        Args:
            username: The username to look up
            
        Returns:
            User object if found, None otherwise
        """
        return self.user_manager.get_user(username)
    
    def get_active_users(self) -> List[User]:
        """
        Get list of active users
        
        Returns:
            List of active User objects
        """
        return self.user_manager.get_active_users()
    
    def get_all_users(self) -> List[User]:
        """
        Get list of all users
        
        Returns:
            List of all User objects
        """
        return self.user_manager.get_all_users()
    
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
        # If message has a specific recipient, only send to that recipient and sender
        if message.recipient:
            # Send to recipient's sessions
            recipient_sessions = self.user_sessions.get(message.recipient, [])
            for session_id in recipient_sessions:
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    for callback in session.callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            print(f"Error delivering message to {message.recipient}: {e}")
            
            # Send to sender's sessions
            sender_sessions = self.user_sessions.get(message.sender, [])
            for session_id in sender_sessions:
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    for callback in session.callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            print(f"Error delivering message to {message.sender}: {e}")
        
        # If broadcast message, send to all active sessions
        else:
            for session_id, session in self.sessions.items():
                for callback in session.callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"Error delivering message to {session.user.username}: {e}")
    
    def _session_cleanup_loop(self) -> None:
        """
        Session cleanup loop
        Runs in a separate thread
        Removes inactive sessions
        """
        SESSION_TIMEOUT = 3600  # 1 hour
        
        while self.running:
            try:
                current_time = time.time()
                to_remove = []
                
                # Find inactive sessions
                for session_id, session in self.sessions.items():
                    if current_time - session.last_activity > SESSION_TIMEOUT:
                        to_remove.append(session_id)
                
                # Remove inactive sessions
                for session_id in to_remove:
                    self.logout(session_id)
                
                # Sleep for a while
                time.sleep(60)  # Check every minute
            
            except Exception as e:
                print(f"Error in session cleanup: {e}")
                time.sleep(60)  # Sleep on error
    
    def shutdown(self) -> None:
        """Shut down the chat manager"""
        self.running = False
        
        # Close all sessions
        for session_id in list(self.sessions.keys()):
            self.logout(session_id)
        
        if self.distribution_thread.is_alive():
            self.distribution_thread.join(timeout=2.0)
        
        if self.session_cleanup_thread.is_alive():
            self.session_cleanup_thread.join(timeout=2.0)
        
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
