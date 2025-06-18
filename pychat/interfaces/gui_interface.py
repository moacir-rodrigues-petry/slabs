"""
Graphical user interface for PyChat
This is a placeholder for Phase 3 implementation
"""
from typing import Optional

from pychat.common.message import Message
from pychat.interfaces.common import ChatInterface


class GUIInterface(ChatInterface):
    """
    Graphical user interface for PyChat
    To be implemented in Phase 3
    """
    def __init__(self, username: str, display_name: Optional[str] = None):
        """
        Initialize the GUI interface
        
        Args:
            username: Username for this interface
            display_name: Display name (defaults to username)
        """
        super().__init__(username, display_name)
        
        print("GUI interface not implemented yet (coming in Phase 3)")
        
    def _receive_message(self, message: Message) -> None:
        """
        Handle received messages
        
        Args:
            message: The received message
        """
        # To be implemented in Phase 3
        pass
    
    def run(self) -> None:
        """Run the GUI interface"""
        # To be implemented in Phase 3
        pass


def main() -> None:
    """Main entry point for the GUI interface"""
    print("GUI interface will be implemented in Phase 3")
    print("Please use the CLI interface for now")


if __name__ == "__main__":
    main()
