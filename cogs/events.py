import asyncio
import os
import json
import time
import random
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord.channel import TextChannel
import discord

def load_data(filename):
    """Load JSON data from file"""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_data(data, filename):
    """Save JSON data to file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def load_slots():
    """Load role slots data"""
    SLOTS_FILE = "role_slots.json"
    if os.path.exists(SLOTS_FILE):
        with open(SLOTS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_slots(slots):
    """Save role slots data"""
    SLOTS_FILE = "role_slots.json"
    with open(SLOTS_FILE, 'w') as f:
        json.dump(slots, f, indent=4)

def check_points(user_id):
    """Check user points"""
    from .database import load_db
    db = load_db()
    return db.get(f"points_{user_id}", 0)

def update_points(user_id, points):
    """Update user points"""
    from .database import load_db, save_db
    db = load_db()
    current_points = db.get(f"points_{user_id}", 0)
    db[f"points_{user_id}"] = max(current_points + points, 0)
    save_db(db)

# Load status tips and slowmode settings at startup
tips = [
    "Did you know? Of course you didn't.", "Run 7/help for help",
    "Hiya!", "Hello, world!", ":3", "Netflix", "You", "For 7/ commands", 
]

# Status management variables
status_hold = False
temporary_status = None
temporary_status_time = None
status_queue = []

class BotEvents(commands.Cog):
    """Bot event handlers"""
    
    def __init__(self, bot):
        self.bot = bot
        # Load slowmode settings
        self.slowmode_settings = load_data("slowmode_settings.json")
        print("Loaded slow mode settings:", self.slowmode_settings)
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Bot ready event"""
        print(f'Logged in as {self.bot.user.name}')
        print(f'With ID: {self.bot.user.id}')
        print('------')
        
        # Start status task
        self.bot.loop.create_task(self.change_status_task())
        
        # Notify startup channel (replace 0 with actual channel ID if needed)
        channel = self.bot.get_channel(0)
        if isinstance(channel, TextChannel):
            await channel.send("7x v2.0 (Cogs) - Now listening for commands!")
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, MissingRequiredArgument):
            command = ctx.command
            await ctx.send(f"""
        Missing required argument for {command.name}: {error.param.name}. Usage: {command.usage}
        """)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle message events"""
        if message.author.bot:
            return
        
        channel_id = message.channel.id
        user_id = str(message.author.id)
        
        print(f"User ID: {user_id}")  
        print(f"Current points: {check_points(user_id)}")  
        update_points(user_id, 0.0625)  
        print(f"Updated points: {check_points(user_id)}")  
        
        # Check if this channel has autoslowmode enabled
        if channel_id in self.slowmode_settings and self.slowmode_settings[channel_id]["active"]:
            settings = self.slowmode_settings[channel_id]
            settings["message_count"] += 1
            elapsed_time = time.time() - settings["last_check"]
            
            # Check the traffic every 60 seconds
            if elapsed_time >= 60:
                if settings["message_count"] > settings["mpm"]:
                    # Set slow mode if message_count exceeds threshold
                    await message.channel.edit(slowmode_delay=settings["slowmode_amount"])
                    await message.channel.send(
                        f"Slow mode activated: {settings['slowmode_amount']} second slowmode due to high activity."
                    )
                
                # Reset count and timestamp
                settings["message_count"] = 0
                settings["last_check"] = time.time()
            
            # Save the entire dictionary after the update
            save_data(self.slowmode_settings, "slowmode_settings.json")
        
        # Continue processing other commands
        await self.bot.process_commands(message)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Handle role deletion"""
        slots = load_slots()
        
        user_ids = list(slots.keys())
        
        for user_id in user_ids:
            user_roles = slots[user_id]
            if role.id in user_roles:
                user_roles.remove(role.id)
                if len(user_roles) == 0:
                    del slots[user_id]  
                else:
                    slots[user_id] = user_roles
        
        save_slots(slots)
    
    async def change_status_task(self):
        """Background task to change bot status"""
        global status_hold, temporary_status, temporary_status_time, status_queue
        last_status = None
        
        while True:
            if temporary_status and (datetime.now() - temporary_status_time).seconds > 10:
                temporary_status = None
            
            if status_hold:
                pass
            elif temporary_status:
                await self.bot.change_presence(activity=discord.Activity(
                    type=discord.ActivityType.watching, name=temporary_status))
            elif status_queue:
                next_status = status_queue.pop(0)
                await self.bot.change_presence(activity=discord.Activity(
                    type=discord.ActivityType.watching, name=next_status))
            else:
                new_status = random.choice(tips)
                while new_status == last_status:
                    new_status = random.choice(tips)
                await self.bot.change_presence(activity=discord.Activity(
                    type=discord.ActivityType.watching, name=new_status))
                last_status = new_status
            
            await asyncio.sleep(10)

async def setup(bot):
    await bot.add_cog(BotEvents(bot))