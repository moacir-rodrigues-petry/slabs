"""
Command-line interface for PyChat
"""
import sys
import threading
import time
import readline  # For better input handling
from typing import List, Optional

from pychat.common.message import Message
from pychat.common.utils import format_message_for_display
from pychat.interfaces.common import ChatInterface
from pychat.core.user import User


class CLIInterface(ChatInterface):
    """
    Command-line interface for PyChat
    """
    def __init__(self, username: str, display_name: Optional[str] = None):
        """
        Initialize the CLI interface
        
        Args:
            username: Username for this interface
            display_name: Display name (defaults to username)
        """
        super().__init__(username, display_name)
        
        # For displaying messages
        self.message_lock = threading.Lock()
        self.running = True
        
        # Show welcome message and instructions
        self._show_welcome()
        
        # Show message history
        self._show_message_history()
    
    def _show_welcome(self) -> None:
        """Show welcome message and instructions"""
        print("\n==================================================")
        print("Welcome to PyChat!")
        print(f"You are logged in as: {self.user}")
        print("==================================================")
        print("Commands:")
        print("  /help              - Show this help message")
        print("  /quit              - Exit the chat")
        print("  /users             - List active users")
        print("  /msg <user> <text> - Send private message")
        print("  /history           - Show message history")
        print("==================================================\n")
    
    def _show_message_history(self, limit: int = 10) -> None:
        """
        Show message history
        
        Args:
            limit: Maximum number of messages to show
        """
        messages = self.get_message_history(limit)
        if not messages:
            print("No message history.")
            return
        
        print(f"\nLast {len(messages)} messages:")
        for message in messages:
            print(str(message))
        print()
    
    def _receive_message(self, message: Message) -> None:
        """
        Handle received messages
        
        Args:
            message: The received message
        """
        with self.message_lock:
            # Clear the current line
            sys.stdout.write("\r" + " " * 80 + "\r")
            # Print the message
            print(str(message))
            # Reprint the input prompt
            sys.stdout.write("> ")
            sys.stdout.flush()
    
    def _list_users(self) -> None:
        """List active users"""
        users = self.get_active_users()
        if not users:
            print("No active users.")
            return
        
        print("\nActive users:")
        for user in users:
            if user.username == self.username:
                print(f"  {user} (You)")
            else:
                print(f"  {user}")
        print()
    
    def _process_command(self, command: str) -> bool:
        """
        Process a command
        
        Args:
            command: The command to process
            
        Returns:
            True if the interface should continue running, False to exit
        """
        # Help command
        if command == "/help":
            self._show_welcome()
            return True
        
        # Quit command
        if command == "/quit":
            print("Goodbye!")
            return False
        
        # List users command
        if command == "/users":
            self._list_users()
            return True
        
        # Show history command
        if command == "/history":
            self._show_message_history(20)
            return True
        
        # Private message command
        if command.startswith("/msg "):
            parts = command.split(" ", 2)
            if len(parts) < 3:
                print("Usage: /msg <username> <message>")
                return True
            
            recipient = parts[1]
            content = parts[2]
            
            # Check if user exists
            users = {user.username: user for user in self.get_active_users()}
            if recipient not in users:
                print(f"User '{recipient}' is not active.")
                return True
            
            # Send the message
            self.send_message(content, recipient)
            return True
        
        # Unknown command
        if command.startswith("/"):
            print(f"Unknown command: {command}")
            return True
        
        return True
    
    def run(self) -> None:
        """Run the CLI interface"""
        try:
            while self.running:
                try:
                    # Get input from user
                    user_input = input("> ")
                    
                    # Process commands
                    if user_input.startswith("/"):
                        self.running = self._process_command(user_input)
                        continue
                    
                    # Send normal message
                    if user_input.strip():
                        self.send_message(user_input)
                
                except KeyboardInterrupt:
                    print("\nUse /quit to exit.")
                except EOFError:
                    break
        
        finally:
            # Clean up
            self.shutdown()


def main() -> None:
    """Main entry point for the CLI interface"""
    # Get username
    username = input("Enter your username: ")
    if not username:
        print("Username cannot be empty.")
        return
    
    # Get display name (optional)
    display_name = input("Enter your display name (or press Enter to use username): ")
    if not display_name:
        display_name = username
    
    # Create and run interface
    interface = CLIInterface(username, display_name)
    interface.run()


if __name__ == "__main__":
    main()
