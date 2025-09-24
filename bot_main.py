#!/usr/bin/python3

import sys
import asyncio
import os
import traceback
import time
import io
import contextlib
from datetime import datetime
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.channel import TextChannel

load_dotenv()

# Global variables and configuration
bot_start_time = datetime.now()

def get_uptime():
    delta = datetime.now() - bot_start_time
    return str(delta)

def days_until_christmas():
    today = datetime.now()
    christmas = datetime(today.year, 12, 25)
    if today > christmas:
        christmas = datetime(today.year + 1, 12, 25)
    
    delta = christmas - today
    return delta.days

def get_build_id():
    return "v2.0-cogs"

# Bot configuration
status_hold = False
temporary_status = None  
temporary_status_time = None
ecancel = False
shutdown_in_progress = False
status_queue = []
new_status = f"{days_until_christmas()} Days until Christmas!"
my_secret = os.getenv('BOT_KEY')
ND_API_KEY = os.getenv('NOTDIAMOND_API_KEY')
fallback_model = "gpt-3.5-turbo-1106"
glasgow_block = True

# Clear screen
os.system('cls' if os.name == 'nt' else 'clear')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True

async def terminal_repl():
    loop = asyncio.get_event_loop()
    print("Terminal REPL started. Type your Python code below:")
    while True:
        # Read a line from the terminal without blocking the event loop.
        code_str = await loop.run_in_executor(None, sys.stdin.readline)
        code_str = code_str.strip()
        if not code_str:
            continue
        try:
            # Attempt to compile and evaluate as an expression.
            code_obj = compile(code_str, "<stdin>", "eval")
            result = eval(code_obj, globals())
            if asyncio.iscoroutine(result):
                result = await result
            if result is not None:
                print(result)
        except SyntaxError:
            # If eval fails (likely due to statements), try exec.
            try:
                code_obj = compile(code_str, "<stdin>", "exec")
                with io.StringIO() as buffer:
                    with contextlib.redirect_stdout(buffer):
                        exec(code_obj, globals())
                    output = buffer.getvalue()
                if not output:
                    continue
                print(output)
            except Exception:
                print("Execution error:\n", traceback.format_exc())
        except Exception:
            print("Evaluation error:\n", traceback.format_exc())

class CogBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("7/"),
            intents=intents,
            case_insensitive=True,
            help_command=None
        )
    
    async def setup_hook(self):
        # Load all cogs
        await self.load_initial_cogs()
        
        # Schedule the terminal REPL task after the bot is ready.
        time.sleep(15)
        asyncio.create_task(terminal_repl())
    
    async def load_initial_cogs(self):
        """Load all cogs at startup"""
        cogs_to_load = [
            'cogs.admin',
            'cogs.moderation', 
            'cogs.ai',
            'cogs.utility',
            'cogs.points',
            'cogs.channel_management',
            'cogs.events'
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                print(f"✓ Loaded {cog}")
            except Exception as e:
                print(f"✗ Failed to load {cog}: {e}")
    
    async def on_ready(self):
        print(f'Logged in as {self.user.name}')
        print(f'With ID: {self.user.id}')
        print('------')
        
        # Notify startup channel
        channel = self.get_channel(0)  # Replace with actual channel ID if needed
        if isinstance(channel, TextChannel):
            await channel.send("7x v2.0 - Now listening for commands! (Cog system active)")

# Create bot instance
bot = CogBot()

# Core cog management commands (these need to be in main bot file)
@bot.command(name="load_cog", help="Load a cog")
@commands.is_owner()
async def load_cog(ctx, *, cog: str):
    """Load a cog"""
    try:
        await bot.load_extension(f"cogs.{cog}")
        await ctx.send(f"✓ Successfully loaded {cog}")
    except Exception as e:
        await ctx.send(f"✗ Failed to load {cog}: {e}")

@bot.command(name="unload_cog", help="Unload a cog")
@commands.is_owner()
async def unload_cog(ctx, *, cog: str):
    """Unload a cog"""
    try:
        await bot.unload_extension(f"cogs.{cog}")
        await ctx.send(f"✓ Successfully unloaded {cog}")
    except Exception as e:
        await ctx.send(f"✗ Failed to unload {cog}: {e}")

@bot.command(name="reload_cog", help="Reload a cog")
@commands.is_owner()
async def reload_cog(ctx, *, cog: str):
    """Reload a cog"""
    try:
        await bot.reload_extension(f"cogs.{cog}")
        await ctx.send(f"✓ Successfully reloaded {cog}")
    except Exception as e:
        await ctx.send(f"✗ Failed to reload {cog}: {e}")

@bot.command(name="list_cogs", help="List all loaded cogs")
@commands.is_owner()
async def list_cogs(ctx):
    """List all loaded cogs"""
    cogs = list(bot.cogs.keys())
    if cogs:
        cog_list = "\n".join([f"• {cog}" for cog in cogs])
        await ctx.send(f"**Loaded Cogs:**\n```\n{cog_list}\n```")
    else:
        await ctx.send("No cogs are currently loaded.")

@bot.command(name="restart_bot", help="Restart the entire bot using external script")
@commands.is_owner()
async def restart_bot(ctx):
    """Restart the entire bot process"""
    await ctx.send("🔄 Initiating bot restart...")
    
    # Save current state if needed
    # ... (add any cleanup code here)
    
    # Execute restart script
    try:
        # Create restart flag file
        with open("restart_flag", "w") as f:
            f.write("restart")
        
        await ctx.send("✓ Restart initiated. Bot will be back shortly.")
        await bot.close()
    except Exception as e:
        await ctx.send(f"✗ Restart failed: {e}")

if __name__ == "__main__":
    bot.run(my_secret)