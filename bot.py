import discord
from discord.ext import commands
import pydirectinput
import pyautogui
import time
import io
import threading

class discordbot:
    def __init__(self, token):
        self.token = token
        self.bot = None
        self.bot_thread = None
        self.is_running = False
        
    def create_bot(self):
        intents = discord.Intents.default()
        intents.message_content = True
       
        self.bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
        
        @self.bot.event
        async def on_ready():
            print(f'[Discord Bot] Logged in as {self.bot.user.name}')
            
        @self.bot.command(name='help')
        async def help_command(ctx):
            """Lists all available commands"""
            embed = discord.Embed(
                title="Bot Commands",
                description="Here are all available commands:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="!help",
                value="Shows this help message",
                inline=False
            )
            embed.add_field(
                name="!ssi",
                value="Screenshots the inventory",
                inline=False
            )
            embed.add_field(
                name="!ssa",
                value="Screenshots the achievements",
                inline=False
            )
            embed.add_field(
                name="!screenshot",
                value="Takes a general screenshot",
                inline=False
            )
            await ctx.send(embed=embed)
        
        @self.bot.command(name='ssi')
        async def screenshot_inventory(ctx):
            """Screenshots the inventory"""
            await ctx.send("Taking Aura Storage screenshot...")
            
            try:
                pydirectinput.press('\\')
                time.sleep(0.1)
                pydirectinput.press('a')
                time.sleep(0.2)
                pydirectinput.press('enter')
                time.sleep(0.1)
                screenshot = pyautogui.screenshot()
                time.sleep(2.0)
                pydirectinput.press('enter')
                time.sleep(0.2)
                pydirectinput.press('\\')
                
                # Convert to bytes and send
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                await ctx.send(
                    "Inventory Screenshot:",
                    file=discord.File(img_byte_arr, 'inventory.png')
                )
            except Exception as e:
                await ctx.send(f"Failed to screenshot inventory: {str(e)}")
        
        @self.bot.command(name='ssa')
        async def screenshot_Potions(ctx):
            """Screenshots the potions storage"""
            await ctx.send("Taking Potions screenshot...")
            
            try:
                pydirectinput.press('\\')
                time.sleep(0.1)
                pydirectinput.press('a')
                time.sleep(0.1)
                pydirectinput.press('s')
                time.sleep(0.1)
                pydirectinput.press('s')
                time.sleep(0.1)
                pydirectinput.press('enter')
                time.sleep(0.1)
                pydirectinput.press('d')
                time.sleep(0.1)

                pydirectinput.press('w')
                time.sleep(0.1)
                pydirectinput.press('d')
                time.sleep(0.1)
                pydirectinput.press('enter')
                time.sleep(0.1)
                screenshot = pyautogui.screenshot()
                time.sleep(3.0)
                pydirectinput.press('a')
                time.sleep(0.1)
                pydirectinput.press('enter')
                time.sleep(0.1)

                pydirectinput.press('a')
                time.sleep(0.1)

                pydirectinput.press('s')
                time.sleep(0.1)

                pydirectinput.press('s')
                time.sleep(0.1)
                pydirectinput.press('enter')
                time.sleep(0.1)
                pydirectinput.press('\\')
                
                # Convert to bytes and send
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                await ctx.send(
                    "Inventory Storage Screenshot:",
                    file=discord.File(img_byte_arr, 'achievements.png')
                )
            except Exception as e:
                await ctx.send(f"Failed to Inventory achievements: {str(e)}")
        
        @self.bot.command(name='screenshot')
        async def general_screenshot(ctx):
            """Takes a general screenshot"""
            await ctx.send("Taking screenshot...")
            
            try:
                # Take screenshot
                screenshot = pyautogui.screenshot()
                
                # Convert to bytes and send
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                await ctx.send(
                    "Screenshot:",
                    file=discord.File(img_byte_arr, 'screenshot.png')
                )
            except Exception as e:
                await ctx.send(f"Failed to take screenshot: {str(e)}")
    
    def start(self):
        """Start the bot in a separate thread"""
        if self.is_running:
            print("[Discord Bot] Bot is already running")
            return False
        
        if not self.token:
            print("[Discord Bot] No token provided")
            return False
        
        self.create_bot()
        self.is_running = True
        
        def run_bot():
            try:
                self.bot.run(self.token)
            except Exception as e:
                print(f"[Discord Bot] Error: {e}")
                self.is_running = False
        
        self.bot_thread = threading.Thread(target=run_bot, daemon=True)
        self.bot_thread.start()
        return True
    
    def stop(self):
        """Stop the bot"""
        if self.bot and self.is_running:
            import asyncio
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.bot.close())
                loop.close()
            except:
                pass
            self.is_running = False
            return True
        return False