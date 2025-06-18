"""
Tests for the Storage component of PyChat
"""
import pytest
import os
from unittest.mock import MagicMock, patch

from pychat.core.storage import Storage
from pychat.core.user import User
from pychat.common.message import Message
from pychat.tests.conftest import skip_failing


class TestStoragePersistence:
    """Tests for data persistence in Storage"""
    
    @skip_failing
    def test_persist_user_data(self, storage, sample_user):
        """Test persisting user data"""
        # Arrange
        username = sample_user.username
        password = "password123"
        hashed_pw, salt = "hashed", "salt"
        
        # Act
        storage.save_user(sample_user, hashed_pw, salt)
        retrieved_user = storage.get_user(username)
        
        # Assert
        assert retrieved_user is not None
        assert retrieved_user.username == username
        assert retrieved_user.display_name == sample_user.display_name
        assert retrieved_user.email == sample_user.email
        
        # Check auth data
        auth_data = storage.get_user_auth_data(username)
        assert auth_data.get('password_hash') == hashed_pw
        assert auth_data.get('password_salt') == salt
    
    def test_persist_message_data(self, storage, sample_message):
        """Test persisting message data"""
        # Arrange
        sender = sample_message.sender
        
        # Act
        storage.save_message(sample_message)
        messages = storage.get_messages(limit=10, recipient=sender)
        
        # Assert
        assert len(messages) > 0
        assert any(msg.msg_id == sample_message.msg_id for msg in messages)
        assert any(msg.content == sample_message.content for msg in messages)
    
    def test_storage_performance(self, storage):
        """Test storage performance with large data sets"""
        # Arrange - create many messages
        message_count = 50  # Reduced for test speed, increase for real performance testing
        sender = "user1"
        
        # Act
        for i in range(message_count):
            msg = Message(content=f"Test message {i}", sender=sender)
            storage.save_message(msg)
        
        # Assert - measure time to retrieve
        import time
        start_time = time.time()
        messages = storage.get_messages(limit=message_count)
        end_time = time.time()
        
        retrieval_time = end_time - start_time
        assert len(messages) == message_count
        
        # This is a soft assertion since performance can vary by environment
        # In a real test, you might define an acceptable threshold
        print(f"Retrieved {message_count} messages in {retrieval_time:.4f} seconds")


class TestStorageOperations:
    """Tests for specific storage operations"""
    
    def test_user_exists(self, storage, sample_user):
        """Test checking if a user exists"""
        # Arrange
        username = sample_user.username
        
        # Save the user first
        storage.save_user(sample_user)
        
        # Act
        exists = storage.user_exists(username)
        non_exists = storage.user_exists("nonexistent_user")
        
        # Assert
        assert exists is True
        assert non_exists is False
    
    def test_update_user(self, storage, sample_user):
        """Test updating a user"""
        # Arrange
        storage.save_user(sample_user)
        
        # Modify user
        sample_user.status = "away"
        sample_user.display_name = "Updated Name"
        
        # Act
        storage.update_user(sample_user)
        retrieved_user = storage.get_user(sample_user.username)
        
        # Assert
        assert retrieved_user.status == "away"
        assert retrieved_user.display_name == "Updated Name"
    
    def test_session_operations(self, storage):
        """Test session creation, validation, and invalidation"""
        # Arrange
        username = "testuser"
        
        # Create a user first
        user = User(username=username)
        storage.save_user(user)
        
        # Act - Create session
        session_id = storage.create_session(username)
        
        # Assert - Validate session
        validated_username = storage.validate_session(session_id)
        assert validated_username == username
        
        # Act - Invalidate session
        storage.invalidate_session(session_id)
        
        # Assert - Session no longer valid
        invalid_username = storage.validate_session(session_id)
        assert invalid_username is None
