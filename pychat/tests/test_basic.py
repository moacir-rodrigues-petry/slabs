"""
Basic tests for PyChat
"""
import unittest
import datetime
from unittest.mock import MagicMock

from pychat.common.message import Message
from pychat.core.user import User, UserManager


class MessageTests(unittest.TestCase):
    """Tests for the Message class"""
    
    def test_message_creation(self):
        """Test that a message can be created correctly"""
        msg = Message(content="Hello", sender="user1")
        self.assertEqual(msg.content, "Hello")
        self.assertEqual(msg.sender, "user1")
        self.assertIsNone(msg.recipient)
        self.assertIsNotNone(msg.msg_id)
        self.assertIsNotNone(msg.timestamp)
    
    def test_message_serialization(self):
        """Test message serialization and deserialization"""
        # Create a message with fixed timestamp for testing
        timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0)
        original = Message(
            content="Test message",
            sender="user1",
            recipient="user2",
            msg_id="test-id",
            timestamp=timestamp
        )
        
        # Convert to JSON and back
        json_str = original.to_json()
        recreated = Message.from_json(json_str)
        
        # Verify all properties are preserved
        self.assertEqual(recreated.content, original.content)
        self.assertEqual(recreated.sender, original.sender)
        self.assertEqual(recreated.recipient, original.recipient)
        self.assertEqual(recreated.msg_id, original.msg_id)
        self.assertEqual(recreated.timestamp, original.timestamp)


class UserTests(unittest.TestCase):
    """Tests for the User class"""
    
    def test_user_creation(self):
        """Test that a user can be created correctly"""
        user = User(username="user1", display_name="User One")
        self.assertEqual(user.username, "user1")
        self.assertEqual(user.display_name, "User One")
        self.assertIsNotNone(user.last_seen)
    
    def test_user_display_name_default(self):
        """Test that display_name defaults to username if not provided"""
        user = User(username="user1")
        self.assertEqual(user.display_name, "user1")


class UserManagerTests(unittest.TestCase):
    """Tests for the UserManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage_mock = MagicMock()
        self.user_manager = UserManager(self.storage_mock)
    
    def test_add_user(self):
        """Test adding a user"""
        user = self.user_manager.add_user("user1", "User One")
        self.assertEqual(user.username, "user1")
        self.assertEqual(user.display_name, "User One")
        self.assertIn("user1", self.user_manager.active_users)
    
    def test_get_user(self):
        """Test getting a user"""
        self.user_manager.add_user("user1", "User One")
        user = self.user_manager.get_user("user1")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "user1")
        
        # Non-existent user
        self.assertIsNone(self.user_manager.get_user("non-existent"))
    
    def test_remove_user(self):
        """Test removing a user"""
        self.user_manager.add_user("user1")
        self.assertIn("user1", self.user_manager.active_users)
        
        self.user_manager.remove_user("user1")
        self.assertNotIn("user1", self.user_manager.active_users)
    
    def test_get_active_users(self):
        """Test getting active users"""
        self.user_manager.add_user("user1", "User One")
        self.user_manager.add_user("user2", "User Two")
        
        active_users = self.user_manager.get_active_users()
        self.assertEqual(len(active_users), 2)
        usernames = {user.username for user in active_users}
        self.assertEqual(usernames, {"user1", "user2"})


if __name__ == "__main__":
    unittest.main()
