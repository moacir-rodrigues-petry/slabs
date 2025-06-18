"""
Command-line interface for PyChat
"""
import sys
import threading
import time
import readline  # For better input handling
import getpass
from typing import List, Optional, Dict, Any

from pychat.common.message import Message
from pychat.common.utils import format_message_for_display
from pychat.interfaces.common import ChatInterface
from pychat.core.user import User


class CLIInterface(ChatInterface):
    """
    Command-line interface for PyChat
    """
    def __init__(self):
        """Initialize the CLI interface"""
        super().__init__()
        
        # For displaying messages
        self.message_lock = threading.Lock()
        self.running = True
    
    def _login_prompt(self) -> bool:
        """
        Show login prompt
        
        Returns:
            True if login successful, False otherwise
        """
        print("\n==================================================")
        print("PyChat Login")
        print("==================================================")
        
        # Get username and password
        username = input("Username: ")
        if not username:
            print("Username cannot be empty.")
            return False
        
        password = getpass.getpass("Password: ")
        if not password:
            print("Password cannot be empty.")
            return False
        
        # Try to login
        if self.login(username, password):
            print(f"Welcome back, {self.user.display_name}!")
            return True
        else:
            print("Login failed. Invalid username or password.")
            return False
    
    def _register_prompt(self) -> bool:
        """
        Show registration prompt
        
        Returns:
            True if registration successful, False otherwise
        """
        print("\n==================================================")
        print("PyChat Registration")
        print("==================================================")
        
        # Get registration info
        username = input("Username: ")
        if not username:
            print("Username cannot be empty.")
            return False
        
        display_name = input("Display Name (optional): ")
        if not display_name:
            display_name = username
        
        email = input("Email (optional): ")
        
        password = getpass.getpass("Password: ")
        if not password:
            print("Password cannot be empty.")
            return False
        
        password_confirm = getpass.getpass("Confirm Password: ")
        if password != password_confirm:
            print("Passwords do not match.")
            return False
        
        # Try to register
        if self.register(username, password, display_name, email):
            print("Registration successful!")
            
            # Auto-login
            if self.login(username, password):
                print(f"Welcome, {self.user.display_name}!")
                return True
            else:
                print("Auto-login failed. Please login manually.")
                return False
        else:
            print("Registration failed. Username may already be taken.")
            return False
    
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
        print("  /history [n]       - Show message history (default: 10)")
        print("  /profile [user]    - View user profile")
        print("  /conversations     - List private conversations")
        print("  /status <status>   - Update your status (online, away, busy)")
        print("  /logout            - Logout from current session")
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
    
    def _show_profile(self, username: Optional[str] = None) -> None:
        """
        Show user profile
        
        Args:
            username: Username to show profile for (current user if None)
        """
        profile = self.get_user_profile(username)
        if not profile:
            print(f"User {username or 'profile'} not found.")
            return
        
        print("\nUser Profile:")
        print(f"  Username: {profile['username']}")
        print(f"  Display Name: {profile['display_name']}")
        if profile.get('email'):
            print(f"  Email: {profile['email']}")
        print(f"  Status: {profile['status']}")
        print(f"  Last Seen: {profile['last_seen']}")
        print()
    
    def _list_conversations(self) -> None:
        """List private conversations"""
        conversations = self.get_conversations()
        if not conversations:
            print("No private conversations.")
            return
        
        print("\nPrivate conversations:")
        for user, last_time in conversations:
            print(f"  {user.display_name} ({user.username}) - Last message: {last_time}")
        print()
    
    def _update_status(self, status: str) -> None:
        """
        Update user status
        
        Args:
            status: New status (online, away, busy)
        """
        if status not in ['online', 'away', 'busy', 'offline']:
            print("Invalid status. Use 'online', 'away', or 'busy'.")
            return
        
        if self.update_status(status):
            print(f"Status updated to: {status}")
        else:
            print("Failed to update status.")
    
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
        if command.startswith("/history"):
            parts = command.split()
            limit = 10
            if len(parts) > 1:
                try:
                    limit = int(parts[1])
                except ValueError:
                    print("Invalid limit. Using default (10).")
            
            self._show_message_history(limit)
            return True
        
        # Profile command
        if command.startswith("/profile"):
            parts = command.split()
            username = None
            if len(parts) > 1:
                username = parts[1]
            
            self._show_profile(username)
            return True
        
        # Conversations command
        if command == "/conversations":
            self._list_conversations()
            return True
        
        # Status command
        if command.startswith("/status"):
            parts = command.split()
            if len(parts) < 2:
                print("Usage: /status <online|away|busy>")
                return True
            
            self._update_status(parts[1])
            return True
        
        # Logout command
        if command == "/logout":
            self.logout()
            print("You have been logged out.")
            
            # Prompt for login
            if not self._auth_prompt():
                return False
            
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
            if not self.chat_manager.get_user(recipient):
                print(f"User '{recipient}' does not exist.")
                return True
            
            # Send the message
            if self.send_message(content, recipient):
                pass  # Message will be displayed by the callback
            else:
                print("Failed to send message.")
            
            return True
        
        # Unknown command
        if command.startswith("/"):
            print(f"Unknown command: {command}")
            return True
        
        return True
    
    def _auth_prompt(self) -> bool:
        """
        Show authentication prompt
        
        Returns:
            True if authentication successful, False to exit
        """
        while True:
            print("\n==================================================")
            print("Welcome to PyChat!")
            print("==================================================")
            print("1. Login")
            print("2. Register")
            print("3. Exit")
            
            choice = input("Choose an option (1-3): ")
            
            if choice == "1":
                if self._login_prompt():
                    return True
            elif choice == "2":
                if self._register_prompt():
                    return True
            elif choice == "3":
                return False
            else:
                print("Invalid option. Please try again.")
    
    def run(self) -> None:
        """Run the CLI interface"""
        try:
            # Authenticate first
            if not self._auth_prompt():
                return
            
            # Show welcome message and message history
            self._show_welcome()
            self._show_message_history()
            
            while self.running and self.is_authenticated():
                try:
                    # Get input from user
                    user_input = input("> ")
                    
                    # Process commands
                    if user_input.startswith("/"):
                        self.running = self._process_command(user_input)
                        if not self.running:
                            break
                        
                        # Check if still authenticated after command
                        if not self.is_authenticated():
                            print("Your session has expired. Please login again.")
                            if not self._auth_prompt():
                                break
                        
                        continue
                    
                    # Send normal message
                    if user_input.strip():
                        if not self.send_message(user_input):
                            print("Failed to send message. You may need to login again.")
                            if not self._auth_prompt():
                                break
                
                except KeyboardInterrupt:
                    print("\nUse /quit to exit.")
                except EOFError:
                    break
        
        finally:
            # Clean up
            self.shutdown()


def main() -> None:
    """Main entry point for the CLI interface"""
    interface = CLIInterface()
    interface.run()


if __name__ == "__main__":
    main()
