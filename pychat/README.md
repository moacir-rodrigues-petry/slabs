# PyChat - Phase 1 Implementation

This is the Phase 1 implementation of PyChat, a simple, lightweight chat application built with Python 3.

## Features Implemented in Phase 1

- Basic chat core module with message handling
- In-memory and SQLite storage for messages
- Simple user management
- Command-line interface
- Support for broadcast and private messaging
- Message history

## Running the Application

To run the PyChat command-line interface:

1. Navigate to the project root directory
2. Run:
   ```
   python -m pychat.interfaces.cli_interface
   ```

## Commands

Once running, the following commands are available:

- `/help` - Show help message
- `/quit` - Exit the chat
- `/users` - List active users
- `/msg <user> <text>` - Send private message
- `/history` - Show message history

## Development

- To run tests: `python -m unittest discover -s pychat/tests`
- Phase 2 will add more robust user management and session handling
- Phase 3 will implement the GUI interface
