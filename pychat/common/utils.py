"""
Utility functions for PyChat
"""
import os
import json
import datetime
import hashlib
import uuid
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pychat.common.message import Message


def ensure_directory(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def get_app_data_dir() -> str:
    """
    Get the application data directory for PyChat.
    
    Returns:
        The path to the application data directory
    """
    # Get user's home directory
    home_dir = os.path.expanduser("~")
    
    # Create app-specific directory
    app_dir = os.path.join(home_dir, ".pychat")
    ensure_directory(app_dir)
    
    return app_dir


def serialize_datetime(obj: Any) -> Any:
    """
    JSON serializer for datetime objects
    
    Args:
        obj: Object to serialize
        
    Returns:
        Serialized object
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """
    Save data to a JSON file
    
    Args:
        data: Data to save
        filepath: Path to the file
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, default=serialize_datetime, indent=2)


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load data from a JSON file
    
    Args:
        filepath: Path to the file
        
    Returns:
        Loaded data
    """
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, 'r') as f:
        return json.load(f)


def format_message_for_display(sender: str, content: str, timestamp: datetime.datetime = None) -> str:
    """
    Format a message for display in the CLI
    
    Args:
        sender: The username of the sender
        content: The message content
        timestamp: The message timestamp (optional)
        
    Returns:
        Formatted message string
    """
    if timestamp is None:
        timestamp = datetime.datetime.now()
    
    time_str = timestamp.strftime("%H:%M:%S")
    return f"[{time_str}] {sender}: {content}"


def generate_random_id() -> str:
    """
    Generate a random ID
    
    Returns:
        Random ID string
    """
    return str(uuid.uuid4())


def validate_username(username: str) -> bool:
    """
    Validate a username
    
    Args:
        username: The username to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Username should be 3-20 characters, alphanumeric and underscores only
    pattern = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    return bool(pattern.match(username))


def validate_email(email: str) -> bool:
    """
    Validate an email address
    
    Args:
        email: The email to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return True  # Empty email is valid (optional)
    
    # Simple email validation pattern
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(pattern.match(email))


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate a password
    
    Args:
        password: The password to validate
        
    Returns:
        Tuple of (valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    return True, None


def format_timestamp(timestamp: datetime.datetime, include_date: bool = False) -> str:
    """
    Format a timestamp for display
    
    Args:
        timestamp: The timestamp to format
        include_date: Whether to include the date
        
    Returns:
        Formatted timestamp string
    """
    if include_date:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp.strftime("%H:%M:%S")


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to a maximum length
    
    Args:
        text: The text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_private_message(message: 'Message', current_user: str) -> str:
    """
    Format a private message for display
    
    Args:
        message: The message to format
        current_user: The current user's username
        
    Returns:
        Formatted message string
    """
    time_str = message.timestamp.strftime('%H:%M:%S')
    
    if message.sender == current_user:
        return f"[{time_str}] You -> {message.recipient}: {message.content}"
    else:
        return f"[{time_str}] {message.sender} -> You: {message.content}"
