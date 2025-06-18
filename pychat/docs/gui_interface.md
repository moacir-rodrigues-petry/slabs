# PyChat GUI Interface

This document provides detailed information about the PyChat GUI interface implemented in Phase 3.

## Overview

The PyChat GUI interface provides a user-friendly way to interact with the PyChat application. It includes the following features:

- User authentication (login/registration)
- Real-time messaging
- Private messaging
- User status updates
- Chat history browsing
- Emoji support
- User profile viewing

## Features

### Authentication

The GUI starts with a login window where users can:
- Login with existing credentials
- Register a new account with username, display name, email, and password

### Main Chat Window

The main chat interface includes:

- Chat display area showing messages with formatting for different message types
- Message input area with emoji support
- User list showing online users and their status
- Tab-based interface for accessing different features

### Chat History

A dedicated tab for browsing chat history with:
- Configurable number of messages to display
- Formatted message display with timestamps
- Clear distinction between broadcast and private messages

### User Management

User-related features include:
- Viewing user profiles
- Initiating private conversations
- Updating personal status
- Seeing which users are currently online

### Emoji Support

The interface includes emoji support with:
- Emoji picker dialog
- Shortcut conversion (e.g., ":)" to 😊)
- Emoji codes support

## Implementation Details

The GUI is implemented using Python's Tkinter library, which is part of the standard library, making it easy to run on most platforms without additional dependencies.

Key components:
- `ChatWindow`: The main window containing the chat interface
- `LoginWindow`: Handles user authentication
- `RegistrationWindow`: Manages new user registration
- `GUIInterface`: Bridges between the interface and core components

## Running the GUI

To run the PyChat GUI:

```bash
# Method 1: Use the run_gui.py script
./run_gui.py

# Method 2: Run the module directly
python -m pychat.interfaces.gui_interface

# Method 3: Use the console script (if installed via pip)
pychat-gui
```
