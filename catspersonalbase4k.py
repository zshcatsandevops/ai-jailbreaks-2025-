import tkinter as tk
from tkinter import ttk, messagebox
import minecraft_launcher_lib as mll
import subprocess
import os
import json
import uuid
import threading
from pathlib import Path

class MinecraftLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Launcher")
        self.root.geometry("800x500")
        self.root.resizable(False, False)
        self.root.configure(bg='#2d2d2d')
        
        # Apply theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#2d2d2d')
        self.style.configure('TLabel', background='#2d2d2d', foreground='white')
        self.style.configure('TButton', background='#3b6ea5', foreground='white', borderwidth=0)
        self.style.map('TButton', background=[('active', '#4a7eb4')])
        self.style.configure('TCombobox', fieldbackground='#3d3d3d', background='#3d3d3d', foreground='white')
        self.style.configure('TEntry', fieldbackground='#3d3d3d', foreground='white')
        self.style.configure('TProgressbar', troughcolor='#3d3d3d', background='#3b6ea5')
        
        # Minecraft directory
        self.minecraft_dir = os.path.join(str(Path.home()), ".minecraft_launcher")
        
        # Variables
        self.versions = []
        self.selected_version = tk.StringVar()
        self.selected_install_version = tk.StringVar()
        self.username = tk.StringVar(value="Player")
        self.setup_done = False
        
        self.setup_ui()
        self.load_available_mc_versions()
        self.check_setup()
    
    # Config management
    def get_config_path(self):
        return os.path.join(self.minecraft_dir, "launcher_config.json")

    def load_config(self):
        try:
            path = self.get_config_path()
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_config(self, data):
        try:
            path = self.get_config_path()
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.status_label.config(text=f"Failed to save config: {str(e)}")

    # UI setup
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        logo_label = ttk.Label(main_frame, text="Minecraft Launcher", 
                               font=("Arial", 24, "bold"))
        logo_label.pack(pady=20)
        
        username_frame = ttk.Frame(main_frame)
        username_frame.pack(fill=tk.X, pady=10)
        ttk.Label(username_frame, text="Username:").pack(side=tk.LEFT)
        username_entry = ttk.Entry(username_frame, textvariable=self.username)
        username_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        version_install_frame = ttk.Frame(main_frame)
        version_install_frame.pack(fill=tk.X, pady=10)
        ttk.Label(version_install_frame, text="Install Version:").pack(side=tk.LEFT)
        self.install_version_combo = ttk.Combobox(version_install_frame, textvariable=self.selected_install_version)
        self.install_version_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        version_frame = ttk.Frame(main_frame)
        version_frame.pack(fill=tk.X, pady=10)
        ttk.Label(version_frame, text="Launch Version:").pack(side=tk.LEFT)
        self.version_combo = ttk.Combobox(version_frame, textvariable=self.selected_version)
        self.version_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=30)
        self.setup_btn = ttk.Button(button_frame, text="Install", 
                                   command=self.setup_minecraft, width=20)
        self.setup_btn.pack(side=tk.LEFT, padx=10)
        self.launch_btn = ttk.Button(button_frame, text="Launch", 
                                    command=self.launch_minecraft, state=tk.DISABLED, width=20)
        self.launch_btn.pack(side=tk.LEFT, padx=10)
        self.refresh_btn = ttk.Button(button_frame, text="Refresh", 
                                     command=self.refresh_versions, width=20)
        self.refresh_btn.pack(side=tk.LEFT, padx=10)
        
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.pack()
    
    # Version management
    def refresh_versions(self):
        self.load_available_mc_versions()
        self.load_versions()
        self.status_label.config(text="Versions refreshed")
    
    def load_available_mc_versions(self):
        try:
            version_list = mll.utils.get_version_list()
            releases = [v['id'] for v in version_list if v['type'] in ['release', 'snapshot']]
            self.install_version_combo['values'] = releases
            if releases:
                self.selected_install_version.set(releases[0])
        except Exception as e:
            self.status_label.config(text=f"Error loading available versions: {str(e)}")
    
    def check_setup(self):
        if os.path.exists(self.minecraft_dir):
            self.load_versions()
            config = self.load_config()
            saved_version = config.get("launch_version")
            if saved_version and saved_version in [v['id'] for v in self.versions]:
                self.selected_version.set(saved_version)
                self.status_label.config(text=f"Loaded saved launch version: {saved_version}")
        else:
            self.status_label.config(text="Minecraft directory not found. Click Install.")
    
    def load_versions(self):
        try:
            all_versions = mll.utils.get_installed_versions(self.minecraft_dir)
            self.versions = all_versions
            version_list = [v['id'] for v in all_versions]
            self.version_combo["values"] = version_list
            if version_list:
                if not self.selected_version.get():
                    self.selected_version.set(version_list[0])
                self.launch_btn.config(state=tk.NORMAL)
                self.setup_done = True
                self.status_label.config(text="Ready to play!")
            else:
                self.launch_btn.config(state=tk.DISABLED)
                self.status_label.config(text="No versions installed. Click Install.")
        except Exception as e:
            self.status_label.config(text=f"Error loading versions: {str(e)}")
    
    # Installation
    def setup_minecraft(self):
        threading.Thread(target=self._setup_minecraft_thread, daemon=True).start()
    
    def _setup_minecraft_thread(self):
        try:
            self.setup_btn.config(state=tk.DISABLED)
            self.progress.start()
            self.status_label.config(text="Setting up Minecraft...")
            
            os.makedirs(self.minecraft_dir, exist_ok=True)
            
            mc_version = self.selected_install_version.get()
            if not mc_version:
                raise Exception("No version selected for installation")
            
            self.status_label.config(text=f"Installing Minecraft {mc_version}...")
            mll.install.install_minecraft_version(mc_version, self.minecraft_dir)
            
            self.load_versions()
            if self.versions:
                installed = self.versions[0]['id']
                self.selected_version.set(installed)
                self.save_config({"launch_version": installed})
                self.status_label.config(text=f"Installation complete! Default set to {installed}")
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
            self.status_label.config(text=f"Installation failed: {str(e)}")
        finally:
            self.progress.stop()
            self.setup_btn.config(state=tk.NORMAL)
    
    # Launching
    def launch_minecraft(self):
        if not self.setup_done:
            messagebox.showerror("Error", "Please install Minecraft first")
            return
        threading.Thread(target=self._launch_minecraft_thread, daemon=True).start()
    
    def _launch_minecraft_thread(self):
        try:
            self.launch_btn.config(state=tk.DISABLED)
            self.progress.start()
            
            version = self.selected_version.get()
            username = self.username.get()
            player_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, username))
            
            # Check if jar exists
            jar_path = os.path.join(self.minecraft_dir, "versions", version, f"{version}.jar")
            if not os.path.exists(jar_path):
                self.status_label.config(text=f"JAR missing, reinstalling {version}...")
                mll.install.install_minecraft_version(version, self.minecraft_dir)
            
            options = {
                "username": username,
                "uuid": player_uuid,
                "token": "",
                "gameDirectory": self.minecraft_dir
            }
            command = mll.command.get_minecraft_command(version, self.minecraft_dir, options)
            
            self.status_label.config(text=f"Launching Minecraft ({version})...")
            subprocess.Popen(command)
            
            self.status_label.config(text=f"Game started! ({version})")
            self.save_config({"launch_version": version})
        except Exception as e:
            messagebox.showerror("Error", f"Launch failed: {str(e)}")
            self.status_label.config(text=f"Launch failed: {str(e)}")
        finally:
            self.progress.stop()
            self.launch_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = MinecraftLauncher(root)
    root.mainloop()
