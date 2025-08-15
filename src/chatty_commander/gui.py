#!/usr/bin/env python3
"""
ChattyCommander Desktop GUI

A desktop application for configuring and managing ChattyCommander.
Provides a user-friendly interface for setting up commands, states, and models.
"""

import json
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Check for DISPLAY environment variable. If missing, print a warning and assign a dummy fallback.
if 'DISPLAY' not in os.environ or not os.environ['DISPLAY'].strip():
    print(
        "Warning: DISPLAY environment variable not set. Running in headless mode. Using dummy display ':0'."
    )
    os.environ['DISPLAY'] = ':0'

from chatty_commander.app.config import Config


class ChattyCommanderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ChattyCommander Configuration")
        self.root.geometry("800x600")

        # Initialize configuration
        self.config_file = "config.json"
        self.config = None
        self.load_config()

        # Create main interface
        self.create_widgets()

        # Status variables
        self.service_running = False

    def load_config(self):
        """Load configuration from file or create default."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    config_data = json.load(f)
                self.config = Config(**config_data)
            else:
                self.config = Config()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            self.config = Config()

    def save_config(self):
        """Save current configuration to file."""
        try:
            config_dict = {
                'model_paths': self.config.model_paths,
                'api_endpoints': self.config.api_endpoints,
                'model_actions': self.config.model_actions,
                'state_models': self.config.state_models,
                'audio_settings': self.config.audio_settings,
                'debug_settings': self.config.debug_settings,
                'default_state': self.config.default_state,
                'inference_framework': self.config.inference_framework,
            }

            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)

            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def create_widgets(self):
        """Create the main GUI widgets."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_commands_tab()
        self.create_states_tab()
        self.create_models_tab()
        self.create_audio_tab()
        self.create_service_tab()

        # Create bottom frame for buttons
        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.pack(fill=tk.X, padx=10, pady=5)

        # Save and Load buttons
        ttk.Button(self.bottom_frame, text="Save Config", command=self.save_config).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(self.bottom_frame, text="Load Config", command=self.load_config_file).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(self.bottom_frame, text="Reset to Defaults", command=self.reset_config).pack(
            side=tk.LEFT, padx=5
        )

    def create_commands_tab(self):
        """Create the commands configuration tab."""
        self.commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.commands_frame, text="Commands")

        # Create sub-notebook for command types
        cmd_notebook = ttk.Notebook(self.commands_frame)
        cmd_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # URL Commands
        self.url_frame = ttk.Frame(cmd_notebook)
        cmd_notebook.add(self.url_frame, text="URL Commands")
        self.create_url_commands_section()

        # Keypress Commands
        self.keypress_frame = ttk.Frame(cmd_notebook)
        cmd_notebook.add(self.keypress_frame, text="Keypress Commands")
        self.create_keypress_commands_section()

        # System Commands
        self.system_frame = ttk.Frame(cmd_notebook)
        cmd_notebook.add(self.system_frame, text="System Commands")
        self.create_system_commands_section()

    def create_url_commands_section(self):
        """Create URL commands configuration section."""
        ttk.Label(self.url_frame, text="URL Commands", font=('Arial', 12, 'bold')).pack(pady=5)

        # Frame for URL commands list
        list_frame = ttk.Frame(self.url_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for URL commands
        self.url_tree = ttk.Treeview(list_frame, columns=('URL',), show='tree headings')
        self.url_tree.heading('#0', text='Command')
        self.url_tree.heading('URL', text='URL')
        self.url_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        url_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.url_tree.yview)
        url_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.url_tree.configure(yscrollcommand=url_scroll.set)

        # Buttons frame
        url_btn_frame = ttk.Frame(self.url_frame)
        url_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(url_btn_frame, text="Add URL Command", command=self.add_url_command).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(url_btn_frame, text="Edit Selected", command=self.edit_url_command).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(url_btn_frame, text="Delete Selected", command=self.delete_url_command).pack(
            side=tk.LEFT, padx=5
        )

        self.populate_url_commands()

    def create_keypress_commands_section(self):
        """Create keypress commands configuration section."""
        ttk.Label(self.keypress_frame, text="Keypress Commands", font=('Arial', 12, 'bold')).pack(
            pady=5
        )

        # Frame for keypress commands list
        list_frame = ttk.Frame(self.keypress_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for keypress commands
        self.keypress_tree = ttk.Treeview(list_frame, columns=('Keys',), show='tree headings')
        self.keypress_tree.heading('#0', text='Command')
        self.keypress_tree.heading('Keys', text='Key Combination')
        self.keypress_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        keypress_scroll = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.keypress_tree.yview
        )
        keypress_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.keypress_tree.configure(yscrollcommand=keypress_scroll.set)

        # Buttons frame
        keypress_btn_frame = ttk.Frame(self.keypress_frame)
        keypress_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            keypress_btn_frame, text="Add Keypress Command", command=self.add_keypress_command
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            keypress_btn_frame, text="Edit Selected", command=self.edit_keypress_command
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            keypress_btn_frame, text="Delete Selected", command=self.delete_keypress_command
        ).pack(side=tk.LEFT, padx=5)

        self.populate_keypress_commands()

    def create_system_commands_section(self):
        """Create system commands configuration section."""
        ttk.Label(self.system_frame, text="System Commands", font=('Arial', 12, 'bold')).pack(
            pady=5
        )

        # Frame for system commands list
        list_frame = ttk.Frame(self.system_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for system commands
        self.system_tree = ttk.Treeview(list_frame, columns=('Command',), show='tree headings')
        self.system_tree.heading('#0', text='Name')
        self.system_tree.heading('Command', text='System Command')
        self.system_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        system_scroll = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.system_tree.yview
        )
        system_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.system_tree.configure(yscrollcommand=system_scroll.set)

        # Buttons frame
        system_btn_frame = ttk.Frame(self.system_frame)
        system_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            system_btn_frame, text="Add System Command", command=self.add_system_command
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(system_btn_frame, text="Edit Selected", command=self.edit_system_command).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            system_btn_frame, text="Delete Selected", command=self.delete_system_command
        ).pack(side=tk.LEFT, padx=5)

        self.populate_system_commands()

    def create_states_tab(self):
        """Create the states configuration tab."""
        self.states_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.states_frame, text="States")

        ttk.Label(self.states_frame, text="State Configuration", font=('Arial', 12, 'bold')).pack(
            pady=5
        )

        # Default state selection
        default_frame = ttk.Frame(self.states_frame)
        default_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(default_frame, text="Default State:").pack(side=tk.LEFT, padx=5)
        self.default_state_var = tk.StringVar(value=self.config.default_state)
        default_combo = ttk.Combobox(
            default_frame,
            textvariable=self.default_state_var,
            values=['idle', 'chatty', 'computer'],
            state='readonly',
        )
        default_combo.pack(side=tk.LEFT, padx=5)

        # State models configuration
        ttk.Label(self.states_frame, text="State Models", font=('Arial', 10, 'bold')).pack(
            pady=(20, 5)
        )

        # Frame for state models
        models_frame = ttk.Frame(self.states_frame)
        models_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for state models
        self.state_models_tree = ttk.Treeview(
            models_frame, columns=('Models',), show='tree headings'
        )
        self.state_models_tree.heading('#0', text='State')
        self.state_models_tree.heading('Models', text='Model Paths')
        self.state_models_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        models_scroll = ttk.Scrollbar(
            models_frame, orient=tk.VERTICAL, command=self.state_models_tree.yview
        )
        models_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.state_models_tree.configure(yscrollcommand=models_scroll.set)

        # Buttons frame
        models_btn_frame = ttk.Frame(self.states_frame)
        models_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(models_btn_frame, text="Edit State Models", command=self.edit_state_models).pack(
            side=tk.LEFT, padx=5
        )

        self.populate_state_models()

    def create_models_tab(self):
        """Create the models configuration tab."""
        self.models_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.models_frame, text="Models")

        ttk.Label(self.models_frame, text="Model Configuration", font=('Arial', 12, 'bold')).pack(
            pady=5
        )

        # Model paths
        paths_frame = ttk.LabelFrame(self.models_frame, text="Model Paths")
        paths_frame.pack(fill=tk.X, padx=5, pady=5)

        # Chatty models path
        chatty_frame = ttk.Frame(paths_frame)
        chatty_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(chatty_frame, text="Chatty Models:").pack(side=tk.LEFT)
        self.chatty_path_var = tk.StringVar(value=self.config.model_paths.get('chatty', ''))
        ttk.Entry(chatty_frame, textvariable=self.chatty_path_var, width=40).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            chatty_frame, text="Browse", command=lambda: self.browse_directory(self.chatty_path_var)
        ).pack(side=tk.LEFT)

        # Computer models path
        computer_frame = ttk.Frame(paths_frame)
        computer_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(computer_frame, text="Computer Models:").pack(side=tk.LEFT)
        self.computer_path_var = tk.StringVar(value=self.config.model_paths.get('computer', ''))
        ttk.Entry(computer_frame, textvariable=self.computer_path_var, width=40).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            computer_frame,
            text="Browse",
            command=lambda: self.browse_directory(self.computer_path_var),
        ).pack(side=tk.LEFT)

        # Idle models path
        idle_frame = ttk.Frame(paths_frame)
        idle_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(idle_frame, text="Idle Models:").pack(side=tk.LEFT)
        self.idle_path_var = tk.StringVar(value=self.config.model_paths.get('idle', ''))
        ttk.Entry(idle_frame, textvariable=self.idle_path_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            idle_frame, text="Browse", command=lambda: self.browse_directory(self.idle_path_var)
        ).pack(side=tk.LEFT)

        # Inference framework
        framework_frame = ttk.LabelFrame(self.models_frame, text="Inference Framework")
        framework_frame.pack(fill=tk.X, padx=5, pady=5)

        self.framework_var = tk.StringVar(value=self.config.inference_framework)
        ttk.Radiobutton(
            framework_frame, text="ONNX", variable=self.framework_var, value="onnx"
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(
            framework_frame, text="OpenVINO", variable=self.framework_var, value="openvino"
        ).pack(side=tk.LEFT, padx=10)

    def create_audio_tab(self):
        """Create the audio configuration tab."""
        self.audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.audio_frame, text="Audio")

        ttk.Label(self.audio_frame, text="Audio Settings", font=('Arial', 12, 'bold')).pack(pady=5)

        # Audio settings frame
        settings_frame = ttk.LabelFrame(self.audio_frame, text="Recording Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)

        # Sample rate
        rate_frame = ttk.Frame(settings_frame)
        rate_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(rate_frame, text="Sample Rate:").pack(side=tk.LEFT)
        self.sample_rate_var = tk.StringVar(
            value=str(self.config.audio_settings.get('sample_rate', 16000))
        )
        ttk.Entry(rate_frame, textvariable=self.sample_rate_var, width=10).pack(
            side=tk.LEFT, padx=5
        )

        # Channels
        channels_frame = ttk.Frame(settings_frame)
        channels_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(channels_frame, text="Channels:").pack(side=tk.LEFT)
        self.channels_var = tk.StringVar(value=str(self.config.audio_settings.get('channels', 1)))
        ttk.Entry(channels_frame, textvariable=self.channels_var, width=10).pack(
            side=tk.LEFT, padx=5
        )

        # Chunk size
        chunk_frame = ttk.Frame(settings_frame)
        chunk_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(chunk_frame, text="Chunk Size:").pack(side=tk.LEFT)
        self.chunk_size_var = tk.StringVar(
            value=str(self.config.audio_settings.get('chunk_size', 1024))
        )
        ttk.Entry(chunk_frame, textvariable=self.chunk_size_var, width=10).pack(
            side=tk.LEFT, padx=5
        )

    def create_service_tab(self):
        """Create the service control tab."""
        self.service_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.service_frame, text="Service")

        ttk.Label(self.service_frame, text="Service Control", font=('Arial', 12, 'bold')).pack(
            pady=5
        )

        # Service status
        status_frame = ttk.LabelFrame(self.service_frame, text="Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_label = ttk.Label(
            status_frame, text="Service Status: Stopped", font=('Arial', 10)
        )
        self.status_label.pack(pady=10)

        # Service controls
        controls_frame = ttk.Frame(self.service_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_btn = ttk.Button(
            controls_frame, text="Start Service", command=self.start_service
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            controls_frame, text="Stop Service", command=self.stop_service, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(controls_frame, text="Test Configuration", command=self.test_config).pack(
            side=tk.LEFT, padx=5
        )

        # System settings
        system_frame = ttk.LabelFrame(self.service_frame, text="System Settings")
        system_frame.pack(fill=tk.X, padx=5, pady=5)

        # Start on boot setting
        boot_frame = ttk.Frame(system_frame)
        boot_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_on_boot_var = tk.BooleanVar(value=getattr(self.config, 'start_on_boot', False))
        ttk.Checkbutton(
            boot_frame,
            text="Start on boot",
            variable=self.start_on_boot_var,
            command=self.toggle_start_on_boot,
        ).pack(side=tk.LEFT)

        # Update checking setting
        update_frame = ttk.Frame(system_frame)
        update_frame.pack(fill=tk.X, padx=5, pady=5)

        self.check_updates_var = tk.BooleanVar(
            value=getattr(self.config, 'check_for_updates', True)
        )
        ttk.Checkbutton(
            update_frame,
            text="Check for updates automatically",
            variable=self.check_updates_var,
            command=self.toggle_update_checking,
        ).pack(side=tk.LEFT)

        ttk.Button(update_frame, text="Check Now", command=self.check_updates_now).pack(
            side=tk.RIGHT, padx=5
        )

        # Log output
        log_frame = ttk.LabelFrame(self.service_frame, text="Service Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # Command management methods
    def populate_url_commands(self):
        """Populate the URL commands tree."""
        for item in self.url_tree.get_children():
            self.url_tree.delete(item)

        url_commands = getattr(self.config, 'url_commands', {})
        for cmd, url in url_commands.items():
            self.url_tree.insert('', 'end', text=cmd, values=(url,))

    def populate_keypress_commands(self):
        """Populate the keypress commands tree."""
        for item in self.keypress_tree.get_children():
            self.keypress_tree.delete(item)

        keypress_commands = getattr(self.config, 'keypress_commands', {})
        for cmd, keys in keypress_commands.items():
            key_str = '+'.join(keys) if isinstance(keys, list) else str(keys)
            self.keypress_tree.insert('', 'end', text=cmd, values=(key_str,))

    def populate_system_commands(self):
        """Populate the system commands tree."""
        for item in self.system_tree.get_children():
            self.system_tree.delete(item)

        system_commands = getattr(self.config, 'system_commands', {})
        for cmd, command in system_commands.items():
            self.system_tree.insert('', 'end', text=cmd, values=(command,))

    def populate_state_models(self):
        """Populate the state models tree."""
        for item in self.state_models_tree.get_children():
            self.state_models_tree.delete(item)

        for state, models in self.config.state_models.items():
            models_str = ', '.join(models) if isinstance(models, list) else str(models)
            self.state_models_tree.insert('', 'end', text=state, values=(models_str,))

    def add_url_command(self):
        """Add a new URL command."""
        dialog = CommandDialog(self.root, "Add URL Command", "URL")
        if dialog.result:
            name, value = dialog.result
            if not hasattr(self.config, 'url_commands'):
                self.config.url_commands = {}
            self.config.url_commands[name] = value
            self.populate_url_commands()

    def add_keypress_command(self):
        """Add a new keypress command."""
        dialog = CommandDialog(self.root, "Add Keypress Command", "Key Combination (e.g., ctrl+c)")
        if dialog.result:
            name, value = dialog.result
            if not hasattr(self.config, 'keypress_commands'):
                self.config.keypress_commands = {}
            # Convert key combination string to list
            keys = [key.strip() for key in value.split('+')]
            self.config.keypress_commands[name] = keys
            self.populate_keypress_commands()

    def add_system_command(self):
        """Add a new system command."""
        dialog = CommandDialog(self.root, "Add System Command", "System Command")
        if dialog.result:
            name, value = dialog.result
            if not hasattr(self.config, 'system_commands'):
                self.config.system_commands = {}
            self.config.system_commands[name] = value
            self.populate_system_commands()

    def edit_url_command(self):
        """Edit selected URL command."""
        selection = self.url_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to edit.")
            return

        item = selection[0]
        name = self.url_tree.item(item, 'text')
        url = self.url_tree.item(item, 'values')[0]

        dialog = CommandDialog(self.root, "Edit URL Command", "URL", name, url)
        if dialog.result:
            new_name, new_url = dialog.result
            if hasattr(self.config, 'url_commands'):
                if new_name != name:
                    del self.config.url_commands[name]
                self.config.url_commands[new_name] = new_url
                self.populate_url_commands()

    def delete_url_command(self):
        """Delete selected URL command."""
        selection = self.url_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to delete.")
            return

        item = selection[0]
        name = self.url_tree.item(item, 'text')

        if messagebox.askyesno("Confirm", f"Delete command '{name}'?"):
            if hasattr(self.config, 'url_commands') and name in self.config.url_commands:
                del self.config.url_commands[name]
                self.populate_url_commands()

    def edit_keypress_command(self):
        """Edit selected keypress command."""
        selection = self.keypress_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to edit.")
            return

        item = selection[0]
        name = self.keypress_tree.item(item, 'text')
        keys = self.keypress_tree.item(item, 'values')[0]

        dialog = CommandDialog(self.root, "Edit Keypress Command", "Key Combination", name, keys)
        if dialog.result:
            new_name, new_keys = dialog.result
            if hasattr(self.config, 'keypress_commands'):
                if new_name != name:
                    del self.config.keypress_commands[name]
                key_list = [key.strip() for key in new_keys.split('+')]
                self.config.keypress_commands[new_name] = key_list
                self.populate_keypress_commands()

    def delete_keypress_command(self):
        """Delete selected keypress command."""
        selection = self.keypress_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to delete.")
            return

        item = selection[0]
        name = self.keypress_tree.item(item, 'text')

        if messagebox.askyesno("Confirm", f"Delete command '{name}'?"):
            if hasattr(self.config, 'keypress_commands') and name in self.config.keypress_commands:
                del self.config.keypress_commands[name]
                self.populate_keypress_commands()

    def edit_system_command(self):
        """Edit selected system command."""
        selection = self.system_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to edit.")
            return

        item = selection[0]
        name = self.system_tree.item(item, 'text')
        command = self.system_tree.item(item, 'values')[0]

        dialog = CommandDialog(self.root, "Edit System Command", "System Command", name, command)
        if dialog.result:
            new_name, new_command = dialog.result
            if hasattr(self.config, 'system_commands'):
                if new_name != name:
                    del self.config.system_commands[name]
                self.config.system_commands[new_name] = new_command
                self.populate_system_commands()

    def delete_system_command(self):
        """Delete selected system command."""
        selection = self.system_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a command to delete.")
            return

        item = selection[0]
        name = self.system_tree.item(item, 'text')

        if messagebox.askyesno("Confirm", f"Delete command '{name}'?"):
            if hasattr(self.config, 'system_commands') and name in self.config.system_commands:
                del self.config.system_commands[name]
                self.populate_system_commands()

    def edit_state_models(self):
        """Edit state models configuration."""
        dialog = StateModelsDialog(self.root, self.config.state_models)
        if dialog.result:
            self.config.state_models = dialog.result
            self.populate_state_models()

    def browse_directory(self, var):
        """Browse for directory and set variable."""
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)

    def load_config_file(self):
        """Load configuration from file dialog."""
        filename = filedialog.askopenfilename(
            title="Load Configuration", filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.config_file = filename
            self.load_config()
            self.refresh_all_tabs()

    def reset_config(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno("Confirm", "Reset all configuration to defaults?"):
            self.config = Config()
            self.refresh_all_tabs()

    def refresh_all_tabs(self):
        """Refresh all tab contents with current config."""
        self.populate_url_commands()
        self.populate_keypress_commands()
        self.populate_system_commands()
        self.populate_state_models()

        # Update variables
        self.default_state_var.set(self.config.default_state)
        self.chatty_path_var.set(self.config.model_paths.get('chatty', ''))
        self.computer_path_var.set(self.config.model_paths.get('computer', ''))
        self.idle_path_var.set(self.config.model_paths.get('idle', ''))
        self.framework_var.set(self.config.inference_framework)
        self.sample_rate_var.set(str(self.config.audio_settings.get('sample_rate', 16000)))
        self.channels_var.set(str(self.config.audio_settings.get('channels', 1)))
        self.chunk_size_var.set(str(self.config.audio_settings.get('chunk_size', 1024)))

        # Update system settings
        if hasattr(self, 'start_on_boot_var'):
            self.start_on_boot_var.set(getattr(self.config, 'start_on_boot', False))
        if hasattr(self, 'check_updates_var'):
            self.check_updates_var.set(getattr(self.config, 'check_for_updates', True))

    def update_config_from_gui(self):
        """Update config object from GUI values."""
        # Update model paths
        self.config.model_paths['chatty'] = self.chatty_path_var.get()
        self.config.model_paths['computer'] = self.computer_path_var.get()
        self.config.model_paths['idle'] = self.idle_path_var.get()

        # Update other settings
        self.config.default_state = self.default_state_var.get()
        self.config.inference_framework = self.framework_var.get()

        # Update audio settings
        try:
            self.config.audio_settings['sample_rate'] = int(self.sample_rate_var.get())
            self.config.audio_settings['channels'] = int(self.channels_var.get())
            self.config.audio_settings['chunk_size'] = int(self.chunk_size_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid audio settings. Please enter valid numbers.")
            return False

        return True

    def start_service(self):
        """Start the ChattyCommander service."""
        if not self.update_config_from_gui():
            return

        self.save_config()

        try:
            # Start the service using the CLI
            self.service_process = subprocess.Popen(
                ['python', 'cli.py', 'run', '--config', self.config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            self.service_running = True
            self.status_label.config(text="Service Status: Running")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

            # Start monitoring the service output
            self.monitor_service()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start service: {e}")

    def stop_service(self):
        """Stop the ChattyCommander service."""
        if hasattr(self, 'service_process') and self.service_process:
            self.service_process.terminate()
            self.service_process = None

        self.service_running = False
        self.status_label.config(text="Service Status: Stopped")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def monitor_service(self):
        """Monitor service output and update log."""
        if hasattr(self, 'service_process') and self.service_process and self.service_running:
            try:
                line = self.service_process.stdout.readline()
                if line:
                    self.log_text.insert(tk.END, line)
                    self.log_text.see(tk.END)

                # Check if process is still running
                if self.service_process.poll() is not None:
                    self.stop_service()
                    return

                # Schedule next check
                self.root.after(100, self.monitor_service)
            except Exception as e:
                self.log_text.insert(tk.END, f"Error monitoring service: {e}\n")

    def test_config(self):
        """Test the current configuration."""
        if not self.update_config_from_gui():
            return

        try:
            # Validate configuration
            self.config.validate()
            messagebox.showinfo("Success", "Configuration is valid!")
        except Exception as e:
            messagebox.showerror("Configuration Error", f"Configuration validation failed: {e}")

    def toggle_start_on_boot(self):
        """Toggle start on boot setting."""
        try:
            enabled = self.start_on_boot_var.get()
            self.config.set_start_on_boot(enabled)
            status = "enabled" if enabled else "disabled"
            self.log_text.insert(tk.END, f"Start on boot {status}\n")
            self.log_text.see(tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle start on boot: {str(e)}")
            # Revert the checkbox state
            self.start_on_boot_var.set(not self.start_on_boot_var.get())

    def toggle_update_checking(self):
        """Toggle automatic update checking."""
        try:
            enabled = self.check_updates_var.get()
            self.config.set_check_for_updates(enabled)
            status = "enabled" if enabled else "disabled"
            self.log_text.insert(tk.END, f"Automatic update checking {status}\n")
            self.log_text.see(tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle update checking: {str(e)}")
            # Revert the checkbox state
            self.check_updates_var.set(not self.check_updates_var.get())

    def check_updates_now(self):
        """Check for updates immediately."""
        try:
            self.log_text.insert(tk.END, "Checking for updates...\n")
            self.log_text.see(tk.END)
            self.root.update()  # Update GUI to show the message

            update_info = self.config.check_for_updates()
            if update_info is None:
                self.log_text.insert(tk.END, "Could not check for updates.\n")
            elif update_info['updates_available']:
                self.log_text.insert(
                    tk.END, f"Updates available: {update_info['update_count']} commits\n"
                )
                self.log_text.insert(tk.END, f"Latest: {update_info['latest_commit']}\n")
                messagebox.showinfo(
                    "Updates Available",
                    f"Updates available: {update_info['update_count']} commits\n"
                    f"Latest: {update_info['latest_commit']}",
                )
            else:
                self.log_text.insert(tk.END, "No updates available.\n")
                messagebox.showinfo("Updates", "No updates available.")

            self.log_text.see(tk.END)
        except Exception as e:
            error_msg = f"Error checking for updates: {str(e)}\n"
            self.log_text.insert(tk.END, error_msg)
            self.log_text.see(tk.END)
            messagebox.showerror("Error", f"Failed to check for updates: {str(e)}")


class CommandDialog:
    """Dialog for adding/editing commands."""

    def __init__(self, parent, title, value_label, name="", value=""):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")

        # Name field
        ttk.Label(self.dialog, text="Command Name:").pack(pady=5)
        self.name_var = tk.StringVar(value=name)
        ttk.Entry(self.dialog, textvariable=self.name_var, width=50).pack(pady=5)

        # Value field
        ttk.Label(self.dialog, text=f"{value_label}:").pack(pady=5)
        self.value_var = tk.StringVar(value=value)
        ttk.Entry(self.dialog, textvariable=self.value_var, width=50).pack(pady=5)

        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)

        # Focus on name field
        self.dialog.focus_set()

        # Wait for dialog to close
        self.dialog.wait_window()

    def ok_clicked(self):
        name = self.name_var.get().strip()
        value = self.value_var.get().strip()

        if not name or not value:
            messagebox.showerror("Error", "Both name and value are required.")
            return

        self.result = (name, value)
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()


class StateModelsDialog:
    """Dialog for editing state models."""

    def __init__(self, parent, state_models):
        self.result = None
        self.state_models = state_models.copy()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit State Models")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")

        # Create interface for each state
        self.model_vars = {}

        for state in ['idle', 'chatty', 'computer']:
            frame = ttk.LabelFrame(self.dialog, text=f"{state.title()} State Models")
            frame.pack(fill=tk.X, padx=10, pady=5)

            models = self.state_models.get(state, [])
            models_str = ', '.join(models) if isinstance(models, list) else str(models)

            self.model_vars[state] = tk.StringVar(value=models_str)
            ttk.Entry(frame, textvariable=self.model_vars[state], width=70).pack(padx=5, pady=5)
            ttk.Label(frame, text="(Comma-separated list of model paths)", font=('Arial', 8)).pack(
                padx=5
            )

        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)

        # Wait for dialog to close
        self.dialog.wait_window()

    def ok_clicked(self):
        result = {}
        for state, var in self.model_vars.items():
            models_str = var.get().strip()
            if models_str:
                models = [model.strip() for model in models_str.split(',') if model.strip()]
                result[state] = models
            else:
                result[state] = []

        self.result = result
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()


def main():
    """Main function to run the GUI."""
    try:
        root = tk.Tk()
    except tk.TclError:
        print(
            "Error: GUI cannot be started because no display is available. Running in headless environment."
        )
        return
    ChattyCommanderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
