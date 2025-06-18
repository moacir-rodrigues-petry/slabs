"""
Utility functions for PyChat
"""
import os
import json
import datetime
from typing import Any, Dict, List


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
