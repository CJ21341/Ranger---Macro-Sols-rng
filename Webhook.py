import json
import requests
import os
import time

CONFIG_FILE = "config.json"
PING_EVERYONE = {"Glitched", "Dreamspace", "Cyberspace"}
BLACKLIST = {"hello", "%3null"}  # Add more words here if needed

# Track the currently active biome
last_active_biome = None
last_active_start = 0

# Track last sent timestamp per biome for cooldown
biome_cooldowns = {}  # biome_name -> last_sent_timestamp

# Cooldown in seconds
COOLDOWN_SECONDS = 10

# Optional: define images per biome
BIOME_IMAGES = {
    "Heaven": "https://maxstellar.github.io/biome_thumb/HEAVEN.png",
    "Glitched": "https://maxstellar.github.io/biome_thumb/GLITCHED.png",
    "Dreamspace": "https://maxstellar.github.io/biome_thumb/DREAMSPACE.png",
    "Cyberspace": "https://maxstellar.github.io/biome_thumb/CYBERSPACE.png",
    "Starfall": "https://maxstellar.github.io/biome_thumb/STARFALL.png",
    "Sand storm": "https://maxstellar.github.io/biome_thumb/SANDSTORM.png",
    "Hell": "https://maxstellar.github.io/biome_thumb/HELL.png",
    "Windy": "https://maxstellar.github.io/biome_thumb/WINDY.png",
    "Rainy": "https://maxstellar.github.io/biome_thumb/RAINY.png",
    "Null": "https://maxstellar.github.io/biome_thumb/NULL.png",
    "Snowy": "https://maxstellar.github.io/biome_thumb/SNOWY.png",
    "Normal": "https://maxstellar.github.io/biome_thumb/NORMAL.png"
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def send_webhook_message(webhook_url, content, image_url=None):
    """Helper to send a message to Discord webhook"""
    payload = {"content": content}
    if image_url:
        payload["embeds"] = [{"image": {"url": image_url}}]

    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print("[Webhook Error]", e)


def send_biome_signal(webhook_url, username, biome, line, private_server="", ping=""):
    """Send a start message for the new biome and end the previous biome if necessary."""
    global last_active_biome, last_active_start, biome_cooldowns

    # Check blacklist
    for blacklisted in BLACKLIST:
        if blacklisted.lower() in line.lower():
            print(f"[Webhook] Ignored blacklisted trigger: {line}")
            return

    now = int(time.time())

    # End the previous biome if different
    if last_active_biome and last_active_biome != biome:
        timestamp_code = f"<t:{last_active_start}:R>"
        end_msg = f"`{last_active_biome}` HAS ENDED {timestamp_code}\n***```{username}``` in server***"
        end_image = BIOME_IMAGES.get(last_active_biome)
        send_webhook_message(webhook_url, end_msg, image_url=end_image)

    # Skip sending if the same biome is still active
    if last_active_biome == biome:
        print(f"[Webhook] Same biome '{biome}' detected, ignoring repeat.")
        return

    # Start the new biome
    last_active_biome = biome
    last_active_start = now
    biome_cooldowns[biome] = now  # Update last sent timestamp

    timestamp_code = f"<t:{now}:R>"
    message = f"{ping}```Trigger: {line}```\n"
    message += f"**{biome} started {timestamp_code}**\n"
    message += f"*{username} in server*\n"
    if private_server:
        message += f"Server: {private_server}"

    image_url = BIOME_IMAGES.get(biome)
    send_webhook_message(webhook_url, message, image_url=image_url)
