import customtkinter as ctk
from tkinter import messagebox
import json
import os
import re
import requests
import keyboard
import threading
from Detection import RobloxLogWatcher
from Webhook import send_biome_signal
from bot import discordbot
import time
import pydirectinput

PRIVATE_SERVER_PATTERNS = [
    re.compile(r"https://www\.roblox\.com/games/\d+/.+\?privateServerLinkCode=.+"),
    re.compile(r"https://www\.roblox\.com/share\?code=.+&type=Server")
]

def is_valid_private_server(url):
    for pattern in PRIVATE_SERVER_PATTERNS:
        if pattern.fullmatch(url):
            return True
    return False

# ---------------- THEME ----------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------- CONSTANTS ----------------
CONFIG_FILE = "config.json"

BIOMES = [
    "Heaven", "Glitched", "Dreamspace", "Cyberspace",
    "Starfall", "Sand storm", "Hell", "Windy",
    "Rainy", "Null", "Snowy", "Normal"
]

PING_EVERYONE = {"Glitched", "Dreamspace", "Cyberspace"}

# ---------------- MAIN APP ----------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ranger - 1/10 rate it")
        self.geometry("740x540")
        self.resizable(False, False)
        self.watch_folder = os.path.expanduser(r"~\AppData\Local\Roblox\logs")
        self.watcher = None
        self.discord_bot = None

        # Defaults
        self.webhook_username = ""
        self.webhook_url = ""
        self.privateserver_url = ""
        self.bot_token = ""
        self.biome_settings = {b: False for b in BIOMES}
        self.use_strange_biome_controller = ctk.BooleanVar(value=False)
        self.afk_enabled = ctk.BooleanVar(value=False)
        self.bot_enabled = ctk.BooleanVar(value=False)
        self.strange_biome_running = False

        # Load config early
        self.load_config()

        # Tabs
        self.tabview = ctk.CTkTabview(self, width=700, height=480)
        self.tabview.pack(padx=20, pady=20)

        self.tab_webhook = self.tabview.add("Webhook Configuration")
        self.tab_bot = self.tabview.add("Bot Configuration")
        self.tab_misc = self.tabview.add("Misc")
        self.tab_afk = self.tabview.add("AFK")


        self.build_webhook_tab()
        self.build_bot_tab()
        self.build_misc_tab()
        self.build_afk_tab()

        keyboard.add_hotkey("F1", lambda: self.start_watcher())
        keyboard.add_hotkey("F2", lambda: self.stop_watcher())


    def build_webhook_tab(self):
        ctk.CTkLabel(
            self.tab_webhook,
            text="Webhook Configuration",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=20)

        ctk.CTkButton(
            self.tab_webhook,
            text="Add Webhook",
            width=260,
            height=40,
            command=self.open_webhook_popup
        ).pack(pady=12)

        ctk.CTkButton(
            self.tab_webhook,
            text="Biome Configuration",
            width=260,
            height=40,
            command=self.open_biome_popup
        ).pack(pady=8)

        ctk.CTkLabel(self.tab_webhook, text="Private Server Link").pack(pady=(15, 5))

        self.privateserver_entry = ctk.CTkEntry(self.tab_webhook, width=400)
        self.privateserver_entry.pack()


        if self.privateserver_url:
            self.privateserver_entry.insert(0, self.privateserver_url)

        ctk.CTkButton(
            self.tab_webhook,
            text="Save Private Server",
            width=200,
            command=self.save_private_server
        ).pack(pady=10)

    def open_webhook_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add Webhook")
        popup.geometry("420x320")
        popup.resizable(False, False)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Username").pack(pady=(20, 5))
        username_entry = ctk.CTkEntry(popup, width=320)
        username_entry.insert(0, self.webhook_username)
        username_entry.pack()

        ctk.CTkLabel(popup, text="Webhook URL").pack(pady=(15, 5))
        webhook_entry = ctk.CTkEntry(popup, width=320)
        webhook_entry.insert(0, self.webhook_url)
        webhook_entry.pack()

        ctk.CTkButton(
            popup,
            text="Save Webhook",
            width=200,
            command=lambda: self.save_webhook(
                username_entry.get(),
                webhook_entry.get(),
                popup
            )
        ).pack(pady=25)

    def save_webhook(self, username, webhook, popup):
        if not username or not webhook:
            messagebox.showerror("Error", "All fields are required.")
            return

        self.webhook_username = username
        self.webhook_url = webhook
        self.save_config()

        messagebox.showinfo("Saved", "Webhook saved.")
        popup.destroy()

    def open_biome_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Biome Configuration")
        popup.geometry("460x520")
        popup.resizable(False, False)
        popup.grab_set()

        frame = ctk.CTkScrollableFrame(popup, width=420, height=380)
        frame.pack(padx=10, pady=10)

        self.biome_vars = {}

        for biome in BIOMES:
            row = ctk.CTkFrame(frame)
            row.pack(fill="x", pady=4, padx=5)

            ctk.CTkLabel(row, text=biome, width=140, anchor="w").pack(side="left", padx=10)

            var = ctk.BooleanVar(value=self.biome_settings.get(biome, False))
            self.biome_vars[biome] = var

            ctk.CTkSwitch(row, text="Notify", variable=var).pack(side="right", padx=10)

        ctk.CTkButton(
            popup,
            text="Save Settings",
            width=200,
            command=lambda: self.save_biomes(popup)
        ).pack(pady=15)

    def save_biomes(self, popup):
        for biome, var in self.biome_vars.items():
            self.biome_settings[biome] = var.get()

        self.save_config()
        messagebox.showinfo("Saved", "Biome settings saved.")
        popup.destroy()

    def save_private_server(self):
        url = self.privateserver_entry.get().strip()
        if not is_valid_private_server(url):
            messagebox.showerror("Invalid Link", "Please enter a valid Roblox Private Server link or Share link.")
            return

        self.privateserver_url = url
        self.save_config()
        messagebox.showinfo("Saved", "Private Server link saved successfully!")


    def build_bot_tab(self):
        ctk.CTkLabel(
            self.tab_bot,
            text="Bot Configuration",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=20)

        ctk.CTkLabel(self.tab_bot, text="Discord Bot Token").pack(pady=(10, 5))
        
        self.bot_token_entry = ctk.CTkEntry(self.tab_bot, width=400, show="*")
        if self.bot_token:
            self.bot_token_entry.insert(0, self.bot_token)
        self.bot_token_entry.pack()

        ctk.CTkButton(
            self.tab_bot,
            text="Save Bot Token",
            width=200,
            command=self.save_bot_token
        ).pack(pady=15)


        status_frame = ctk.CTkFrame(self.tab_bot)
        status_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(
            status_frame,
            text="Bot Status:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)

        self.bot_status_label = ctk.CTkLabel(
            status_frame,
            text=" Bot is OFF",
            font=ctk.CTkFont(size=14)
        )
        self.bot_status_label.pack(pady=5)


        button_frame = ctk.CTkFrame(self.tab_bot)
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Start Bot",
            width=150,
            command=self.start_bot
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Stop Bot",
            width=150,
            command=self.stop_bot
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            self.tab_bot,
            text="View Commands",
            width=200,
            command=self.show_commands_popup
        ).pack(pady=15)

       
        commands_frame = ctk.CTkFrame(self.tab_bot)
        commands_frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(
            commands_frame,
            text="Available Commands:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)

  
        commands = [
            ("!help", "Lists all available commands"),
            ("!ssi", "Screenshots the inventory"),
            ("!ssa", "Screenshots the achievements"),
            ("!screenshot", "Takes a general screenshot")
        ]

        for cmd, desc in commands:
            cmd_row = ctk.CTkFrame(commands_frame, fg_color="transparent")
            cmd_row.pack(fill="x", pady=3, padx=10)
            
            ctk.CTkLabel(
                cmd_row,
                text=cmd,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
                width=120
            ).pack(side="left", padx=(5, 10))
            
            ctk.CTkLabel(
                cmd_row,
                text=desc,
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(side="left")

    def save_bot_token(self):
        token = self.bot_token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter a bot token.")
            return

        self.bot_token = token
        self.save_config()
        messagebox.showinfo("Saved", "Bot token saved successfully!")

    def start_bot(self):
        if not self.bot_token:
            messagebox.showerror("Error", "Please save a bot token first.")
            return

        if self.discord_bot and self.discord_bot.is_running:
            messagebox.showinfo("Info", "Bot is already running.")
            return

        self.discord_bot = discordbot(self.bot_token)
        if self.discord_bot.start():
            self.bot_status_label.configure(text=" Bot is ONLINE")
            messagebox.showinfo("Success", "Discord bot started successfully!")
        else:
            messagebox.showerror("Error", "Failed to start bot.")

    def stop_bot(self):
        if not self.discord_bot or not self.discord_bot.is_running:
            messagebox.showinfo("Info", "Bot is not running.")
            return

        if self.discord_bot.stop():
            self.bot_status_label.configure(text=" Bot is OFF")
            messagebox.showinfo("Success", "Discord bot stopped.")
        else:
            messagebox.showerror("Error", "Failed to stop bot.")

    def show_commands_popup(self):
        """Show a popup window with all available bot commands"""
        popup = ctk.CTkToplevel(self)
        popup.title("Bot Commands")
        popup.geometry("520x400")
        popup.resizable(False, False)
        popup.grab_set()

        ctk.CTkLabel(
            popup,
            text="Discord Bot Commands",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)


        commands_frame = ctk.CTkScrollableFrame(popup, width=480, height=280)
        commands_frame.pack(padx=20, pady=10)

        commands = [
            ("!help", "Lists all available commands with descriptions"),
            ("!ssi", "Takes a Screenshot of your Inventory/All the potions you have "),
            ("!ssa", "Takes a Screenshot of your Aura Storage "),
            ("!screenshot", "Takes a Screenshot of whole Screen")
        ]

        for cmd, desc in commands:
   
            cmd_container = ctk.CTkFrame(commands_frame, fg_color=("gray85", "gray25"))
            cmd_container.pack(fill="x", pady=8, padx=5)
            
           
            ctk.CTkLabel(
                cmd_container,
                text=cmd,
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w"
            ).pack(fill="x", padx=15, pady=(10, 5))
            
       
            ctk.CTkLabel(
                cmd_container,
                text=desc,
                font=ctk.CTkFont(size=12),
                anchor="w",
                wraplength=440
            ).pack(fill="x", padx=15, pady=(0, 10))

      
        ctk.CTkButton(
            popup,
            text="Close",
            width=150,
            command=popup.destroy
        ).pack(pady=15)


    def build_misc_tab(self):
        ctk.CTkLabel(
            self.tab_misc,
            text="Misc Settings",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=20)

        ctk.CTkSwitch(
            self.tab_misc,
            text="Use Strange and Biome controller (MUST HAVE UI NAVIGATION ON)",
            variable=self.use_strange_biome_controller,
            command=self.toggle_strange_biome_controller
        ).pack(pady=20)

     
        ctk.CTkButton(
            self.tab_misc,
            text="Test Webhook",
            width=250,
            command=self.test_webhook
        ).pack(pady=15)

       
        ctk.CTkButton(
            self.tab_misc,
            text="Start (F1)",
            width=250,
            command=self.start_watcher
        ).pack(pady=5)

        ctk.CTkButton(
            self.tab_misc,
            text="Stop (F2)",
            width=250,
            command=self.stop_watcher
        ).pack(pady=5)

    def test_webhook(self):
        config = None
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read config: {e}")
            return

        webhook_url = config.get("webhook", {}).get("url")
        if not webhook_url:
            messagebox.showerror("Error", "No webhook URL found in config.")
            return

        try:
            response = requests.post(webhook_url, json={"content": "Test message from GUI."})
            if response.status_code in [200, 204]:
                messagebox.showinfo("Success", "Webhook test message sent successfully!")
            else:
                messagebox.showerror("Failed", f"Webhook returned status code: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send webhook: {e}")

    def toggle_strange_biome_controller(self):
        """Toggle the Strange and Biome controller macro on/off"""
        if self.use_strange_biome_controller.get():
            self.strange_biome_running = True
            self.start_strange_biome_macro()
        else:
            self.strange_biome_running = False
        self.save_config()

    def start_strange_biome_macro(self):
        """Start the macro in a background thread - runs every 15 minutes"""
        def macro_loop():
            def press(key, delay=0.1):
                pydirectinput.press(key)
                time.sleep(delay)
            
            sequence = [
                '\\', 'a', 's', 's', 'enter', 'd', 'w', 'd', 'enter',
                's', 'enter', 's', 't', 'r', 'a', 'enter', 's', 's',
                's', 'enter', 'a', 'w', 'd', 'enter', 'd', 'w', 'enter',
                'r', 'a', 'n', 'enter', 's', 's', 's', 'enter', 'a',
                'w', 'd', 'enter', 'd', 'w', 'enter', 'enter', 'w',
                'enter', 'a', 'enter', 'w', 's', 'a', 'w', 'w', 'w', 'enter', '\\'
            ]
            
  
            time.sleep(3)
            
          
            while self.strange_biome_running and self.use_strange_biome_controller.get():
                print("[Strange Biome] Running macro sequence...")
                for key in sequence:
                    if not self.strange_biome_running or not self.use_strange_biome_controller.get():
                        break
                    press(key)
                
                print("[Strange Biome] Macro sequence completed. Waiting 15 minutes...")
                
                for _ in range(900):
                    if not self.strange_biome_running or not self.use_strange_biome_controller.get():
                        break
                    time.sleep(1)
        
        threading.Thread(target=macro_loop, daemon=True).start()


    def build_afk_tab(self):
        ctk.CTkLabel(
            self.tab_afk,
            text="AFK Mode",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=20)

        self.afk_toggle = ctk.CTkSwitch(
            self.tab_afk,
            text="Enable AFK (Press Space every 10 minutes)",
            variable=self.afk_enabled,
            command=self.toggle_afk
        )
        self.afk_toggle.pack(pady=20)

        self.afk_status_label = ctk.CTkLabel(
            self.tab_afk,
            text="AFK is OFF",
            font=ctk.CTkFont(size=16)
        )
        self.afk_status_label.pack(pady=10)

    def toggle_afk(self):
        if self.afk_enabled.get():
            self.afk_status_label.configure(text="AFK is ON")
            self.start_afk_thread()
        else:
            self.afk_status_label.configure(text="AFK is OFF")

    def start_afk_thread(self):
        def afk_loop():
            while self.afk_enabled.get():
                pydirectinput.press("space")
                print("[AFK] Pressed spacebar.")
          
                for _ in range(600):
                    if not self.afk_enabled.get():
                        break
                    time.sleep(1)
        threading.Thread(target=afk_loop, daemon=True).start()

    def start_watcher(self):
        if self.watcher:
            messagebox.showinfo("Ranger", "Ranger is already running.")
            return

        self.watcher = RobloxLogWatcher(
            self.watch_folder,
            signal_callback=self.send_to_webhook
        )
        self.watcher.start()
  
        if self.use_strange_biome_controller.get():
            self.strange_biome_running = True
            self.start_strange_biome_macro()
        
        messagebox.showinfo("Ranger", "Ranger has started.")

    def stop_watcher(self):
        if self.watcher:
            self.watcher.stop()
            self.watcher = None
            
  
            self.strange_biome_running = False
            
            messagebox.showinfo("Watcher", "Log watcher stopped.")
        else:
            messagebox.showinfo("Watcher", "Log watcher is not running.")

    def send_to_webhook(self, biome, line):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print("[LogWatcher] Failed to read config:", e)
            return

        biomes_config = config.get("biomes", {})
        webhook_data = config.get("webhook", {})
        private_server = config.get("private_server", "")

        if not biomes_config.get(biome, False):
            return

        ping = "@everyone " if biome in PING_EVERYONE else ""

        send_biome_signal(
            webhook_url=webhook_data.get("url", ""),
            username=webhook_data.get("username", ""),
            biome=biome,
            line=line,
            private_server=private_server,
            ping=ping
        )


    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.webhook_username = data.get("webhook", {}).get("username", "")
            self.webhook_url = data.get("webhook", {}).get("url", "")
            self.biome_settings.update(data.get("biomes", {}))
            self.use_strange_biome_controller.set(
                data.get("misc", {}).get("use_strange_biome_controller", False)
            )
            self.privateserver_url = data.get("private_server", "")
            self.bot_token = data.get("bot_token", "")

           
            if hasattr(self, "privateserver_entry") and self.privateserver_url:
                self.privateserver_entry.delete(0, "end")
                self.privateserver_entry.insert(0, self.privateserver_url)

        except Exception as e:
            print("Failed to load config:", e)

    def save_config(self):
        data = {
            "webhook": {
                "username": self.webhook_username,
                "url": self.webhook_url
            },
            "biomes": self.biome_settings,
            "misc": {
                "use_strange_biome_controller": self.use_strange_biome_controller.get()
            },
            "private_server": self.privateserver_url,
            "bot_token": self.bot_token
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)



if __name__ == "__main__":
    app = App()
    app.mainloop()