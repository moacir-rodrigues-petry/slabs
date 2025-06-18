"""
Graphical user interface for PyChat
Implementation for Phase 3
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox, filedialog
import threading
import time
import datetime
import queue
from typing import Optional, List, Dict, Any
import os
import sys
try:
    import emoji
except ImportError:
    # Graceful fallback if emoji package is not installed
    def emojize(text, **kwargs):
        return text
    emoji = type('DummyEmoji', (), {'emojize': emojize})

from pychat.common.message import Message
from pychat.interfaces.common import ChatInterface
from pychat.core.user import User
from pychat.common.utils import format_timestamp, truncate_text

# Define some colors and styles
COLORS = {
    "primary": "#3498db",      # Blue
    "secondary": "#2ecc71",    # Green
    "accent": "#e74c3c",       # Red
    "light": "#ecf0f1",        # Light gray
    "dark": "#34495e",         # Dark blue-gray
    "text": "#2c3e50",         # Very dark blue-gray
    "text_light": "#7f8c8d"    # Medium gray
}

# Common emoji shortcuts
EMOJI_MAP = {
    ":)": ":slightly_smiling_face:",
    ":(": ":disappointed_face:",
    ":D": ":grinning_face_with_big_eyes:",
    ";)": ":winking_face:",
    ":p": ":face_with_tongue:",
    "<3": ":red_heart:",
    ":/": ":confused_face:",
    ":o": ":face_with_open_mouth:",
}


class ChatWindow(tk.Tk):
    """Main chat window class"""
    
    def __init__(self, interface: 'GUIInterface'):
        """Initialize the chat window"""
        super().__init__()
        
        self.interface = interface
        self.msg_queue = queue.Queue()
        self.is_running = True
        
        # Configure the window
        self.title("PyChat")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Set icon
        # self.iconbitmap("icon.ico")  # Uncomment and add icon file if available
        
        # Configure styles
        self.configure_styles()
        
        # Create the main layout
        self.create_layout()
        
        # Start the message checking thread
        self.check_messages_thread = threading.Thread(
            target=self._check_messages_loop,
            daemon=True
        )
        self.check_messages_thread.start()
        
        # Bind closing event
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Auto-scroll settings
        self.auto_scroll = True
        
        # Update user list
        self.update_user_list()
        
        # Schedule periodic updates
        self.after(5000, self.periodic_updates)
    
    def configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.configure("TFrame", background=COLORS["light"])
        style.configure("TButton", 
                       background=COLORS["primary"], 
                       foreground="white",
                       padding=5)
        style.configure("Accent.TButton", 
                       background=COLORS["accent"], 
                       foreground="white",
                       padding=5)
        style.configure("TLabel", 
                       background=COLORS["light"], 
                       foreground=COLORS["text"],
                       padding=5)
        style.configure("Status.TLabel", 
                       background=COLORS["light"], 
                       foreground=COLORS["text_light"],
                       font=("Arial", 9, "italic"),
                       padding=2)
        style.configure("User.TLabel", 
                       background=COLORS["light"], 
                       foreground=COLORS["primary"],
                       padding=5)
        style.configure("Header.TLabel", 
                       background=COLORS["dark"], 
                       foreground="white",
                       font=("Arial", 12, "bold"),
                       padding=8)
    
    def create_layout(self):
        """Create the main window layout"""
        # Main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top panel - user info and status
        self.top_panel = ttk.Frame(self.main_container)
        self.top_panel.pack(fill=tk.X, padx=5, pady=5)
        
        self.user_label = ttk.Label(
            self.top_panel, 
            text=f"Logged in as: {self.interface.user.display_name if self.interface.user else 'Guest'}"
        )
        self.user_label.pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Online")
        self.status_label = ttk.Label(
            self.top_panel, 
            textvariable=self.status_var,
            style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.logout_button = ttk.Button(
            self.top_panel,
            text="Logout",
            command=self.on_logout,
            style="Accent.TButton"
        )
        self.logout_button.pack(side=tk.RIGHT)
        
        # Create a paned window for the main content
        self.paned_window = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left panel - chat display and input
        self.chat_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(self.chat_panel, weight=3)
        
        # Chat display header
        self.chat_header = ttk.Label(
            self.chat_panel, 
            text="Chat Messages",
            style="Header.TLabel"
        )
        self.chat_header.pack(fill=tk.X)
        
        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_panel,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="white",
            fg=COLORS["text"]
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chat_display.config(state=tk.DISABLED)
        
        # Toggle auto-scroll button
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.autoscroll_check = ttk.Checkbutton(
            self.chat_panel,
            text="Auto-scroll",
            variable=self.autoscroll_var,
            command=self.toggle_autoscroll
        )
        self.autoscroll_check.pack(anchor=tk.E, pady=(0, 5))
        
        # Message entry area
        self.message_frame = ttk.Frame(self.chat_panel)
        self.message_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.emoji_button = ttk.Button(
            self.message_frame,
            text="😊",
            width=3,
            command=self.show_emoji_picker
        )
        self.emoji_button.pack(side=tk.LEFT)
        
        self.message_entry = ttk.Entry(self.message_frame, font=("Arial", 10))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind("<Return>", self.on_send)
        
        self.send_button = ttk.Button(
            self.message_frame,
            text="Send",
            command=self.on_send
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Recipient selector
        self.recipient_frame = ttk.Frame(self.chat_panel)
        self.recipient_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.recipient_frame, text="To:").pack(side=tk.LEFT)
        
        self.recipient_var = tk.StringVar(value="Everyone")
        self.recipient_combo = ttk.Combobox(
            self.recipient_frame, 
            textvariable=self.recipient_var,
            state="readonly",
            width=20
        )
        self.recipient_combo.pack(side=tk.LEFT, padx=5)
        self.recipient_combo['values'] = ['Everyone']
        
        # Right panel - users and features
        self.users_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(self.users_panel, weight=1)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.users_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Users tab
        self.users_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.users_tab, text="Users")
        
        ttk.Label(self.users_tab, text="Online Users", style="Header.TLabel").pack(fill=tk.X)
        
        # User listbox
        self.users_frame = ttk.Frame(self.users_tab)
        self.users_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.users_listbox = tk.Listbox(
            self.users_frame,
            bg="white",
            fg=COLORS["text"],
            font=("Arial", 10),
            selectbackground=COLORS["primary"],
            selectforeground="white"
        )
        self.users_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.users_listbox.bind("<Double-1>", self.on_user_select)
        
        users_scrollbar = ttk.Scrollbar(self.users_frame, orient=tk.VERTICAL, command=self.users_listbox.yview)
        users_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.users_listbox.config(yscrollcommand=users_scrollbar.set)
        
        # User actions frame
        self.user_actions = ttk.Frame(self.users_tab)
        self.user_actions.pack(fill=tk.X, padx=5, pady=5)
        
        self.view_profile_btn = ttk.Button(
            self.user_actions,
            text="View Profile",
            command=self.on_view_profile
        )
        self.view_profile_btn.pack(fill=tk.X, pady=2)
        
        self.private_msg_btn = ttk.Button(
            self.user_actions,
            text="Private Message",
            command=self.on_private_message
        )
        self.private_msg_btn.pack(fill=tk.X, pady=2)
        
        # History tab
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="History")
        
        ttk.Label(self.history_tab, text="Message History", style="Header.TLabel").pack(fill=tk.X)
        
        # History controls
        self.history_controls = ttk.Frame(self.history_tab)
        self.history_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.history_controls, text="Messages:").pack(side=tk.LEFT)
        self.history_limit_var = tk.StringVar(value="20")
        self.history_limit = ttk.Spinbox(
            self.history_controls,
            from_=10,
            to=100,
            increment=10,
            textvariable=self.history_limit_var,
            width=5
        )
        self.history_limit.pack(side=tk.LEFT, padx=5)
        
        self.load_history_btn = ttk.Button(
            self.history_controls,
            text="Load History",
            command=self.on_load_history
        )
        self.load_history_btn.pack(side=tk.LEFT, padx=5)
        
        # History display
        self.history_display = scrolledtext.ScrolledText(
            self.history_tab,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="white",
            fg=COLORS["text"]
        )
        self.history_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_display.config(state=tk.DISABLED)
        
        # Bottom status bar
        self.status_bar = ttk.Label(
            self.main_container, 
            text="Ready",
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
    
    def _check_messages_loop(self):
        """Background thread to check for new messages"""
        while self.is_running:
            try:
                # Check if there are any messages in the queue
                if not self.msg_queue.empty():
                    message = self.msg_queue.get()
                    self.display_message(message)
                    self.msg_queue.task_done()
                
                # Sleep to avoid CPU overuse
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in message checking thread: {e}")
    
    def periodic_updates(self):
        """Perform periodic updates"""
        if self.is_running:
            # Update user list
            self.update_user_list()
            
            # Schedule the next update
            self.after(10000, self.periodic_updates)
    
    def update_user_list(self):
        """Update the list of active users"""
        users = self.interface.get_active_users()
        
        # Clear the current list
        self.users_listbox.delete(0, tk.END)
        
        # Update the combo box for recipients
        recipient_options = ['Everyone']
        
        # Add users to the list
        for user in users:
            display_text = f"{user.display_name} ({user.status})"
            if user.username == self.interface.username:
                display_text += " (You)"
            else:
                recipient_options.append(user.display_name)
            
            self.users_listbox.insert(tk.END, display_text)
        
        # Update the recipient dropdown
        self.recipient_combo['values'] = recipient_options
    
    def display_message(self, message: Message):
        """
        Display a message in the chat window
        
        Args:
            message: The message to display
        """
        # Enable editing
        self.chat_display.config(state=tk.NORMAL)
        
        # Format timestamp
        time_str = format_timestamp(message.timestamp)
        
        # Format and insert the message
        if message.recipient and message.recipient != "Everyone" and message.recipient != self.interface.username:
            # Private message sent by current user
            self.chat_display.insert(tk.END, f"[{time_str}] ", "timestamp")
            self.chat_display.insert(tk.END, f"You → {message.recipient}: ", "private")
            self.chat_display.insert(tk.END, f"{message.content}\n", "message")
        elif message.recipient and message.recipient == self.interface.username:
            # Private message received by current user
            self.chat_display.insert(tk.END, f"[{time_str}] ", "timestamp")
            self.chat_display.insert(tk.END, f"{message.sender} → You: ", "private")
            self.chat_display.insert(tk.END, f"{message.content}\n", "message")
        else:
            # Broadcast message
            self.chat_display.insert(tk.END, f"[{time_str}] ", "timestamp")
            
            if message.sender == self.interface.username:
                self.chat_display.insert(tk.END, "You: ", "self")
            else:
                self.chat_display.insert(tk.END, f"{message.sender}: ", "sender")
            
            self.chat_display.insert(tk.END, f"{message.content}\n", "message")
        
        # Configure tags
        self.chat_display.tag_configure("timestamp", foreground=COLORS["text_light"], font=("Arial", 9, "italic"))
        self.chat_display.tag_configure("sender", foreground=COLORS["primary"], font=("Arial", 10, "bold"))
        self.chat_display.tag_configure("self", foreground=COLORS["secondary"], font=("Arial", 10, "bold"))
        self.chat_display.tag_configure("private", foreground=COLORS["accent"], font=("Arial", 10, "bold"))
        self.chat_display.tag_configure("message", foreground=COLORS["text"], font=("Arial", 10))
        
        # Disable editing
        self.chat_display.config(state=tk.DISABLED)
        
        # Auto-scroll to the bottom if enabled
        if self.autoscroll_var.get():
            self.chat_display.see(tk.END)
    
    def display_system_message(self, message: str):
        """
        Display a system message
        
        Args:
            message: The message to display
        """
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"[System] {message}\n", "system")
        self.chat_display.tag_configure("system", foreground="gray", font=("Arial", 9, "italic"))
        self.chat_display.config(state=tk.DISABLED)
        
        if self.autoscroll_var.get():
            self.chat_display.see(tk.END)
    
    def on_send(self, event=None):
        """Send a message"""
        content = self.message_entry.get().strip()
        if not content:
            return
        
        # Process emoji shortcuts
        for shortcut, emoji_code in EMOJI_MAP.items():
            content = content.replace(shortcut, emoji_code)
        
        # Convert emoji codes to actual emojis
        content = emoji.emojize(content, language='alias')
        
        # Get recipient
        recipient = None
        if self.recipient_var.get() != "Everyone":
            # Find the username corresponding to the display name
            for user in self.interface.get_active_users():
                if user.display_name == self.recipient_var.get():
                    recipient = user.username
                    break
        
        # Send the message
        success = self.interface.send_message(content, recipient)
        
        if success:
            # Clear the message entry
            self.message_entry.delete(0, tk.END)
            self.message_entry.focus()
        else:
            messagebox.showerror("Error", "Failed to send message")
    
    def toggle_autoscroll(self):
        """Toggle auto-scrolling"""
        self.auto_scroll = self.autoscroll_var.get()
    
    def on_view_profile(self):
        """View the selected user's profile"""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a user first")
            return
        
        selected_text = self.users_listbox.get(selection[0])
        username = selected_text.split(" (")[0]
        
        # Find the username
        target_username = None
        for user in self.interface.get_active_users():
            if user.display_name == username:
                target_username = user.username
                break
        
        if not target_username:
            messagebox.showerror("Error", "User not found")
            return
        
        # Get the profile
        profile = self.interface.get_user_profile(target_username)
        if not profile:
            messagebox.showerror("Error", "Could not retrieve user profile")
            return
        
        # Show profile in a dialog
        profile_window = tk.Toplevel(self)
        profile_window.title(f"Profile: {profile['display_name']}")
        profile_window.geometry("300x200")
        profile_window.resizable(False, False)
        
        ttk.Label(profile_window, text=f"Username: {profile['username']}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(profile_window, text=f"Display Name: {profile['display_name']}").pack(anchor=tk.W, padx=10, pady=5)
        
        if profile.get('email'):
            ttk.Label(profile_window, text=f"Email: {profile['email']}").pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Label(profile_window, text=f"Status: {profile['status']}").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(profile_window, text=f"Last Seen: {profile['last_seen']}").pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Button(profile_window, text="Close", command=profile_window.destroy).pack(pady=10)
    
    def on_private_message(self):
        """Start a private message with the selected user"""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a user first")
            return
        
        selected_text = self.users_listbox.get(selection[0])
        display_name = selected_text.split(" (")[0]
        
        # Set as recipient
        self.recipient_var.set(display_name)
        
        # Focus the message entry
        self.message_entry.focus()
    
    def on_user_select(self, event):
        """Handle user double-click"""
        self.on_private_message()
    
    def on_load_history(self):
        """Load and display message history"""
        try:
            limit = int(self.history_limit_var.get())
        except ValueError:
            limit = 20  # Default
        
        messages = self.interface.get_message_history(limit)
        
        # Clear the history display
        self.history_display.config(state=tk.NORMAL)
        self.history_display.delete(1.0, tk.END)
        
        if not messages:
            self.history_display.insert(tk.END, "No message history found.")
            self.history_display.config(state=tk.DISABLED)
            return
        
        # Display messages in the history tab
        for message in messages:
            time_str = format_timestamp(message.timestamp, include_date=True)
            
            if message.recipient and message.recipient != "Everyone":
                if message.sender == self.interface.username:
                    self.history_display.insert(tk.END, f"[{time_str}] ", "timestamp")
                    self.history_display.insert(tk.END, f"You → {message.recipient}: ", "private")
                    self.history_display.insert(tk.END, f"{message.content}\n", "message")
                elif message.recipient == self.interface.username:
                    self.history_display.insert(tk.END, f"[{time_str}] ", "timestamp")
                    self.history_display.insert(tk.END, f"{message.sender} → You: ", "private")
                    self.history_display.insert(tk.END, f"{message.content}\n", "message")
            else:
                self.history_display.insert(tk.END, f"[{time_str}] ", "timestamp")
                
                if message.sender == self.interface.username:
                    self.history_display.insert(tk.END, "You: ", "self")
                else:
                    self.history_display.insert(tk.END, f"{message.sender}: ", "sender")
                
                self.history_display.insert(tk.END, f"{message.content}\n", "message")
        
        # Configure tags
        self.history_display.tag_configure("timestamp", foreground=COLORS["text_light"], font=("Arial", 9, "italic"))
        self.history_display.tag_configure("sender", foreground=COLORS["primary"], font=("Arial", 10, "bold"))
        self.history_display.tag_configure("self", foreground=COLORS["secondary"], font=("Arial", 10, "bold"))
        self.history_display.tag_configure("private", foreground=COLORS["accent"], font=("Arial", 10, "bold"))
        self.history_display.tag_configure("message", foreground=COLORS["text"], font=("Arial", 10))
        
        self.history_display.config(state=tk.DISABLED)
    
    def show_emoji_picker(self):
        """Show emoji picker dialog"""
        emoji_window = tk.Toplevel(self)
        emoji_window.title("Emoji Picker")
        emoji_window.geometry("300x200")
        
        # Common emojis
        emojis = [
            "😊", "😂", "😍", "👍", "👎", "❤️", "👋", "🎉",
            "😢", "😎", "🤔", "👀", "🙌", "🔥", "✅", "⭐"
        ]
        
        # Create a frame with buttons for each emoji
        emoji_frame = ttk.Frame(emoji_window)
        emoji_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        row, col = 0, 0
        for e in emojis:
            # Create a button for each emoji
            ttk.Button(
                emoji_frame,
                text=e,
                width=2,
                command=lambda emoji=e: self.insert_emoji(emoji, emoji_window)
            ).grid(row=row, column=col, padx=5, pady=5)
            
            col += 1
            if col > 3:  # 4 columns
                col = 0
                row += 1
        
        ttk.Button(
            emoji_window,
            text="Close",
            command=emoji_window.destroy
        ).pack(pady=10)
    
    def insert_emoji(self, emoji_char, window=None):
        """Insert an emoji at the cursor position"""
        self.message_entry.insert(tk.INSERT, emoji_char)
        self.message_entry.focus()
        
        if window:
            window.destroy()
    
    def on_logout(self):
        """Handle logout button click"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.interface.logout()
            self.destroy()
    
    def on_close(self):
        """Handle window close event"""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.is_running = False
            self.interface.shutdown()
            self.destroy()
            sys.exit(0)


class LoginWindow(tk.Tk):
    """Login window class"""
    
    def __init__(self, interface: 'GUIInterface'):
        """Initialize the login window"""
        super().__init__()
        
        self.interface = interface
        self.result = None
        
        # Configure the window
        self.title("PyChat Login")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Set icon
        # self.iconbitmap("icon.ico")  # Uncomment and add icon file if available
        
        # Create the login UI
        self.create_login_ui()
        
        # Center the window
        self.center_window()
    
    def create_login_ui(self):
        """Create the login user interface"""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Welcome to PyChat",
            font=("Arial", 16, "bold"),
            foreground=COLORS["primary"]
        )
        title_label.pack(pady=(0, 20))
        
        # Login form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Username
        ttk.Label(form_frame, text="Username:").pack(anchor=tk.W, pady=(0, 5))
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.pack(fill=tk.X, pady=(0, 10))
        self.username_entry.focus()
        
        # Password
        ttk.Label(form_frame, text="Password:").pack(anchor=tk.W, pady=(0, 5))
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.pack(fill=tk.X, pady=(0, 20))
        self.password_entry.bind("<Return>", self.on_login)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X)
        
        self.login_button = ttk.Button(
            button_frame,
            text="Login",
            command=self.on_login
        )
        self.login_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.register_button = ttk.Button(
            button_frame,
            text="Register",
            command=self.on_register
        )
        self.register_button.pack(side=tk.LEFT)
        
        # Status message
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            foreground=COLORS["accent"]
        )
        self.status_label.pack(pady=(10, 0))
    
    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_login(self, event=None):
        """Handle login button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username:
            self.status_var.set("Username cannot be empty")
            return
        
        if not password:
            self.status_var.set("Password cannot be empty")
            return
        
        self.status_var.set("Logging in...")
        self.update_idletasks()
        
        # Try to login
        if self.interface.login(username, password):
            self.result = "login_success"
            self.destroy()
        else:
            self.status_var.set("Login failed. Invalid username or password.")
    
    def on_register(self):
        """Handle register button click"""
        # Hide the login window
        self.withdraw()
        
        # Show the registration window
        register_window = RegistrationWindow(self, self.interface)
        register_window.transient(self)
        register_window.grab_set()
        self.wait_window(register_window)
        
        # Check the result
        if register_window.result == "register_success":
            self.result = "login_success"
            self.destroy()
        else:
            # Show the login window again
            self.deiconify()


class RegistrationWindow(tk.Toplevel):
    """Registration window class"""
    
    def __init__(self, parent, interface: 'GUIInterface'):
        """Initialize the registration window"""
        super().__init__(parent)
        
        self.interface = interface
        self.result = None
        
        # Configure the window
        self.title("PyChat Registration")
        self.geometry("400x350")
        self.resizable(False, False)
        
        # Create the registration UI
        self.create_registration_ui()
        
        # Center the window relative to parent
        self.center_window()
    
    def create_registration_ui(self):
        """Create the registration user interface"""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Register New Account",
            font=("Arial", 16, "bold"),
            foreground=COLORS["primary"]
        )
        title_label.pack(pady=(0, 20))
        
        # Registration form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Username
        ttk.Label(form_frame, text="Username:").pack(anchor=tk.W, pady=(0, 5))
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.pack(fill=tk.X, pady=(0, 10))
        self.username_entry.focus()
        
        # Display Name
        ttk.Label(form_frame, text="Display Name (optional):").pack(anchor=tk.W, pady=(0, 5))
        self.display_name_entry = ttk.Entry(form_frame, width=30)
        self.display_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Email
        ttk.Label(form_frame, text="Email (optional):").pack(anchor=tk.W, pady=(0, 5))
        self.email_entry = ttk.Entry(form_frame, width=30)
        self.email_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Password
        ttk.Label(form_frame, text="Password:").pack(anchor=tk.W, pady=(0, 5))
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Confirm Password
        ttk.Label(form_frame, text="Confirm Password:").pack(anchor=tk.W, pady=(0, 5))
        self.confirm_password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.confirm_password_entry.pack(fill=tk.X, pady=(0, 20))
        self.confirm_password_entry.bind("<Return>", self.on_register)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X)
        
        self.register_button = ttk.Button(
            button_frame,
            text="Register",
            command=self.on_register
        )
        self.register_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        )
        self.cancel_button.pack(side=tk.LEFT)
        
        # Status message
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            foreground=COLORS["accent"]
        )
        self.status_label.pack(pady=(10, 0))
    
    def center_window(self):
        """Center the window relative to the parent"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_register(self, event=None):
        """Handle register button click"""
        username = self.username_entry.get().strip()
        display_name = self.display_name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Validate input
        if not username:
            self.status_var.set("Username cannot be empty")
            return
        
        if not password:
            self.status_var.set("Password cannot be empty")
            return
        
        if password != confirm_password:
            self.status_var.set("Passwords do not match")
            return
        
        if not display_name:
            display_name = username
        
        self.status_var.set("Registering...")
        self.update_idletasks()
        
        # Try to register
        if self.interface.register(username, password, display_name, email):
            # Auto-login
            if self.interface.login(username, password):
                self.result = "register_success"
                self.destroy()
            else:
                self.status_var.set("Registration successful, but auto-login failed")
        else:
            self.status_var.set("Registration failed. Username may already be taken.")
    
    def on_cancel(self):
        """Handle cancel button click"""
        self.result = "cancelled"
        self.destroy()


class GUIInterface(ChatInterface):
    """
    Graphical user interface for PyChat
    Implementation for Phase 3
    """
    def __init__(self):
        """Initialize the GUI interface"""
        super().__init__()
        
        self.message_queue = queue.Queue()
        self.window = None
    
    def _receive_message(self, message: Message) -> None:
        """
        Handle received messages
        
        Args:
            message: The received message
        """
        if self.window:
            self.message_queue.put(message)
    
    def _show_login_window(self) -> bool:
        """
        Show the login window
        
        Returns:
            True if login successful, False otherwise
        """
        login_window = LoginWindow(self)
        login_window.mainloop()
        
        return login_window.result == "login_success"
    
    def run(self) -> None:
        """Run the GUI interface"""
        # Show login window first
        if not self._show_login_window():
            print("Login cancelled or failed")
            return
        
        # Create and show the main chat window
        self.window = ChatWindow(self)
        self.window.mainloop()


def main() -> None:
    """Main entry point for the GUI interface"""
    interface = GUIInterface()
    interface.run()


if __name__ == "__main__":
    main()
