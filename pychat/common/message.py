"""
Message format and serialization for PyChat
"""
import json
import uuid
import datetime
from typing import Dict, Any, Optional


class Message:
    """
    Represents a chat message in the PyChat application.
    """
    def __init__(self, 
                 content: str, 
                 sender: str, 
                 recipient: Optional[str] = None, 
                 msg_id: Optional[str] = None,
                 timestamp: Optional[datetime.datetime] = None):
        """
        Initialize a new message.
        
        Args:
            content: The text content of the message
            sender: The username of the sender
            recipient: The username of the recipient (None for broadcast)
            msg_id: A unique identifier for the message (auto-generated if None)
            timestamp: The time the message was sent (auto-generated if None)
        """
        self.content = content
        self.sender = sender
        self.recipient = recipient  # None means broadcast to all
        self.msg_id = msg_id if msg_id else str(uuid.uuid4())
        self.timestamp = timestamp if timestamp else datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            'msg_id': self.msg_id,
            'content': self.content,
            'sender': self.sender,
            'recipient': self.recipient,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from dictionary"""
        return cls(
            content=data['content'],
            sender=data['sender'],
            recipient=data.get('recipient'),
            msg_id=data['msg_id'],
            timestamp=datetime.datetime.fromisoformat(data['timestamp'])
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create a message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """String representation of the message"""
        time_str = self.timestamp.strftime('%H:%M:%S')
        if self.recipient:
            return f"[{time_str}] {self.sender} -> {self.recipient}: {self.content}"
        return f"[{time_str}] {self.sender}: {self.content}"
