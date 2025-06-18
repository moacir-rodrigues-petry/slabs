"""
Storage module for PyChat
"""
import os
import sqlite3
import datetime
import uuid
from typing import List, Optional, Dict, Any, Tuple, TYPE_CHECKING

from pychat.common.message import Message
from pychat.common.utils import get_app_data_dir, ensure_directory

if TYPE_CHECKING:
    from pychat.core.user import User


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
        
        # Create users table (Phase 2)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            email TEXT,
            status TEXT DEFAULT 'offline',
            last_seen TEXT
        )
        ''')
        
        # Create user authentication table (Phase 2)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_auth (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username)
        )
        ''')
        
        # Create sessions table (Phase 2)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (username) REFERENCES users(username)
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
            WHERE recipient IS NULL OR recipient = ? OR sender = ?
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            cursor.execute(query, (recipient, recipient, limit))
        
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
    
    def save_user(self, user: 'User', password_hash: Optional[str] = None, 
                 password_salt: Optional[str] = None) -> None:
        """
        Save a user to the database
        
        Args:
            user: The user to save
            password_hash: Optional password hash
            password_salt: Optional password salt
        """
        cursor = self.conn.cursor()
        
        # Generate user_id if not present
        if not user.user_id:
            user.user_id = str(uuid.uuid4())
        
        # Save user data
        cursor.execute(
            """
            INSERT OR REPLACE INTO users 
            (user_id, username, display_name, email, status, last_seen) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.user_id,
                user.username,
                user.display_name,
                user.email,
                user.status,
                user.last_seen.isoformat() if user.last_seen else None
            )
        )
        
        # Save authentication data if provided
        if password_hash and password_salt:
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_auth
                (username, password_hash, password_salt)
                VALUES (?, ?, ?)
                """,
                (user.username, password_hash, password_salt)
            )
        
        self.conn.commit()
    
    def update_user(self, user: 'User') -> None:
        """
        Update a user in the database
        
        Args:
            user: The user to update
        """
        cursor = self.conn.cursor()
        
        # Update user data
        cursor.execute(
            """
            UPDATE users SET
            display_name = ?,
            email = ?,
            status = ?,
            last_seen = ?
            WHERE username = ?
            """,
            (
                user.display_name,
                user.email,
                user.status,
                user.last_seen.isoformat() if user.last_seen else None,
                user.username
            )
        )
        
        self.conn.commit()
    
    def get_user(self, username: str) -> Optional['User']:
        """
        Get a user by username
        
        Args:
            username: The username to look up
            
        Returns:
            User object if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Import here to avoid circular import
        from pychat.core.user import User
        
        user = User(
            username=row['username'],
            display_name=row['display_name'],
            email=row['email'],
            status=row['status'],
            user_id=row['user_id']
        )
        
        if row['last_seen']:
            user.last_seen = datetime.datetime.fromisoformat(row['last_seen'])
        
        return user
    
    def get_users(self, status: Optional[str] = None) -> List['User']:
        """
        Get all users
        
        Args:
            status: Optional filter by status
            
        Returns:
            List of User objects
        """
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM users WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT * FROM users")
        
        rows = cursor.fetchall()
        
        # Import here to avoid circular import
        from pychat.core.user import User
        
        users = []
        for row in rows:
            user = User(
                username=row['username'],
                display_name=row['display_name'],
                email=row['email'],
                status=row['status'],
                user_id=row['user_id']
            )
            
            if row['last_seen']:
                user.last_seen = datetime.datetime.fromisoformat(row['last_seen'])
            
            users.append(user)
        
        return users
    
    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists
        
        Args:
            username: The username to check
            
        Returns:
            True if user exists, False otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None
    
    def get_user_auth_data(self, username: str) -> Dict[str, str]:
        """
        Get authentication data for a user
        
        Args:
            username: The username to look up
            
        Returns:
            Dictionary with 'password_hash' and 'password_salt'
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash, password_salt FROM user_auth WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if not row:
            return {}
        
        return {
            'password_hash': row['password_hash'],
            'password_salt': row['password_salt']
        }
    
    def create_session(self, username: str, expires_in: int = 86400) -> str:
        """
        Create a new session for a user
        
        Args:
            username: The username to create a session for
            expires_in: Session duration in seconds (default: 24 hours)
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        created_at = datetime.datetime.now()
        expires_at = created_at + datetime.timedelta(seconds=expires_in)
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions
            (session_id, username, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                username,
                created_at.isoformat(),
                expires_at.isoformat()
            )
        )
        
        self.conn.commit()
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """
        Validate a session and return the associated username
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            Username if session is valid, None otherwise
        """
        now = datetime.datetime.now().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT username FROM sessions
            WHERE session_id = ?
            AND expires_at > ?
            AND is_active = 1
            """,
            (session_id, now)
        )
        
        row = cursor.fetchone()
        return row['username'] if row else None
    
    def invalidate_session(self, session_id: str) -> None:
        """
        Invalidate a session
        
        Args:
            session_id: The session ID to invalidate
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET is_active = 0 WHERE session_id = ?",
            (session_id,)
        )
        self.conn.commit()
    
    def get_private_conversations(self, username: str) -> List[Tuple[str, datetime.datetime]]:
        """
        Get a list of users that the given user has had private conversations with
        
        Args:
            username: The username to look up conversations for
            
        Returns:
            List of tuples (username, last_message_time)
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT
                CASE
                    WHEN sender = ? THEN recipient
                    ELSE sender
                END as other_user,
                MAX(timestamp) as last_message
            FROM messages
            WHERE 
                (sender = ? AND recipient IS NOT NULL)
                OR
                (recipient = ?)
            GROUP BY other_user
            ORDER BY last_message DESC
            """,
            (username, username, username)
        )
        
        rows = cursor.fetchall()
        return [(row['other_user'], datetime.datetime.fromisoformat(row['last_message'])) 
                for row in rows if row['other_user']]
    
    def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self) -> None:
        """Ensure connection is closed on deletion"""
        self.close()
