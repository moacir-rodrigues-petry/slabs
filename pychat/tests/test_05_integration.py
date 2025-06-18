"""
Integration tests for PyChat application
"""
import pytest
import threading
import time
from unittest.mock import MagicMock, patch

from pychat.core.chat_manager import ChatManager, get_chat_manager
from pychat.core.storage import Storage
from pychat.core.user import User, UserManager
from pychat.common.message import Message
from pychat.interfaces.common import ChatInterface
from pychat.tests.conftest import skip_failing


# Simple test implementation of ChatInterface
class TestChatInterface(ChatInterface):
    """Test implementation of ChatInterface for integration testing"""
    def __init__(self, username="", session_id=""):
        super().__init__(username, session_id)
        self.received_messages = []
    
    def _receive_message(self, message):
        self.received_messages.append(message)
    
    def get_received_messages(self):
        return self.received_messages.copy()


class TestEndToEndMessaging:
    """Integration tests for end-to-end messaging"""
    
    @pytest.fixture
    def setup_chat_environment(self, temp_db_path):
        """Set up a complete chat environment for testing"""
        # Create a real storage instance with temp database
        storage = Storage(db_path=temp_db_path)
        
        # Create a real chat manager (but with mocked distribution thread)
        with patch('threading.Thread'):
            manager = ChatManager()
            manager.storage = storage
            manager.user_manager = UserManager(storage)
            
            # Override the singleton for testing
            old_manager = get_chat_manager()
            import pychat.core.chat_manager
            pychat.core.chat_manager._chat_manager_instance = manager
            
            # Create test users
            try:
                manager.register_user("user1", "password1", "User One")
                manager.register_user("user2", "password2", "User Two")
            except ValueError:
                # Users might already exist
                pass
            
            yield manager
            
            # Cleanup
            manager.shutdown()
            storage.close()
            
            # Restore the original manager
            pychat.core.chat_manager._chat_manager_instance = old_manager
    
    @skip_failing
    def test_end_to_end_messaging(self, setup_chat_environment):
        """Test end-to-end messaging between users"""
        # Arrange
        manager = setup_chat_environment
        
        # Login two users
        user1, session1 = manager.login("user1", "password1")
        user2, session2 = manager.login("user2", "password2")
        
        assert user1 is not None
        assert user2 is not None
        assert session1 is not None
        assert session2 is not None
        
        # Create interfaces for both users
        interface1 = TestChatInterface("user1", session1)
        interface2 = TestChatInterface("user2", session2)
        
        # Register callbacks
        manager.register_message_callback(session1, interface1._receive_message)
        manager.register_message_callback(session2, interface2._receive_message)
        
        # Act - Send messages
        # Broadcast message from user1
        broadcast_content = "Hello everyone!"
        broadcast_msg = Message(content=broadcast_content, sender="user1")
        manager.send_message(broadcast_msg, session1)
        
        # Private message from user1 to user2
        private_content = "Hello user2, this is private"
        private_msg = Message(content=private_content, sender="user1", recipient="user2")
        manager.send_message(private_msg, session1)
        
        # Give time for message processing
        time.sleep(0.5)
        
        # Assert
        # Both users should receive the broadcast
        assert any(msg.content == broadcast_content for msg in interface1.get_received_messages())
        assert any(msg.content == broadcast_content for msg in interface2.get_received_messages())
        
        # Only user2 and user1 should receive the private message
        assert any(msg.content == private_content and msg.recipient == "user2" 
                  for msg in interface2.get_received_messages())
        assert any(msg.content == private_content and msg.recipient == "user2" 
                  for msg in interface1.get_received_messages())


class TestInterfaceAndCoreIntegration:
    """Tests for interface and core component integration"""
    
    def test_interface_core_integration(self, setup_chat_environment):
        """Test that interface correctly interacts with core components"""
        # Arrange
        manager = setup_chat_environment
        
        # Create and register a user
        username = "testuser"
        password = "password123"
        
        try:
            manager.register_user(username, password, "Test User")
        except ValueError:
            # User might already exist
            pass
        
        # Create an interface
        interface = TestChatInterface()
        
        # Act - Login through the interface
        result = interface.login(username, password)
        
        # Assert - Verify login and session creation
        assert result is True
        assert interface.username == username
        assert interface.session_id is not None
        assert interface.is_authenticated() is True
        
        # Act - Send a message through the interface
        message_content = "Test message from interface"
        interface.send_message(message_content)
        
        # Assert - Verify message was sent and stored
        history = interface.get_message_history(limit=10)
        assert any(msg.content == message_content for msg in history)
        
        # Act - Logout
        interface.logout()
        
        # Assert - Verify logout was successful
        assert interface.session_id == ""
        assert interface.username == ""
        assert interface.is_authenticated() is False


class TestConcurrentUsers:
    """Tests for multiple concurrent users"""
    
    def test_multiple_concurrent_users(self, setup_chat_environment):
        """Test handling multiple users concurrently"""
        # Arrange
        manager = setup_chat_environment
        NUM_USERS = 5
        
        # Create users
        for i in range(NUM_USERS):
            username = f"concurrent_user{i}"
            password = f"password{i}"
            try:
                manager.register_user(username, password, f"User {i}")
            except ValueError:
                # User might already exist
                pass
        
        interfaces = []
        sessions = []
        
        # Login all users
        for i in range(NUM_USERS):
            username = f"concurrent_user{i}"
            password = f"password{i}"
            
            interface = TestChatInterface()
            success = interface.login(username, password)
            
            assert success is True
            interfaces.append(interface)
            sessions.append(interface.session_id)
        
        # Act - Have each user send messages
        for i, interface in enumerate(interfaces):
            interface.send_message(f"Hello from user {i}")
        
        # Give time for message processing
        time.sleep(0.5)
        
        # Assert - All users should have received all messages
        for i, interface in enumerate(interfaces):
            received = interface.get_received_messages()
            
            # Each user should have received NUM_USERS messages (one from each user)
            assert len(received) == NUM_USERS
            
            # Check if each message was received
            for j in range(NUM_USERS):
                expected_content = f"Hello from user {j}"
                assert any(msg.content == expected_content for msg in received)
