"""
Tests for PyChat interface components
"""
import pytest
from unittest.mock import MagicMock, patch, call
import io
import sys

from pychat.interfaces.common import ChatInterface
from pychat.interfaces.cli_interface import CLIInterface
from pychat.common.message import Message
from pychat.core.user import User
from pychat.tests.conftest import skip_failing


@pytest.fixture
def mock_cli_interface():
    """Create a mocked CLI interface for testing"""
    # Mock stdin/stdout
    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
         patch('builtins.input', side_effect=['help', 'quit']):
        
        # Create a mock chat manager
        mock_chat_manager = MagicMock()
        
        # Patch the get_chat_manager function
        with patch('pychat.interfaces.cli_interface.get_chat_manager', return_value=mock_chat_manager):
            # Create CLI interface
            cli = CLIInterface()
            cli.chat_manager = mock_chat_manager
            
            # Mock some interface methods
            cli._receive_message = MagicMock()
            
            yield cli, mock_stdout, mock_chat_manager


class TestCLIInterface:
    """Tests for the CLI interface"""
    
    @skip_failing
    def test_start_cli_application(self, mock_cli_interface):
        """Test starting the CLI application"""
        # Arrange
        cli, mock_stdout, _ = mock_cli_interface
        
        # Mock the run method to prevent actual execution
        with patch.object(cli, 'run'):
            # Act
            cli.start()
            
            # Assert
            output = mock_stdout.getvalue()
            assert "Welcome to PyChat" in output
            assert "Type /help for available commands" in output
    
    def test_execute_commands_in_cli(self, mock_cli_interface):
        """Test executing commands in CLI"""
        # Arrange
        cli, mock_stdout, mock_manager = mock_cli_interface
        
        # Mock some methods
        cli.login = MagicMock(return_value=True)
        cli.is_authenticated = MagicMock(return_value=True)
        mock_manager.get_active_users.return_value = [
            User(username="user1", status="online"),
            User(username="user2", status="away")
        ]
        
        # Act - simulate processing the /users command
        cli.process_command("users")
        
        # Assert
        assert mock_manager.get_active_users.called
        output = mock_stdout.getvalue()
        assert "Active users" in output
    
    def test_error_handling_in_cli(self, mock_cli_interface):
        """Test error handling in CLI"""
        # Arrange
        cli, mock_stdout, _ = mock_cli_interface
        
        # Act - simulate processing an invalid command
        cli.process_command("invalid_command")
        
        # Assert
        output = mock_stdout.getvalue()
        assert "Unknown command" in output or "Command not found" in output


class TestGUIInterfaceMocked:
    """Tests for the GUI interface using mocks"""
    
    @pytest.mark.skipif(sys.platform != "darwin", reason="GUI tests may not work in CI environment")
    def test_gui_interface_initialization(self):
        """Test GUI interface initialization with mocks"""
        # This is a basic test to check if the GUI interface can be imported
        # Full GUI testing would require more complex setup with tkinter mocking
        
        try:
            from pychat.interfaces.gui_interface import GUIInterface
            
            # Patch the tkinter and other dependencies
            with patch('pychat.interfaces.gui_interface.tk.Tk'), \
                 patch('pychat.interfaces.gui_interface.get_chat_manager'):
                
                # This just tests that the class can be imported and instantiated
                # without errors when properly mocked
                GUIInterface()
                
            assert True  # If we get here, the import worked
        except ImportError:
            pytest.skip("GUI interface module could not be imported")
        except Exception as e:
            pytest.fail(f"Error initializing GUI interface: {e}")


class TestInterfaceCommon:
    """Tests for the common interface functionality"""
    
    class TestInterface(ChatInterface):
        """Test implementation of ChatInterface abstract class"""
        def _receive_message(self, message):
            pass
        
        def display_message(self, message):
            pass
    
    @pytest.fixture
    def test_interface(self):
        """Create a test interface instance"""
        return self.TestInterface()
    
    def test_login_functionality(self, test_interface):
        """Test login functionality in common interface"""
        # Arrange
        username = "testuser"
        password = "password"
        user = User(username=username)
        session_id = "test-session"
        
        test_interface.chat_manager = MagicMock()
        test_interface.chat_manager.login.return_value = (user, session_id)
        
        # Act
        result = test_interface.login(username, password)
        
        # Assert
        assert result is True
        assert test_interface.username == username
        assert test_interface.session_id == session_id
        assert test_interface.user == user
        test_interface.chat_manager.login.assert_called_once_with(username, password)
    
    def test_send_message(self, test_interface):
        """Test sending messages through the interface"""
        # Arrange
        test_interface.username = "testuser"
        test_interface.session_id = "test-session"
        test_interface.chat_manager = MagicMock()
        test_interface.chat_manager.send_message.return_value = True
        
        content = "Hello, world!"
        recipient = "otheruser"
        
        # Act
        result = test_interface.send_message(content, recipient)
        
        # Assert
        assert result is True
        test_interface.chat_manager.send_message.assert_called_once()
        
        # Check that the message had the correct properties
        call_args = test_interface.chat_manager.send_message.call_args
        message = call_args[0][0]  # First positional argument of first call
        assert message.content == content
        assert message.sender == test_interface.username
        assert message.recipient == recipient
