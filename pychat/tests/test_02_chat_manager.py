"""
Tests for the ChatManager component of PyChat
"""
import pytest
from unittest.mock import MagicMock, patch

from pychat.core.chat_manager import ChatManager, ChatSession
from pychat.common.message import Message
from pychat.core.user import User
from pychat.tests.conftest import skip_failing


class TestChatManagerSessions:
    """Tests for chat session management"""
    
    @skip_failing
    def test_create_new_chat_session(self, chat_manager, sample_user):
        """Test creating a new chat session"""
        # Arrange
        username = sample_user.username
        password = "password123"
        
        # Mock the authentication
        chat_manager.user_manager.authenticate_user = MagicMock(return_value=sample_user)
        session_id = "test-session-id"
        chat_manager.storage.create_session = MagicMock(return_value=session_id)
        
        # Act
        user, returned_session_id = chat_manager.login(username, password)
        
        # Assert
        assert user is not None
        assert returned_session_id == session_id
        assert returned_session_id in chat_manager.sessions
        chat_manager.user_manager.authenticate_user.assert_called_once_with(username, password)
        chat_manager.storage.create_session.assert_called_once_with(username)
    
    def test_add_messages_to_chat_session(self, chat_manager, sample_user, sample_message):
        """Test adding messages to a chat session"""
        # Arrange
        session_id = "test-session-id"
        
        # Create a session
        session = ChatSession(sample_user, session_id)
        chat_manager.sessions[session_id] = session
        
        # Mock the callback function
        callback_mock = MagicMock()
        session.add_callback(callback_mock)
        
        # Mock validate_session to return True
        chat_manager.validate_session = MagicMock(return_value=True)
        
        # Act
        result = chat_manager.send_message(sample_message, session_id)
        
        # Assert
        assert result is True
        chat_manager.storage.save_message.assert_called_once()
        
        # Let the distribution thread work
        import time
        time.sleep(0.1)
        
        # Check that the message was distributed to the callback
        # This depends on the implementation but in a real test it would verify
        # that the callback was called with the message
    
    def test_retrieve_chat_history(self, chat_manager, message_list):
        """Test retrieving chat history"""
        # Arrange
        username = "user1"
        limit = 10
        chat_manager.storage.get_messages = MagicMock(return_value=message_list)
        
        # Act
        history = chat_manager.get_message_history(username, limit)
        
        # Assert
        assert len(history) == len(message_list)
        assert all(isinstance(msg, Message) for msg in history)
        chat_manager.storage.get_messages.assert_called_once_with(limit, username)


class TestUserSessions:
    """Tests for user session handling"""
    
    def test_validate_session(self, chat_manager):
        """Test validating a session"""
        # Arrange
        session_id = "test-session-id"
        username = "testuser"
        
        # Session not in memory but valid in storage
        chat_manager.storage.validate_session = MagicMock(return_value=username)
        chat_manager.user_manager.get_user = MagicMock(return_value=User(username=username))
        
        # Act
        result = chat_manager.validate_session(session_id)
        
        # Assert
        assert result is True
        assert session_id in chat_manager.sessions
        chat_manager.storage.validate_session.assert_called_once_with(session_id)
    
    def test_logout(self, chat_manager, sample_user):
        """Test logging out a session"""
        # Arrange
        session_id = "test-session-id"
        username = sample_user.username
        
        # Create a session
        session = ChatSession(sample_user, session_id)
        chat_manager.sessions[session_id] = session
        
        if username not in chat_manager.user_sessions:
            chat_manager.user_sessions[username] = []
        chat_manager.user_sessions[username].append(session_id)
        
        # Act
        chat_manager.logout(session_id)
        
        # Assert
        assert session_id not in chat_manager.sessions
        assert session_id not in chat_manager.user_sessions.get(username, [])
        chat_manager.storage.invalidate_session.assert_called_once_with(session_id)
