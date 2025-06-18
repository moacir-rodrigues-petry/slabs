# Python Simple Chat Application (PyChat)

## Project Overview

PyChat is a simple, lightweight chat application built with Python 3. It allows users to communicate in real-time through a single-machine architecture. The application provides both a command-line interface and a graphical user interface for flexible usage.

## Features

- **Real-time messaging**: Users can send and receive messages instantly
- **User authentication**: Simple login system to identify users
- **Multiple clients**: Support for multiple concurrent connections
- **Private messaging**: Option to send messages to specific users
- **Chat history**: Messages are stored and can be viewed later
- **GUI and CLI interfaces**: Both graphical and command-line interfaces available

## Technical Design

### Architecture

The application uses a single-machine architecture with multiple modules running on the same system:

```
+----------------------------Single Machine-----------------------------+
|                                                                       |
|  +----------------+        +----------------+        +----------------+
|  |                |        |                |        |                |
|  |  User          | <----> |  Chat Core     | <----> |  User          |
|  |  Interface 1   |        |  Module        |        |  Interface 2   |
|  |  (GUI/CLI)     |        |  (In-memory)   |        |  (GUI/CLI)     |
|  |                |        |                |        |                |
|  +----------------+        +----------------+        +----------------+
|                                    ^                                  |
|                                    |                                  |
|                                    v                                  |
|                            +----------------+                         |
|                            |                |                         |
|                            |  Local Storage |                         |
|                            |  (SQLite/File) |                         |
|                            |                |                         |
|                            +----------------+                         |
|                                                                       |
+-----------------------------------------------------------------------+
```

### Components

1. **Chat Core Module**:

   - Central communication hub between interfaces
   - Manages user sessions and message routing
   - Handles message queuing and delivery
   - Runs as a local service or library

2. **User Interfaces**:

   - Multiple interface options (CLI or GUI)
   - Communicates with the Chat Core via function calls or local IPC
   - Can be launched independently from the same codebase

3. **Local Storage**:
   - Stores user profiles and message history
   - Implemented using SQLite for simplicity
   - Directly accessed by the Chat Core module

### Technologies

- **Python 3**: Core programming language
- **Multiprocessing/Threading**: For handling multiple user interfaces
- **Inter-process Communication**: For communication between modules
- **Tkinter/PyQt**: For GUI implementation
- **SQLite**: For local data storage
- **JSON/Pickle**: For message serialization

## Implementation Plan

### Phase 1: Core Functionality

- Implement the Chat Core module
- Create message handling and storage system
- Build a simple command-line interface

### Phase 2: User Management

- Add user profile management
- Implement session handling
- Add support for private messaging

### Phase 3: GUI and Enhancements

- Create a graphical user interface
- Add chat history browsing
- Implement additional features (file sharing, emojis, etc.)

## Project Structure

```
pychat/
├── core/
│   ├── chat_manager.py   # Main chat logic implementation
│   ├── storage.py        # Database/file storage handling
│   └── user.py           # User profile management
├── interfaces/
│   ├── cli_interface.py  # Command-line interface
│   ├── gui_interface.py  # Graphical user interface
│   └── common.py         # Shared interface code
├── common/
│   ├── message.py        # Message format and serialization
│   └── utils.py          # Utility functions
├── tests/                # Unit and integration tests
└── docs/                 # Documentation
```

## Development Setup

1. Clone the repository
2. Install required dependencies: `pip install -r requirements.txt`
3. Start the application:
   - CLI: `python -m pychat.interfaces.cli_interface`
   - GUI: `python -m pychat.interfaces.gui_interface`

The Chat Core module starts automatically when an interface is launched.

## Future Ideas

- **End-to-end encryption**: Add secure messaging
- **Group chat**: Support for creating and managing group conversations
- **Voice/Video chat**: Integrate multimedia communication
- **Cross-platform support**: Mobile and web clients
- **Chatbots**: Automated responses and assistant functionality
- **Message formatting**: Support for rich text, markdown, etc.
- **Notifications**: Desktop or mobile notifications for new messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
