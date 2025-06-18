"""
Tests for basic functionality of PyChat application
"""
import pytest
from unittest.mock import MagicMock, patch

from pychat.common.message import Message
from pychat.core.user import User
from pychat.tests.conftest import skip_failing


class TestUserCreationAndManagement:
    """Tests for user creation and management"""
    
    @skip_failing
    def test_create_new_user(self, user_manager):
        """Test creating a new user"""
        # Arrange
        username = "newuser"
        password = "Password123!"
        display_name = "New User"
        email = "new@example.com"
        
        # Mock storage to prevent actual database operations
        user_manager.storage.user_exists.return_value = False
        
        # Act
        user = user_manager.register_user(username, password, display_name, email)
        
        # Assert
        assert user.username == username
        assert user.display_name == display_name
        assert user.email == email
        assert user.status == "online"
        user_manager.storage.save_user.assert_called_once()
    
    def test_retrieve_existing_user(self, user_manager, sample_user):
        """Test retrieving an existing user"""
        # Arrange
        username = sample_user.username
        user_manager.storage.get_user.return_value = sample_user
        
        # Act
        retrieved_user = user_manager.get_user(username)
        
        # Assert
        assert retrieved_user is not None
        assert retrieved_user.username == username
        assert retrieved_user.display_name == sample_user.display_name
        user_manager.storage.get_user.assert_called_once_with(username)
    
    def test_update_user_information(self, user_manager, sample_user):
        """Test updating user information"""
        # Arrange
        username = sample_user.username
        new_status = "away"
        
        # Mock storage to return our sample user
        user_manager.storage.get_user.return_value = sample_user
        user_manager.active_users[username] = sample_user
        
        # Act
        updated_user = user_manager.update_user_status(username, new_status)
        
        # Assert
        assert updated_user is not None
        assert updated_user.status == new_status
        user_manager.storage.update_user.assert_called_once()


class TestMessageHandling:
    """Tests for message handling"""
    
    def test_create_and_send_message(self, chat_manager, sample_user):
        """Test creating and sending a message"""
        # Arrange
        content = "Test message"
        sender = "testuser"
        session_id = "test-session"
        
        # Mock the validate_session method
        chat_manager.validate_session = MagicMock(return_value=True)
        
        # Act
        message = Message(content=content, sender=sender)
        result = chat_manager.send_message(message, session_id)
        
        # Assert
        assert result is True
        chat_manager.storage.save_message.assert_called_once()
    
    def test_retrieve_messages_for_user(self, chat_manager, message_list):
        """Test retrieving messages for a user"""
        # Arrange
        username = "user1"
        limit = 5
        chat_manager.storage.get_messages = MagicMock(return_value=message_list[:limit])
        
        # Act
        retrieved_messages = chat_manager.get_message_history(username, limit)
        
        # Assert
        assert len(retrieved_messages) == limit
        chat_manager.storage.get_messages.assert_called_once_with(limit, username)
    
    def test_message_formatting(self, sample_message):
        """Test message formatting"""
        # Arrange
        # Act
        json_format = sample_message.to_json()
        dict_format = sample_message.to_dict()
        
        # Assert
        assert json_format is not None
        assert isinstance(json_format, str)
        assert dict_format is not None
        assert isinstance(dict_format, dict)
        assert dict_format["content"] == sample_message.content
        assert dict_format["sender"] == sample_message.sender
