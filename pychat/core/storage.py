"""
Storage module for PyChat
"""
import os
import sqlite3
import datetime
from typing import List, Optional, Dict, Any

from pychat.common.message import Message
from pychat.common.utils import get_app_data_dir, ensure_directory


class Storage:
    """
    Handles persistent storage for messages and user profiles
    """
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the storage with a SQLite database
        
        Args:
            db_path: Path to SQLite database (default: ~/.pychat/pychat.db)
        """
        if db_path is None:
            app_dir = get_app_data_dir()
            db_path = os.path.join(app_dir, "pychat.db")
        
        self.db_path = db_path
        ensure_directory(os.path.dirname(db_path))
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Initialize tables
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            msg_id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            sender TEXT NOT NULL,
            recipient TEXT,
            timestamp TEXT NOT NULL
        )
        ''')
        
        # Create users table (for Phase 2)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            display_name TEXT,
            last_seen TEXT
        )
        ''')
        
        self.conn.commit()
    
    def save_message(self, message: Message) -> None:
        """
        Save a message to the database
        
        Args:
            message: The message to save
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO messages (msg_id, content, sender, recipient, timestamp) VALUES (?, ?, ?, ?, ?)",
            (message.msg_id, message.content, message.sender, message.recipient, message.timestamp.isoformat())
        )
        self.conn.commit()
    
    def get_messages(self, limit: int = 100, recipient: Optional[str] = None) -> List[Message]:
        """
        Retrieve messages from the database
        
        Args:
            limit: Maximum number of messages to retrieve
            recipient: Filter messages by recipient (None for all messages)
            
        Returns:
            List of Message objects
        """
        cursor = self.conn.cursor()
        
        if recipient is None:
            query = """
            SELECT * FROM messages 
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            cursor.execute(query, (limit,))
        else:
            query = """
            SELECT * FROM messages 
            WHERE recipient IS NULL OR recipient = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            cursor.execute(query, (recipient, limit))
        
        rows = cursor.fetchall()
        messages = []
        
        for row in rows:
            message = Message(
                content=row['content'],
                sender=row['sender'],
                recipient=row['recipient'],
                msg_id=row['msg_id'],
                timestamp=datetime.datetime.fromisoformat(row['timestamp'])
            )
            messages.append(message)
        
        # Return in chronological order
        return list(reversed(messages))
    
    def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self) -> None:
        """Ensure connection is closed on deletion"""
        self.close()
