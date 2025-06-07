#!/usr/bin/python3
import argparse # Added for --eco flag
import os # Ensure os is imported
from datetime import datetime
from typing import Optional # Ensure Optional is imported
from dotenv import load_dotenv
# Removed duplicate imports of datetime, Optional, load_dotenv
from discord.channel import TextChannel
import discord # Ensuring discord is imported for various functionalities
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument, has_any_role
import asyncio
import sys
import io
import contextlib
import traceback
import random
import string
import time # 4 MyBot setup_hook
import json
import psutil

# --- Argument Parsing for --eco flag ---
parser = argparse.ArgumentParser(description="7x: A Discord bot.")
parser.add_argument(
    "--eco",
    action="store_true",
    help="Run in eco mode, disabling processor-intensive features to save resources."
)
# Parse known arguments, allowing Discord bot to receive its own args if necessary
cli_args, unknown_cli_args = parser.parse_known_args()
eco_mode = cli_args.eco

if eco_mode:
    print("Running in ECO mode. Processor-intensive features (like AI commands) will be limited or disabled.")
else:
    print("Running in FULL mode. All features enabled.")

# Moved from later in the script to after eco mode message
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')

load_dotenv()

# :3

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

def get_bot_info(bot: commands.Bot, ctx: Optional[commands.Context] = None):
  """Return basic bot info such as ping, shard ID and CPU load."""
  ping_ms = round(bot.latency * 1000)
  shard_id = ctx.guild.shard_id if ctx and ctx.guild else 0
  load = psutil.cpu_percent(interval=None)
  return {"ping_ms": ping_ms, "shard_id": shard_id, "cpu_load": load}

status_hold = False
temporary_status = None
temporary_status_time = None
ecancel = False
shutdown_in_progress = False
status_queue = []
new_status = f"{days_until_christmas()} Days until Christmas!"
status_hold = False
my_secret = os.getenv('BOT_KEY')
ND_API_KEY = os.getenv('NOTDIAMOND_API_KEY')
fallback_model = "gpt-3.5-turbo-1106"
glasgow_block = True

# Man pages dictionary
man_pages = {}

# Explanation for the 'beta' command group
beta_explanation = """
***Info:***
Provides information about the bot's build and uptime, or access to beta tester commands.

**Usage:**
`7/beta info` - Displays build ID and uptime.
`7/beta tester` - Accesses beta tester subcommands.
`7/beta help` - Shows this help message.

**Subcommands for `7/beta tester` (owner only):**
  `add <@member>` - Adds a member to the beta tester role.
  `remove <@member>` - Removes a member from the beta tester role.
  `list` - Lists all current beta testers.
"""
man_pages["beta"] = beta_explanation

# Explanation for the 'beta_tester' command group (used by 'beta tester' and direct '7/tester')
beta_tester_explanation = """
***Info:***
Manages beta testers for the bot. (Owner only)

**Usage:**
`7/tester add <@member>` - Adds a member to the '7x Waitlist' role.
`7/tester remove <@member>` - Removes a member from the '7x Waitlist' role.
`7/tester list` - Lists all members with the '7x Waitlist' role.
`7/tester help` - Shows this help message.
"""
man_pages["tester"] = beta_tester_explanation

# Explanation for the 'query-status' command
query_status_explanation = """
***Info:***
Queues status messages for the bot to display. (Manage Guild permissions required)

**Usage:**
`7/query-status "<message1>" "<message2>" ...` - Adds one or more messages to the status queue.
`7/query-status help` - Shows this help message.

**Examples:**
`7/query-status "Watching a movie" "Playing a game"`
"""
man_pages["query-status"] = query_status_explanation

# Explanation for the 'glasgow-block' command
glasgow_block_explanation = """
***Info:***
Toggles the Glasgow block feature.

**Usage:**
`7/glasgow-block <true|false>` - Enables or disables the Glasgow block.
`7/glasgow-block help` - Shows this help message.

**Examples:**
`7/glasgow-block true`
`7/glasgow-block false`
"""
man_pages["glasgow-block"] = glasgow_block_explanation

# Explanation for the 'eval' command
eval_explanation = """
***Info:***
Evaluates Python code. (Owner only)

**Usage:**
`7/eval <code>` - Executes the provided Python code.
`7/eval help` - Shows this help message.

**Examples:**
`7/eval print("Hello, world!")`
`7/eval 1 + 1`
"""
man_pages["eval"] = eval_explanation

# Explanation for the 'repl' command
repl_explanation = """
***Info:***
Starts an interactive Python REPL session in the current channel. (Owner only)
The bot edits its own message to create a scrolling terminal-style view.

**Usage:**
`7/repl` - Starts the REPL session.
`exit()` or `quit()` - Stops the REPL session.
`7/repl help` - Shows this help message.

**Details:**
- The REPL is unsandboxed, meaning code has full access to the bot's environment.
- Sessions automatically time out after a period of inactivity (15 minutes).
- Only one REPL session can be active per channel.
"""
man_pages["repl"] = repl_explanation

# Explanation for the 'echo' command
echo_explanation = """
***Info:***
Repeats the message you provide.

**Usage:**
`7/echo <message>` - The bot will send back your message.
`7/echo help` - Shows this help message.

**Examples:**
`7/echo Hello there!`
"""
man_pages["echo"] = echo_explanation

# Explanation for the 'shop' command
shop_explanation = """
***Info:***
Displays items available in the shop.

**Usage:**
`7/shop` - Shows the list of items and their prices.
`7/shop help` - Shows this help message.
"""
man_pages["shop"] = shop_explanation

# Explanation for the 'fillerspam' command
fillerspam_explanation = """
***Info:***
Creates a new channel and fills it with spam messages for testing. (Devs only)

**Usage:**
`7/fillerspam` or `7/fs` - Executes the command.
`7/fillerspam help` - Shows this help message.
"""
man_pages["fillerspam"] = fillerspam_explanation

# Explanation for the 'warn' command
warn_explanation = """
***Info:***
Warns a user and escalates their strike level. (Manage Messages permission required)
Strike levels include warnings, timeouts, kick, and ban.

**Usage:**
`7/warn <@member> [reason]` - Warns the member.
`7/warn help` - Shows this help message.

**Examples:**
`7/warn @User123 Spamming in chat.`
"""
man_pages["warn"] = warn_explanation

# Explanation for the 'pardon' command
pardon_explanation = """
***Info:***
Reduces a user's strike level by one. (Manage Messages permission required)

**Usage:**
`7/pardon <@member>` - Pardons the member.
`7/pardon help` - Shows this help message.

**Examples:**
`7/pardon @User123`
"""
man_pages["pardon"] = pardon_explanation

# Explanation for the 'lockdown' command
lockdown_explanation = """
***Info:***
Initiates or deactivates server lockdown. (Administrator permission required)
Initiating lockdown sets slowmode in all text channels to 10 seconds and deletes all active invites.
Deactivating lockdown reverts slowmode changes.

**Usage:**
`7/lockdown <initiate|deactivate>` - Manages lockdown state.
`7/lockdown help` - Shows this help message.

**Examples:**
`7/lockdown initiate`
`7/lockdown deactivate`
"""
man_pages["lockdown"] = lockdown_explanation

# Explanation for the 'spamping' command
spamping_explanation = """
***Info:***
Spam pings a user a specified number of times. (Mod or 7x Waitlist role required)
The bot will delete the command message.

**Usage:**
`7/spamping <@member> [amount]` - Pings the member. Default amount is 5, max is 25.
`7/spamping help` - Shows this help message.

**Examples:**
`7/spamping @User123 10`
`7/spamping @User123`
"""
man_pages["spamping"] = spamping_explanation

# Explanation for the 'cancel' command
cancel_explanation = """
***Info:***
Toggles the 'ecancel' flag, which can be used to stop certain ongoing bot operations.

**Usage:**
`7/cancel` - Toggles the ecancel state.
`7/cancel help` - Shows this help message.
"""
man_pages["cancel"] = cancel_explanation

# Explanation for the 'tc' command (test channel)
tc_explanation = """
***Info:***
Tests if the bot can send a message in the current channel by sending "Success".

**Usage:**
`7/tc` - Sends a test message.
`7/tc help` - Shows this help message.
"""
man_pages["tc"] = tc_explanation # Note: tc_explanation was already defined, this ensures it's in man_pages

# Explanation for the 'derhop' command
derhop_explanation = """
***Info:***
Placeholder command. (Functionality to be defined)

**Usage:**
`7/derhop [arguments...]`
`7/derhop help` - Shows this help message.
"""
man_pages["derhop"] = derhop_explanation

# Explanation for the 'setup' command
setup_explanation = """
***Info:***
Starts an interactive wizard to configure this server. (Manage Guild required)

**Usage:**
`7/setup` - Begin the wizard.
`7/setup help` - Shows this help message.
"""
man_pages["setup"] = setup_explanation

# Explanation for the 'shutdown' command
shutdown_explanation = """
***Info:***
Shuts down the bot. (Owner only)

**Usage:**
`7/shutdown` - Initiates bot shutdown.
`7/shutdown help` - Shows this help message.
"""
man_pages["shutdown"] = shutdown_explanation

# Explanation for the 'ai' command (already exists, ensuring it's in man_pages if not)
# ai_explanation is defined later in the script.
# We will add it to man_pages after its definition.



g4f_client = None 
if not eco_mode:
    try:
        from g4f.client import Client
        g4f_client = Client()
        print("g4f Client initialized for full mode.")
    except ImportError:
        print("WARNING: Failed to import g4f.client. AI features will be unavailable.")
    except Exception as e:
        print(f"WARNING: Failed to initialize g4f.client: {e}. AI features will be unavailable.")
else:
    print("g4f Client NOT initialized (ECO mode).")

def get_build_id():
  return "v1.9"
os.system('cls' if os.name == 'nt' else 'clear')

tips = [
    "Did you know? Of course you didn't.", "Run 7/help for help",
    "Hiya!", "Hello, world!", ":3", "Netflix", "You", "For 7/ commands", 
]

intents = discord.Intents.default()
intents.message_content = True 


class MyBot(commands.Bot):
  async def setup_hook(self):
    if not eco_mode:
      # Schedule the terminal REPL task after the bot is ready.
      time.sleep(15)
      asyncio.create_task(terminal_repl())

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
          # output = "Code executed without output."
          continue
        print(output)
      except Exception:
        print("Execution error:\n", traceback.format_exc())
    except Exception:
      print("Evaluation error:\n", traceback.format_exc())

bot = MyBot(command_prefix=commands.when_mentioned_or("7/"),
                   intents=intents,
                   case_insensitive=True,
                   help_command=None)

@bot.event
async def on_ready():
  print(f"Connected to {len(bot.guilds)} servers.")
  print(f'Logged in as {bot.user.name}')
  print(f'Build ID: {get_build_id()}')
  print(f'With ID: {bot.user.id}')
  print(f"Mode: {'ECO' if eco_mode else 'FULL'}")
  print('------')
  bot.loop.create_task(change_status_task())

@bot.event
async def on_guild_join(guild: discord.Guild):
  # Notify guild admins about setup
  channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
  if channel:
    await channel.send("Thanks for adding me! Server admins can run `7/setup` to configure the bot.")

@bot.group(invoke_without_command=True, help="General beta features and info.")
async def beta(ctx, option: Optional[str] = None, *, sub_command_args: Optional[str] = None):
    if option == "help":
        embed = discord.Embed(title="Beta Command Help", description=beta_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if option is None:
        await ctx.send("Please provide a valid option: `info`, `tester`, or `help`.")
    elif option == "info":
        info = get_bot_info(bot, ctx)
        await ctx.send(
            f"Build ID: {get_build_id()} | Uptime: {get_uptime()} | Ping: {info['ping_ms']}ms | Shard: {info['shard_id']} | CPU: {info['cpu_load']}%"
        )
    elif option == "tester":
        if sub_command_args:
            await ctx.invoke(bot.get_command('tester'), sub_command_args)
        else:
            await ctx.invoke(bot.get_command('tester'))
    else:
        await ctx.send(f"Unknown option: `{option}`. Use `7/beta help` for more info.")

@bot.group(name="tester", invoke_without_command=True, help="Beta tester management commands. (Owner only)")
@commands.is_owner()
async def beta_tester(ctx, subcommand_arg: Optional[str] = None, member_arg: Optional[discord.Member] = None):
    if subcommand_arg == "help":
        embed = discord.Embed(title="Beta Tester Command Help", description=beta_tester_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if ctx.invoked_subcommand is None and subcommand_arg not in ['add', 'remove', 'list']:
        await ctx.send("Valid subcommands are: `add`, `remove`, `list`. Use `7/tester help` for more info.")

@beta_tester.command(name="add", help="Adds a beta tester. Usage: 7/tester add <@member>")
async def beta_tester_add(ctx, member: Optional[discord.Member] = None):
    if member is None:
        await ctx.send("Please specify a member to add as a beta tester. Usage: `7/tester add <@member>`")
        return
    if role := discord.utils.get(ctx.guild.roles, name="7x Waitlist"):
        await member.add_roles(role)
        await ctx.send(f"Added {member.mention} as a beta tester.")
    else:
        await ctx.send("Role '7x Waitlist' not found.")

@beta_tester.command(name="remove", help="Removes a beta tester. Usage: 7/tester remove <@member>")
async def beta_tester_remove(ctx, member: Optional[discord.Member] = None):
    if member is None:
        await ctx.send("Please specify a member to remove from beta testers. Usage: `7/tester remove <@member>`")
        return
    role = discord.utils.get(ctx.guild.roles, name="7x Waitlist")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"Removed {member.mention} from beta testers.")
    else:
        await ctx.send(f"{member.mention} is not a tester.")

@beta_tester.command(name="list", help="Lists all beta testers.")
async def beta_tester_list(ctx):
    if role := discord.utils.get(ctx.guild.roles, name="7x Waitlist"):
        testers = [member.mention for member in role.members]
        await ctx.send("Beta Testers: " + ", ".join(testers))
    else:
        await ctx.send("No beta testers found.")

@bot.command(name="query-status")
@commands.has_permissions(manage_guild=True)
async def query_status(ctx, *, messages: Optional[str] = None):
    if messages and messages.lower() == "help":
        embed = discord.Embed(title="Query Status Command Help", description=query_status_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if not messages:
        await ctx.send("Please provide messages to queue or type `7/query-status help` for more info.")
        return

    global status_queue

    # Split the messages by quotes and filter out any empty strings
    messages_list = [msg for msg in messages.split('"') if msg.strip()]
    status_queue.extend(messages_list)

    await ctx.send(f"Queued {len(messages_list)} statuses.")

@bot.command(name="glasgow-block")
async def ggb(ctx, state: Optional[str] = None):
    if state and state.lower() == "help":
        embed = discord.Embed(title="Glasgow Block Command Help", description=glasgow_block_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return

    global glasgow_block
    if state is None:
        await ctx.send("Please specify `true` or `false`, or `help` for more info.")
        return

    state_bool = None
    if state.lower() == 'true':
        state_bool = True
    elif state.lower() == 'false':
        state_bool = False

    if state_bool is not None:
        glasgow_block = state_bool
        word = "Applied" if state_bool else "Removed"
        await ctx.send(f"Glasgow Block: {word}")
    else:
        await ctx.send(f"""Error: Expected boolean value (true/false) or 'help', received: "{state}" """)

@bot.command(name="setup")
@commands.has_permissions(manage_guild=True)
async def setup_wizard(ctx, *, args: Optional[str] = None):
    if args and args.lower() == "help":
        embed = discord.Embed(title="Setup Command Help", description=setup_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if args:
        embed = discord.Embed(title="Setup Command Help", description=setup_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return

    await ctx.send("Starting setup wizard. Reply with 'cancel' at any time to stop.")

    def check(m: discord.Message):
        return m.author == ctx.author and m.channel == ctx.channel

    config = {}

    await ctx.send("Enter strike roles separated by spaces or 'none':")
    msg = await bot.wait_for('message', check=check)
    if msg.content.lower() == 'cancel':
        await ctx.send("Setup cancelled.")
        return
    config['strike_roles'] = [r.id for r in msg.role_mentions]

    await ctx.send("Enable AI features? (yes/no):")
    msg = await bot.wait_for('message', check=check)
    if msg.content.lower() == 'cancel':
        await ctx.send("Setup cancelled.")
        return
    config['ai_enabled'] = msg.content.lower().startswith('y')

    await ctx.send("Economy type (regular/prankful/none):")
    msg = await bot.wait_for('message', check=check)
    if msg.content.lower() == 'cancel':
        await ctx.send("Setup cancelled.")
        return
    config['economy'] = msg.content.lower()

    db.setdefault('config', {})[str(ctx.guild.id)] = config
    save_db(db)
    await ctx.send("Setup complete.")



# Create a persistent global environment.
# Including __builtins__ is important for exec to work correctly.
global_env = {
  "__builtins__": __builtins__,
  "bot": None,
  "discord": discord,
  "commands": commands,
  "asyncio": asyncio,
}

@bot.command(name="eval")
@commands.is_owner()
async def _eval(ctx, *, code: Optional[str] = None):
    if code and code.lower() == "help":
        embed = discord.Embed(title="Eval Command Help", description=eval_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if not code:
        await ctx.send("Please provide code to evaluate or type `7/eval help` for more info.")
        return

    # Update the persistent environment with current context and bot.
    global_env["bot"] = bot
    global_env["ctx"] = ctx

      # If the code is wrapped in a code block, remove those markers.
    if code.startswith("```") and code.endswith("```"):
        lines = code.splitlines()
        code = "\n".join(lines[1:-1]) if len(lines) >= 3 else code[3:-3].strip()
    try:
      # First, try to compile as an expression.
      compiled = compile(code, "<eval>", "eval")
      result = eval(compiled, global_env)
      if asyncio.iscoroutine(result):
        result = await result
      await ctx.send(f"Result: {result}")
    except SyntaxError:
      try:
        compiled = compile(code, "<exec>", "exec")
        with io.StringIO() as buffer:
          with contextlib.redirect_stdout(buffer):
            exec(compiled, global_env)
          output = buffer.getvalue()
        if not output:
          output = "Code executed without output."
        await ctx.send(f"Output:\n```py\n{output}\n```")
      except Exception:
        tb = traceback.format_exc()
        await ctx.send(f"Error during exec:\n```py\n{tb}\n```")
    except Exception:
      tb = traceback.format_exc()
      await ctx.send(f"Error during eval:\n```py\n{tb}\n```")
async def force_status(ctx, *, status: str):
  global status_hold, temporary_status, temporary_status_time

  if '-indf' in status:
    status_hold = True 
    status = status.replace('-indf', '').strip() 
  else:
    status_hold = False  

  await bot.change_presence(activity=discord.Activity(
      type=discord.ActivityType.watching, name=status))

  if not status_hold:
    temporary_status = status
    temporary_status_time = datetime.now()
    await asyncio.sleep(10)  
    temporary_status = None
    temporary_status_time = None

  await ctx.send(f"Status changed to: {status}")

# ────────────────────────────────────────────────────────────────────────────────
# 7/repl  – owner-only live Python REPL that streams its output in Discord
# ────────────────────────────────────────────────────────────────────────────────
import textwrap                                               # add with the other imports

REPL_TIMEOUT = 15 * 60   # seconds of inactivity before the session auto-closes
repl_sessions: dict[int, asyncio.Task] = {}   # channel-id → running task


@bot.command(name="repl",
             help="Start an owner-only live Python REPL in this channel.",
             usage="7/repl   ← start | exit() / quit() to stop")
@commands.is_owner()
async def repl(ctx: commands.Context, *, args: Optional[str] = None):
    if args and args.lower() == "help":
        embed = discord.Embed(title="REPL Command Help", description=repl_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if args: # If any other arg is passed, show help.
        embed = discord.Embed(title="REPL Command Help", description=repl_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    """
    Interactive, *unsandboxed* Python – each line you send is executed.
    The bot edits one message so you get a scrolling terminal-style view.
    Use `exit()` or `quit()` (or let it time-out) to leave.
    """
    # If there’s already a session in this channel, ignore the new request.
    if ctx.channel.id in repl_sessions:
        await ctx.send("A REPL is already active in this channel.")
        return

    # Persistent namespace for this session only
    env = {
        "__builtins__": __builtins__,
        "bot": bot,
        "ctx": ctx,
        "discord": discord,
        "asyncio": asyncio,
        # feel free to expose extras here (db, client, …)
    }

    banner = "# ‣ Python REPL started – type exit() or quit() to stop\n>>> "
    log_lines: list[str] = [banner]

    # The message we’ll keep editing so the log scrolls in place
    term_msg = await ctx.send(f"```py\n{banner}```")

    def fmt_log() -> str:
        """Return the current log chunk wrapped in a code-block, truncated to 2 000 chars."""
        txt = "\n".join(log_lines)[-1950:]          # keep breathing room for the ```py
        return f"```py\n{txt}\n```"

    # Helper to append & display new output
    async def push(line: str):
        log_lines.append(line)
        payload = fmt_log()
        # If the edited message would be too large, send a fresh one instead.
        if len(payload) > 2000:
            await ctx.send(payload)
            log_lines.clear()
        else:
            await term_msg.edit(content=payload)

    # Wait-loop lives in its own task so multiple channels can run REPLs concurrently
    async def repl_loop():
        try:
            while True:
                # wait for the owner’s next message in this channel
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                try:
                    user_msg = await bot.wait_for("message",
                                                  check=check,
                                                  timeout=REPL_TIMEOUT)
                except asyncio.TimeoutError:
                    await push("\n# Session timed-out, REPL closed.")
                    break

                src = user_msg.content.strip()
                # Allow triple-back-tick blocks; strip fences if present
                if src.startswith("```") and src.endswith("```"):
                    src = "\n".join(src.splitlines()[1:-1])

                if src in {"exit()", "quit()", "exit", "quit"}:
                    await push("\n# REPL closed.")
                    break

                # Echo the input to the log
                await push(f">>> {src}")

                # Capture stdout/stderr
                with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    try:
                        try:
                            # try expression first, then statements
                            compiled = compile(src, "<repl>", "eval")
                            result = eval(compiled, env)
                            if asyncio.iscoroutine(result):
                                result = await result
                        except SyntaxError:
                            compiled = compile(src, "<repl>", "exec")
                            exec(compiled, env)
                            result = None
                    except Exception:
                        result = traceback.format_exc()

                    output = buf.getvalue()

                # Prepare what to print back
                lines = []
                if output:
                    lines.append(output.rstrip())
                if result is not None:
                    lines.append(repr(result))
                if not lines:
                    lines.append("None")

                await push("\n".join(lines))
        finally:
            # Clean-up so another session can be started later
            repl_sessions.pop(ctx.channel.id, None)

    # Store and start the task
    repl_sessions[ctx.channel.id] = asyncio.create_task(repl_loop())

async def change_status_task():
    global status_hold, temporary_status, temporary_status_time, status_queue
    last_status = None

    while True:
        if temporary_status and (datetime.now() - temporary_status_time).seconds > 10:
          temporary_status = None

        if status_hold:
            pass
        elif temporary_status:
            await bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching, name=temporary_status))
        elif status_queue:
            next_status = status_queue.pop(0)
            await bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching, name=next_status))
        else:
            new_status = random.choice(tips)
            while new_status == last_status:
              new_status = random.choice(tips)
            await bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching, name=new_status))
            last_status = new_status

        await asyncio.sleep(10)


shop_items = {
    'item1': {
        'price': 100,
        'description': 'Item 1 Description'
    },
    'item2': {
        'price': 200,
        'description': 'Item 2 Description'
    },
    # placeholder for later updates
}

@bot.command(name="echo")
async def echo(ctx, *, message: Optional[str] = None):
    if message and message.lower() == "help":
        embed = discord.Embed(title="Echo Command Help", description=echo_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if not message:
        await ctx.send("Please provide a message to echo or type `7/echo help` for more info.")
        return
    await ctx.send(message)
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass # Bot doesn't have permission to delete messages
    except discord.NotFound:
        pass # Message already deleted

@bot.command(name="shop")
async def shop(ctx, *, args: Optional[str] = None):
    if args and args.lower() == "help":
        embed = discord.Embed(title="Shop Command Help", description=shop_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if args: # If any other arg is passed, show help as shop takes no args
        embed = discord.Embed(title="Shop Command Help", description=shop_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title="7x Shop",
                        description="Available items to purchase with points:",
                        color=0x00ff00)
    if not shop_items:
        embed.description = "The shop is currently empty."
    else:
        for item_id, details in shop_items.items():
            embed.add_field(name=f"{item_id} - {details['price']} points",
                            value=details['description'],
                            inline=False)
    await ctx.send(embed=embed)

@bot.command(
    name="fillerspam",
    aliases=["fs"],
    help="Creates a channel and generates spam test messages. DEVS ONLY")
@commands.is_owner() # Typically a dev/owner only command
async def filler_spam(ctx, *, args: Optional[str] = None):
    if args and args.lower() == "help":
        embed = discord.Embed(title="FillerSpam Command Help", description=fillerspam_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if args: # If any other arg is passed, show help
        embed = discord.Embed(title="FillerSpam Command Help", description=fillerspam_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return

    try:
        new_channel = await ctx.guild.create_text_channel("test-spam-channel") # Renamed for clarity
        for _ in range(10): # Reduced spam for efficiency in testing
            gibberish = ''.join(
                random.choices(string.ascii_letters + string.digits, k=20))
            await new_channel.send(gibberish)
        await ctx.send(
            f"Channel {new_channel.mention} created and filled with test messages.")
    except discord.Forbidden:
        await ctx.send("I don't have permissions to create channels.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command(help="Warn a user and escalate their strike.", name="warn")
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: Optional[discord.Member] = None, *, reason: Optional[str] = None):
    if isinstance(member, str) and member.lower() == "help": # Check if first arg is 'help'
        embed = discord.Embed(title="Warn Command Help", description=warn_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if not member: # member is None
        await ctx.send("Please specify a member to warn or type `7/warn help`.")
        return
    if not reason:
        reason = "No reason provided"

    guild = ctx.guild
    # ... (rest of the warn command logic remains the same, but ensure it's efficient)
    # For efficiency, the existing logic is already quite direct.
    # The main improvement here is the help handling.
    current_role = next(
        (role for role in member.roles if role.name in strike_roles), None
    )
    if current_role is None:
        next_role_obj = discord.utils.get(guild.roles, name="Warning 1")
    else:
        try:
            current_index = strike_roles.index(current_role.name)
            next_role_name = strike_roles[min(current_index + 1, len(strike_roles) - 1)]
            next_role_obj = discord.utils.get(guild.roles, name=next_role_name)
        except ValueError: # Should not happen if strike_roles is consistent
            await ctx.send("An internal error occurred with role indexing.")
            return

    if not next_role_obj:
        await ctx.send(f"The role for the next strike level was not found. Please check server roles.")
        return

    try:
        if current_role:
            await member.remove_roles(current_role)
        await member.add_roles(next_role_obj)
        await ctx.send(f"{member.mention} has been warned and given the role: {next_role_obj.name} for: {reason}")

        # Timeout, kick, ban logic
        if next_role_obj.name == "Time out warning 1":
            await member.timeout(datetime.timedelta(minutes=10), reason=reason)
        elif next_role_obj.name == "Time out warning 2":
            await member.timeout(datetime.timedelta(hours=1), reason=reason)
        elif next_role_obj.name == "Time out warning 3":
            await member.timeout(datetime.timedelta(days=1), reason=reason)
        elif next_role_obj.name == "Kick warning":
            await member.kick(reason=f"Accumulated strikes: {reason}")
        elif next_role_obj.name == "Banned":
            await member.ban(reason=f"Accumulated strikes: {reason}")
        # Audit log reason was missing, adding it back.
        # await ctx.guild.audit_logs(reason=f"Warned {member.display_name}: {reason}") # This creates an entry, not what's usually done.
        # Instead, the actions (add_roles, timeout, kick, ban) have their own audit log entries.
    except discord.Forbidden:
        await ctx.send(f"I don't have permissions to manage roles or perform actions on {member.mention}.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command(help="Reverse the last warning of a user.", name="pardon")
@commands.has_permissions(manage_messages=True)
async def pardon(ctx, member: Optional[discord.Member] = None, *, args: Optional[str] = None):
    if isinstance(member, str) and member.lower() == "help": # Check if first arg is 'help'
        embed = discord.Embed(title="Pardon Command Help", description=pardon_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if args and args.lower() == "help": # Check if args (reason part) is 'help'
        embed = discord.Embed(title="Pardon Command Help", description=pardon_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if not member:
        await ctx.send("Please specify a member to pardon or type `7/pardon help`.")
        return

    guild = ctx.guild
    # ... (rest of the pardon command logic, ensuring efficiency)
    # Existing logic is fairly direct.
    current_role = next(
        (role for role in member.roles if role.name in strike_roles), None
    )
    if current_role is None:
        await ctx.send(f"{member.mention} has no warnings to pardon.")
        return

    try:
        current_index = strike_roles.index(current_role.name)
        await member.remove_roles(current_role)

        if current_index == 0:
            await ctx.send(f"{member.mention} has been fully pardoned. They now have no warning roles.")
        else:
            previous_role_name = strike_roles[current_index - 1]
            previous_role_obj = discord.utils.get(guild.roles, name=previous_role_name)
            if previous_role_obj:
                await member.add_roles(previous_role_obj)
                await ctx.send(f"{member.mention} has been pardoned and demoted to {previous_role_obj.name}.")
            else: # Should not happen if roles are set up
                await ctx.send(f"{member.mention} has been pardoned from {current_role.name}, but the previous role '{previous_role_name}' was not found.")
    except discord.Forbidden:
        await ctx.send(f"I don't have permissions to manage roles for {member.mention}.")
    except ValueError:
        await ctx.send(f"The role {current_role.name} is not in the recognized strike roles list.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command(help="Initiate or deactivate lockdown mode.", name="lockdown")
@commands.has_permissions(administrator=True)
async def lockdown(ctx, action: Optional[str] = None):
    if not action or action.lower() == "help":
        embed = discord.Embed(title="Lockdown Command Help", description=lockdown_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return

    guild = ctx.guild
    action_lower = action.lower()

    if action_lower == "initiate":
        try:
            for channel in guild.text_channels:
                await channel.edit(slowmode_delay=10)
            # Deleting invites can be disruptive and might require more specific permissions or intent.
            # Consider making invite deletion optional or a separate command.
            # invites = await guild.invites()
            # for invite in invites:
            #     await invite.delete()
            await ctx.send("Lockdown initiated. Slow mode is set to 10 seconds for all text channels.")
        except discord.Forbidden:
            await ctx.send("I don't have permissions to modify channel settings or manage invites.")
        except Exception as e:
            await ctx.send(f"An error occurred during lockdown initiation: {e}")

    elif action_lower == "deactivate":
        try:
            for channel in guild.text_channels:
                await channel.edit(slowmode_delay=0) # Reset slowmode
            await ctx.send("Lockdown deactivated. Channels are back to normal (slowmode reset).")
        except discord.Forbidden:
            await ctx.send("I don't have permissions to modify channel settings.")
        except Exception as e:
            await ctx.send(f"An error occurred during lockdown deactivation: {e}")
    else:
        await ctx.send("Invalid action. Use `initiate`, `deactivate`, or `help`.")


@bot.command(name="spamping",
             help="Spam pings a user a specified amount.",
             usage="7/spamping <@member> [amount]")
@has_any_role("mod", "7x Waitlist") # Ensure these roles exist or adjust as needed
async def spamping(ctx,
                   member: Optional[discord.Member] = None,
                   amount_str: Optional[str] = None): # Changed to str for help parsing
    global ecancel # Assuming ecancel is a global flag to stop spamming

    # Help check
    if isinstance(member, str) and member.lower() == "help":
        embed = discord.Embed(title="SpamPing Command Help", description=spamping_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if not member:
        await ctx.send("Please specify a user to ping or type `7/spamping help`.")
        return

    # Parse amount
    ping_count = 5 # Default
    if amount_str:
        if amount_str.lower() == "help": # If 'help' is in the amount position
            embed = discord.Embed(title="SpamPing Command Help", description=spamping_explanation, color=0x00ff00)
            await ctx.send(embed=embed)
            return
        try:
            ping_count = int(amount_str)
        except ValueError:
            await ctx.send("Invalid amount. Please provide a number or type `7/spamping help`.")
            return

    ping_count = min(max(1, ping_count), 25) # Ensure count is between 1 and 25

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    except discord.NotFound:
        pass

    ecancel = False # Reset cancel flag for this command instance
    for i in range(ping_count):
        if ecancel:
            await ctx.send(f"Spamming of {member.mention} cancelled after {i} pings.", delete_after=10)
            ecancel = False # Reset for next potential use
            return
        try:
            await ctx.send(f"{member.mention} ({i+1}/{ping_count})", delete_after=5) # Add counter and auto-delete pings
        except discord.Forbidden:
            await ctx.send("I don't have permission to send messages here.")
            return
        except Exception as e:
            await ctx.send(f"An error occurred while pinging: {e}")
            return
        await asyncio.sleep(1) # Small delay between pings to avoid rate limits
    await ctx.send(f"Finished pinging {member.mention} {ping_count} times.", delete_after=10)


@bot.command(name="cancel")
async def cancel(ctx, *, args: Optional[str] = None):
    if args and args.lower() == "help":
        embed = discord.Embed(title="Cancel Command Help", description=cancel_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if args: # If any other arg is passed, show help
        embed = discord.Embed(title="Cancel Command Help", description=cancel_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return

    global ecancel
    ecancel = not ecancel
    await ctx.send(f"Global 'ecancel' flag set to: {ecancel}")


@bot.command(name='tc',
             ignore_extra=False, # This is default, can be removed
             help="Tests if 7x can send a message in a channel.", # help is already in decorator
             usage="7/tc") # usage is already in decorator
async def tc_command(ctx, *, args: Optional[str] = None): # Changed to *args to catch 'help'
    if args and args.lower() == "help":
        # tc_explanation is already defined globally
        embed = discord.Embed(title="Test Channel (tc) Command Help", description=tc_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    if args: # If any other arg is passed, show help
        embed = discord.Embed(title="Test Channel (tc) Command Help", description=tc_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    try:
        await ctx.send("Success! I can send messages in this channel.")
    except discord.Forbidden:
        # Cannot send message, so can't inform user in this channel.
        # Bot owner might see an error in console if logging is set up.
        print(f"TC Command: Could not send message in {ctx.channel.name} ({ctx.channel.id}) due to permissions.")
    except Exception as e:
        print(f"TC Command: An error occurred in {ctx.channel.name} ({ctx.channel.id}): {e}")


@bot.command(name="derhop") # Basic structure, functionality to be added
async def derhop(ctx, *, args: Optional[str] = None):
    if args and args.lower() == "help":
        embed = discord.Embed(title="Derhop Command Help", description=derhop_explanation, color=0x00ff00)
        await ctx.send(embed=embed)
        return
    # Current behavior: if args are provided (other than help), it will show help.
    # If no args, it does nothing. This can be changed when functionality is added.
    if args:
        await ctx.send(f"Derhop received: `{args}`. Use `7/derhop help` for info.")
    else:
        await ctx.send("Derhop command acknowledged. Use `7/derhop help` for info.")

        @bot.command(name="shutdown")
        @commands.is_owner()
        async def shutdown(ctx, *args):
          # Check for help request
          if args and args[0].lower() == "help":
            embed = discord.Embed(title="Shutdown Command Help", description=shutdown_explanation, color=0x00ff00)
            await ctx.send(embed=embed)
            return

          global shutdown_in_progress

          # Emergency shutdown
          if args and '-e' in args:
            await ctx.send("Emergency Shutdown Bypass: Activated | Force Quiting All Running Services...")
            res = bot.close()
            return

          # Cancel ongoing shutdown
          if shutdown_in_progress:
            shutdown_in_progress = False
            await ctx.send("Shutdown sequence halted.")
            return

          # Start shutdown sequence with countdown
          shutdown_in_progress = True
          countdown_message = await ctx.send(
            "! - Shutdown Sequence Initiated: (--s) Run 7/shutdown again to cancel.")

          for i in range(10, 0, -1):
            if not shutdown_in_progress:
              return
            await countdown_message.edit(
              content=
              f"! - Shutdown Sequence Initiated: ({i}s) Run 7/shutdown again to cancel."
            )
            await asyncio.sleep(1)

          if shutdown_in_progress:
            await countdown_message.edit(
              content="! - Shutdown Sequence Initiated: (0s)")
            await asyncio.sleep(0.5)
            await countdown_message.edit(
              content="! - Shutdown Sequence Finished - 7x Shut Down.")
            await bot.close()

          shutdown_in_progress = False

# -------------------------
# Database Load/Save
# -------------------------
def load_db(filename="database.json"):
  """
  Loads the JSON database from disk, returns an empty dict if it doesn't exist or is invalid.
  """
  try:
    with open(filename, 'r') as f:
      # Check if file is empty
      first_char = f.read(1)
      if not first_char:
        return {} # Return empty dict if file is empty
      f.seek(0) # Reset file pointer
      return json.load(f)
  except FileNotFoundError:
    return {} # Return empty dict if file doesn't exist
  except json.JSONDecodeError:
    print(f"Warning: '{filename}' contains invalid JSON or is empty. Initializing with empty data.")
    # Optionally, you could back up the corrupted file here
    # and create a new empty one.
    # For now, we'll just return an empty dict and save_db will overwrite on next save.
    return {}

def save_db(data, filename="database.json"):
  """
  Saves the provided dict to the JSON database with indentation for readability.
  Ensures that an empty JSON object is written if data is empty.
  """
  with open(filename, 'w') as f:
    if not data: # Ensure data is not None or empty in a way that json.dump would fail
        json.dump({}, f, indent=4)
    else:
        json.dump(data, f, indent=4)

db = load_db()

def save_message(guild_id, user_id, message):
  """
  Appends a message dict to the conversation history for (guild_id, user_id).
  """
  key = f"{guild_id}-{user_id}"
  messages = db.get(key, [])
  messages.append(message)
  db[key] = messages
  save_db(db)

def get_messages(guild_id, user_id):
  """
  Retrieves the conversation history for (guild_id, user_id).
  """
  key = f"{guild_id}-{user_id}"
  return db.get(key, [])


# List of global variable names to exclude from debug output.
SAFETY_BLACKLIST = ['my_secret', 'ND_API_KEY']

@bot.command()
async def debug(ctx, *args):
  all_globals = globals()
  debug_info = []

  for name, value in all_globals.items():
    # Skip private/system variables.
    if name.startswith("__"):
      continue
    # Skip any variable that’s in our blacklist.
    if name in SAFETY_BLACKLIST:
      continue
    if args and name not in args:
      continue
    debug_info.append(f"{name}: {value}")

  output = "\n".join(debug_info)

  # Check if the output is too long for a message.
  if len(output) > 1900:
    with io.StringIO(output) as file:
      await ctx.send(file=discord.File(file, filename="debug.txt"))
  else:
    await ctx.send(f"```python\n{output}\n```")


# -------------------------
# AI Explanation / Help Text
# -------------------------
ai_explanation = (
  "**Info:**\n"
  "Interacts with an AI (model-specifiable) to simulate conversation or answer queries.\n"
  "- Normal conversation maintains context for a more coherent interaction.\n"
  "- Optional flag `-s` for a standalone query without context.\n"
  "\n"
  "**Usage:**\n"
  "`7/ai \"<message>\" [-s] [-search] [-model <model>]`\n"
  "\n"
  "**Examples:**\n"
  "`7/ai \"What is the capital of France?\"` (Contextual conversation)\n"
  "`7/ai \"What is the capital of France?\" -s` (Standalone, without conversation history)\n"
  "`7/ai \"What is the capital of France?\" -model gpt-4o` (Use the GPT-4o model)\n"
  "`7/ai \"What is the capital of France?\" -search` (Enable web search if supported)\n"
  "`7/ai \"What is the capital of France?\" -s -model gpt-4o -search` (Combine flags)\n"
  "`7/ai models` (Displays a list of available models.)\n"
  "\n"
  "**Tips:**\n"
  "- Use `-s` for quick queries when you don't need conversation context.\n"
  "- The `-search` flag enables web search for GPT-based models, helping get more accurate info.\n"
  "- The AI's response quality may vary based on the selected model.\n"
)
man_pages["ai"] = ai_explanation # Add AI explanation to man_pages

# A consolidated list of available models (remove duplicates)
available_models = [
  "gemini-1.5-pro",
  "llama-3.3-70b",
  "qwen-2.5-coder-32b",
  "hermes-3",
  "llama-3.2-90b",
  "blackboxai",
  "gpt-4",
  "gpt-4o",
  "gemini-1.5-flash",
  "claude-3.5-sonnet",
  "blackboxai-pro",
  "llama-3.1-8b",
  "llama-3.1-70b",
  "llama-3-1-405b",
  "mixtral-7b",
  "deepseek-chat",
  "dbrx-instruct",
  "qwq-32b",
  "hermes-2-dpo",
  "deepseek-r1",
  "gpt-4o-mini",
  "claude-3-haiku",
  "mixtral-8x7b",
  "wizardlm-2-8x22b",
  "wizardlm-2-7b",
  "qwen-2.5-72b",
  "nemotron-70b"
]
available_models = sorted(set(available_models))
# Models that support web_search
allowed_search_models = ["gpt-4", "gpt-4o", "gpt-4o-mini"]

# -------------------------
# Utility: Parsing Flags
# -------------------------
def parse_flags_and_content(raw_message: str):
    """
  Parses the user's raw message for flags and quoted content.
  Returns: (message_content, standalone, search_enabled, selected_model).
  """

    # Quick check for 'help' or 'models' before doing complex parse
    # (If the user literally typed 'help' or 'models' without quotes.)
    command_lower = raw_message.strip().lower()
    if command_lower == "help":
      return ("HELP_COMMAND", False, False, None)
    if command_lower == "models":
      return ("MODELS_LIST", False, False, None)

    # Standalone mode
    standalone = "-s" in raw_message
    # Web search flag
    search_enabled = "-search" in raw_message
    # Default model
    selected_model = "gpt-4o"

    # Remove the flags from the raw string; do it carefully so we don't kill partial text
    # We'll handle the -model part separately.
    def remove_flag(text, flag):
      return re.sub(rf"\s*{flag}\b", "", text)

    flags = ["-s", "-search"]
    for flag in flags:
      raw_message = remove_flag(raw_message, flag)

    # Check for "-model <model>"
    model_match = re.search(r"-model\s+(\S+)", raw_message)
    if model_match:
        model_candidate = model_match[1]
        # Remove it from the raw message
        raw_message = re.sub(rf"-model\s+{model_candidate}", "", raw_message).strip()
        selected_model = model_candidate

    # Now parse the quoted string
    message_content_pattern = r'"([^"]+)"'
    match = re.search(message_content_pattern, raw_message)
    message_content = match[1].strip() if match else ""
    return (message_content, standalone, search_enabled, selected_model)

# -------------------------
# Context Truncation (Placeholder)
# -------------------------
def truncate_conversation(conversation, model="gpt-4o", max_tokens=4000):
  """
  If you'd like to implement token-based truncation, you can place your logic here
  using tiktoken or a similar library. For now, it just returns the conversation unmodified.
  """
  # Example placeholder:
  # total_tokens = count_tokens_in_messages(conversation, model)
  # while total_tokens > max_tokens and len(conversation) > 2:
  #   conversation.pop(0)  # remove oldest message
  #   total_tokens = count_tokens_in_messages(conversation, model)
  return conversation

# -------------------------
# Response Splitting
# -------------------------
def split_into_chunks(text, chunk_size=2000):
  """
  Splits a long string into chunks for Discord messages.
  """
  return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

# -------------------------
# The Command
# -------------------------
@bot.command(name="ai", usage="7/ai <message> [-s] [-search] [-model <model>]", aliases=["ai_bot"])
async def ai_command(ctx, *, message: str = None):
    global glasgow_block
    if not message or not message.strip():
        await ctx.send("✦ | Please provide a message. For help, type: `7/ai help`.")
        return

    # Parse the flags and content
    message_content, standalone, search_enabled, selected_model = parse_flags_and_content(message)

    # If user asked for help (no quotes or "help")
    if message_content == "HELP_COMMAND":
      await send_help_embed(ctx)
      return

    # If user asked for model list
    if message_content == "MODELS_LIST":
      await send_models_list(ctx)
      return

    # If no quoted text found and it's not help/models
    if not message_content:
      await ctx.send("Please provide a message within quotes. For help, type: `7/ai help`.")
      return

    # Validate model
    if selected_model not in available_models:
      model_list_str = ", ".join(available_models) if available_models else "No models currently available."
      await ctx.send(f"Invalid model: **{selected_model}**.\nAvailable models: {model_list_str}")
      return

    # Validate -search usage for GPT models only
    if search_enabled and selected_model not in allowed_search_models:
      await ctx.send(f"⚠️ The **{selected_model}** model does not support web search.")
      # If you want to force it off but still continue:
      if glasgow_block:
         search_enabled = False
      return

    # Retrieve conversation or create a new one
    user_id = str(ctx.author.id)
    guild_id = str(ctx.guild.id)

    if standalone:
      conversation = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": message_content}
      ]
    else:
      existing_convo = get_messages(guild_id, user_id)
      # Insert system message right before user's new query
      conversation = existing_convo + [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": message_content}
      ]

    # Truncate conversation if needed (placeholder)
    conversation = truncate_conversation(conversation, model=selected_model, max_tokens=4000)

    # Show a "typing" indicator while generating the response
    async with ctx.typing():
      try:
        print(f"AI Command: {message_content}")
        print(f"Standalone: {standalone}")
        print(f"Search Enabled: {search_enabled}")
        print(f"Selected Model: {selected_model}")
        # GPT4Free call (adjust to your actual library usage)
        response = g4f_client.chat.completions.create(
          model=selected_model,
          messages=conversation,
          web_search=search_enabled
        )
        ai_reply = response.choices[0].message.content

        # Split the reply if it's too long for a single Discord message
        parts = split_into_chunks(ai_reply, 2000)
        for part in parts:
          await ctx.send(part)

        # If not standalone, save user/assistant messages to DB
        if not standalone:
          save_message(guild_id, user_id, {"role": "user", "content": message_content})
          save_message(guild_id, user_id, {"role": "assistant", "content": ai_reply})

      except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# -------------------------
# Sending Help Embed
# -------------------------
async def send_help_embed(ctx):
  """
  Sends a help embed with usage details, flag descriptions, and examples.
  Splits it up if needed.
  """
  embed = discord.Embed(title="AI Command Help", color=0x00ff00)
  embed.add_field(name="Usage", value='`7/ai "<message>" [-s] [-search] [-model <model>]`', inline=False)
  embed.add_field(
    name="Flags",
    value=(
      "**-s**: Standalone (ignore conversation history)\n"
      "**-search**: Enable web search (GPT-based models only)\n"
      "**-model <model>**: Choose one of the available models\n"
    ),
    inline=False
  )
  embed.add_field(
    name="Examples",
    value=(
      "`7/ai \"What is the capital of France?\"`\n"
      "`7/ai \"What is the capital of France?\" -s`\n"
      "`7/ai \"What is the capital of France?\" -model gpt-4o`\n"
      "`7/ai \"What is the capital of France?\" -search`\n"
      "`7/ai \"What is the capital of France?\" -s -model gpt-4o -search`\n"
      "`7/ai models` (displays available models)\n"
    ),
    inline=False
  )
  embed.add_field(
    name="Tips",
    value=(
      "• Use `-s` for quick queries without context.\n"
      "• `-search` fetches fresh info from the web on GPT models.\n"
      "• Model quality may vary.\n"
    ),
    inline=False
  )
  await ctx.send(embed=embed)

# -------------------------
# Sending Models List
# -------------------------
async def send_models_list(ctx):
  """
  Sends an embed listing all available models, with a note about which models
  support web search.
  """
  embed = discord.Embed(title="Available Models", color=0x00ff00)
  # Build a string listing each model. Mark the GPT-based models that allow search.
  lines = []
  for m in available_models:
    if m in allowed_search_models:
      lines.append(f"• **{m}** (web-search enabled)")
    else:
      lines.append(f"• {m}")

  embed.description = "\n".join(lines)
  embed.set_footer(text="Only GPT-based models support the -search flag.")
  await ctx.send(embed=embed)


def check_points(user_id):
  print("Checking points...")
  return db.get(f"points_{user_id}", 0)

def set_points(user_id, points):
  db[f"points_{user_id}"] = points
  save_db(db)
  print(f"Set points for user {user_id} to {points}")

def update_points(user_id, points):
  current_points = check_points(user_id)
  new_points = max(current_points + points, 0)
  set_points(user_id, new_points)
  print(f"Updated points for user {user_id} to {new_points}")

@bot.group(invoke_without_command=True)
async def points(ctx):
    await ctx.send("Usage: `7/points <add/remove/query> <@user> [amount]`")

@points.command()
@commands.has_permissions(manage_guild=True)
async def add(ctx, member: discord.Member, amount: int):
    user_id = str(member.id)
    update_points(user_id, amount)
    await ctx.send(f"Added {amount} points to {member.mention}. They now have {check_points(user_id)} points.")

@points.command()
@commands.has_permissions(manage_guild=True)
async def remove(ctx, member: discord.Member, amount: int):
    user_id = str(member.id)
    update_points(user_id, -amount)
    await ctx.send(f"Removed {amount} points from {member.mention}. They now have {check_points(user_id)} points.")

@points.command()
async def query(ctx, member: Optional[discord.Member] = None):
    if member is None:
        member = ctx.author
    user_id = str(member.id)
    points = check_points(user_id)
    await ctx.send(f"{member.mention} has {points} points.")

http_explanation = """
***Info:***
Deletes messages or entire channels based on flags.
- `-rm`: Deletes the channel.
- `-rmc`: Deletes and recreates the channel.
- `-trf`: Transfers messages from this channel to another.
- `-rmc.trf`: Deletes, clones, and transfers messages to a new channel.
- `-num`: Deletes or transfers a specified number of recent messages.

**Usage:**
`7/http -rm` (Deletes the channel)
`7/http -rmc` (Deletes and recreates the channel)
`7/http -trf <#target-channel>` (Transfers all messages)
`7/http -trf.num <#target-channel> <number>` (Transfers specified number of messages)
`7/http -rmc.trf <#target-channel>` (Deletes and transfers all messages to new channel)

**Examples:**
`7/http -rm`
`7/http -rmc`
`7/http -trf.num #new-channel 10`

***Tips:***
- Use `-rm` with caution; it can't be undone.
- `-trf` is useful for archiving messages from one channel to another.
- The `-num` flag can be used with both `-trf` and `-rmc`.
"""
@bot.command(help="Deletes messages or entire channels, or transfers messages.",
             usage="7/http -rm / -rmc / -trf / -num")
@commands.is_owner()
async def http(ctx, *args):
    if not args:
      await ctx.send("Usage: `7/http help` for detailed info.")
      return

    channel = ctx.channel

    if "help" in args:
      embed = discord.Embed(title="HTTP Command",
                            description=http_explanation,
                            color=0x00ff00)
      await ctx.send(embed=embed)
      return

    if "-rm" in args or "-rmc" in args or "-rmc.trf" in args:

        channel_category = channel.category
        channel_name = channel.name
        channel_position = channel.position
        channel_topic = channel.topic

        target_channel = None
        if "-rmc.trf" in args or "-trf" in args:
          try:
            target_channel = ctx.message.channel_mentions[0]
          except IndexError:
            await ctx.send("Please mention a valid target channel for message transfer.")
            return

        if "-trf" in args or "-rmc.trf" in args:

          await transfer_messages(ctx, channel, target_channel, args)

    if "-rmc" in args or "-rmc.trf" in args:
        await channel_category.create_text_channel(
          name=channel_name,
          topic=channel_topic,
          position=channel_position,
          reason="7/http command with -rmc or -rmc.trf flag")

        return

    if "-rm" in args:
        await channel.delete(reason="7/http command with -rm, -rmc or -rmc.trf flag")
    if "-ai" in args or "-regex" in args:
          await handle_scan_and_delete(ctx, args)
          return

    if "-all" in args:
      countdown_message = await ctx.send(
          "! - Server Purge Sequence Initiated: (--s) Run 7/shutdown -e to emergency cancel.")

      for i in range(10, 0, -1):
        await countdown_message.edit(
            content=f"! - Server Purge Sequence Initiated: ({i}s) Run 7/shutdown -e again to cancel.")
        await asyncio.sleep(1)

      await countdown_message.edit(content="! - Delete All Sequence Initiated: (0s)")
      await asyncio.sleep(0.5)
      await countdown_message.edit(content="! - Delete All Sequence Finished - Deleting all channels, roles, and bans members.")

      for channel in ctx.guild.channels:
        try:
          await channel.delete(reason="7/http command with -all flag")
        except Exception as e:
          await ctx.send(f"Failed to delete {channel.name}: {e}")

      for role in ctx.guild.roles:
        try:
          await role.delete(reason="7/http command with -all flag")
        except Exception as e:
          await ctx.send(f"Failed to delete role {role.name}: {e}")

      for member in ctx.guild.members:
        try:
          if member != ctx.guild.owner and ctx.me.top_role > member.top_role:
            await member.ban(reason="7/http command with -all flag")
        except Exception as e:
          await ctx.send(f"Failed to ban {member.name}: {e}")

      return
    if "-num" in args or "-trf.num" in args:
      try:
        num_index = args.index("-num") + 1 if "-num" in args else args.index("-trf.num") + 2
        num_messages = int(args[num_index])
        target_channel = ctx.message.channel_mentions[0] if "-trf.num" in args else None

        if "-trf.num" in args:
          await transfer_messages(ctx, channel, target_channel, args, num_messages)
        else:
          await ctx.channel.purge(limit=num_messages + 1)

      except (ValueError, IndexError):
        await ctx.send("Invalid usage, please specify a valid number of messages.")
      return

async def handle_scan_and_delete(ctx, args):
    try:
        if "-ai" in args and "-regex" in args:
            await ctx.send("❌ Cannot use both -ai and -regex flags together.")
            return

        if "-ai" in args:
            ai_index = args.index("-ai")
            if ai_index + 2 >= len(args):
                await ctx.send("❌ Missing parameters for -ai flag. Usage: `-ai \"query\" limit`")
                return
            query = args[ai_index + 1]
            try:
                limit = min(int(args[ai_index + 2]), 200)
            except ValueError:
                await ctx.send("❌ Invalid limit value for -ai flag")
                return

            # Fetch messages
            messages = []
            async for msg in ctx.channel.history(limit=limit, before=ctx.message):
                messages.append(msg)
            messages.reverse()  # Oldest first for context

            # Process with AI
            flagged_messages = await ai_scan_messages(query, messages)

        elif "-regex" in args:
            regex_index = args.index("-regex")
            if regex_index + 2 >= len(args):
                await ctx.send("❌ Missing parameters for -regex flag. Usage: `-regex pattern limit`")
                return
            pattern = args[regex_index + 1]
            try:
                limit = min(int(args[regex_index + 2]), 200)
            except ValueError:
                await ctx.send("❌ Invalid limit value for -regex flag")
                return

            # Fetch messages
            messages = []
            async for msg in ctx.channel.history(limit=limit, before=ctx.message):
                messages.append(msg)

            # Process with Regex
            try:
                regex = re.compile(pattern)
            except re.error:
                await ctx.send("❌ Invalid regular expression pattern")
                return

            flagged_messages = [msg for msg in messages if regex.search(msg.content)]

        else:
            await ctx.send("❌ Missing -ai or -regex flag")
            return

        if not flagged_messages:
            await ctx.send("✅ No messages found matching the criteria.")
            return

        # User review process
        await review_and_confirm(ctx, flagged_messages)

    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")
        raise e

async def ai_scan_messages(query, messages):
      # Make sure this variable is defined

    # Prepare messages for AI analysis
    messages_text = "\n".join(
        [f"{i+1}. [{msg.author.display_name}] {msg.content}" 
         for i, msg in enumerate(messages)]
    )

    prompt = f"""Analyze these messages for: {query}
    
Messages:
{messages_text}

Return a comma-separated list of message numbers that should be deleted. 
Consider message content, context, and any patterns of inappropriate content."""

    try:
        # ayai 76055
        response = g4f_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a content moderation assistant. Analyze messages and ONLY return numbers of messages to delete."},
            {"role": "user", "content": prompt}
        ],
        web_search=False
        )
        # Parse AI response
        numbers = []
        for part in response.choices[0].message.content.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                numbers.extend(range(start, end+1))
            else:
                numbers.append(int(part.strip()))

        # Convert to 0-based indices and get messages
        return [messages[i-1] for i in numbers if 0 < i <= len(messages)]

    except Exception as e:
        print(e)
        raise RuntimeError(f"AI processing failed: {str(e)}") from e

async def review_and_confirm(ctx, flagged_messages):
    # Create review embed
    embed = discord.Embed(
        title="⚠️ Flagged Messages Review",
        description=f"Found {len(flagged_messages)} potentially problematic messages",
        color=0xff9900
    )

    # Add first 10 messages as examples
    for idx, msg in enumerate(flagged_messages[:10], 1):
        embed.add_field(
            name=f"Message {idx} ({msg.author.display_name})",
            value=f"{msg.content[:100]}..." if len(msg.content) > 100 else msg.content,
            inline=False
        )

    if len(flagged_messages) > 10:
        embed.set_footer(text=f"Plus {len(flagged_messages)-10} more messages...")

    control_msg = await ctx.send(embed=embed)
    await control_msg.add_reaction("✅")
    await control_msg.add_reaction("❌")
    await control_msg.add_reaction("✏️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in {"✅", "❌", "✏️"}

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

        if str(reaction.emoji) == "✅":
            await perform_deletion(ctx, flagged_messages)
        elif str(reaction.emoji) == "❌":
            await ctx.send("❌ Deletion cancelled.")
        elif str(reaction.emoji) == "✏️":
            await edit_flagged_messages(ctx, flagged_messages)

    except asyncio.TimeoutError:
        await ctx.send("⌛ Review timed out. Cancelling deletion.")

async def edit_flagged_messages(ctx, flagged_messages):
    embed = discord.Embed(
        title="✏️ Edit Flagged Messages",
        description="Reply with message numbers to remove (space-separated)\nExample: `1 3 5-7`",
        color=0x00ffff
    )
    await ctx.send(embed=embed)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", timeout=60.0, check=check)
        to_remove = set()
        for part in msg.content.split():
            if '-' in part:
                start, end = map(int, part.split('-'))
                to_remove.update(range(start, end+1))
            else:
                to_remove.add(int(part))

        # Filter messages (using 1-based index)
        new_flagged = [
            msg for idx, msg in enumerate(flagged_messages, 1)
            if idx not in to_remove
        ]

        await ctx.send(f"✅ Updated to {len(new_flagged)} messages")
        await review_and_confirm(ctx, new_flagged)

    except (ValueError, IndexError):
        await ctx.send("❌ Invalid input format")
    except asyncio.TimeoutError:
        await ctx.send("⌛ Edit timed out. Cancelling.")

async def perform_deletion(ctx, messages):
    # Split into bulk deletable and individual messages
    bulk_deletable = []
    individual = []

    for msg in messages:
        if (datetime.now(timezone.utc) - msg.created_at).days < 14:
            bulk_deletable.append(msg)
        else:
            individual.append(msg)

    # Delete in bulk chunks of 100
    try:
        for chunk in [bulk_deletable[i:i+100] for i in range(0, len(bulk_deletable), 100)]:
            await ctx.channel.delete_messages(chunk)
    except Exception as e:
        await ctx.send(f"⚠️ Partial error during bulk delete: {str(e)}")

    # Delete older messages individually
    for msg in individual:
        try:
            await msg.delete()
        except Exception as e:
            await ctx.send(f"⚠️ Couldn't delete message from {msg.author}: {str(e)}")

    await ctx.send(f"✅ Successfully deleted {len(messages)} messages")


@bot.command()
@commands.is_owner()
async def test_fetch(ctx, source: discord.TextChannel, limit: int = 2):
  try:

    if not source.permissions_for(ctx.me).read_message_history:
      await ctx.send("I don't have permission to read the message history.")
      return
    if not source.permissions_for(ctx.me).read_messages:
      await ctx.send("I don't have permission to read messages in the source channel.")
      return

    await ctx.send(f"Attempting to fetch {limit} messages from {source.mention}...")


    print("Fetching messages...")
    messages = []
    async for message in source.history(limit=limit):
      messages.append(message)

    if not messages:
      await ctx.send("No messages were fetched.")
      return


    for message in messages:
      await ctx.send(f"Message from {message.author}: {message.content}")

  except asyncio.TimeoutError:
    await ctx.send("Fetching messages took too long and timed out.")
  except Exception as e:
    await ctx.send(f"An error occurred: {e}")

@bot.command()
@commands.is_owner()
async def test_transfer(ctx, source: discord.TextChannel, target: discord.TextChannel, amount: int):
  if not source.permissions_for(ctx.me).read_message_history:
    await ctx.send("I don't have permission to read message history in the source channel.")
    return
  if not target.permissions_for(ctx.me).send_messages:
    await ctx.send("I don't have permission to send messages in the target channel.")
    return
  await ctx.send(f"Moving {amount} messages...")
  await transfer_messages(ctx, source, target, amount)


async def transfer_messages(ctx, source_channel: discord.TextChannel, target_channel: discord.TextChannel, limit=None):
  print("Fetching messages from the source channel")

  messages = []
  async for message in source_channel.history(limit=limit):
    messages.append(message)
  if not messages:
    await ctx.send("No messages found in the source channel.")
    return


  print("Fetched messages successfully")
  messages.reverse()


  for message in messages:
    print(message.content)
    try:
      print("Skip system messages")
      if message.type != discord.MessageType.default:
        continue

      print("Create a webhook with the original user's name and avatar")
      webhook = await target_channel.create_webhook(name=f"{message.author.display_name} Webhook")
      await webhook.send(content=message.content,
                         username=message.author.display_name,
                         avatar_url=message.author.avatar.url if message.author.avatar else None)

      print("Delete the webhook after sending the message")
      await webhook.delete()

    except Exception as e:
      await ctx.send(f"Error transferring message from {message.author}: {e}")

  await ctx.send(f"Messages successfully transferred from {source_channel.mention} to {target_channel.mention}!")

def save_data(data, filename="data.json"):
  with open(filename, 'w') as f:
    json.dump(data, f)


def load_data(filename="data.json"):
  try:
    if os.path.exists(filename):
      with open(filename, 'r') as f:
        return json.load(f)
    return {}
  except FileNotFoundError:
     with open(filename, 'w') as f:
        return {}


def load_data(filename):
  try:
    with open(filename, "r") as f:
      return json.load(f)
  except FileNotFoundError:
    return {}
  except json.JSONDecodeError:
    return {}

def save_data(data, filename):
  with open(filename, "w") as f:
    json.dump(data, f, indent=2)

# Load the entire slowmode settings dict once at startup
slowmode_settings = load_data("slowmode_settings.json")
print("Loaded slow mode settings:", slowmode_settings)

@bot.command(help="Automatically enables slow mode when message traffic is high.",
             usage="7/autoslowmode <mpm> <slowmode amount>")
@commands.has_permissions(manage_guild=True)
async def autoslowmode(ctx, mpm: int, slowmode_amount: int = 5):
  # Register/Update this channel's settings
  slowmode_settings[ctx.channel.id] = {
    "mpm": mpm,
    "slowmode_amount": slowmode_amount,
    "message_count": 0,
    "last_check": time.time(),
    "active": True
  }
  # Save the entire dictionary
  save_data(slowmode_settings, "slowmode_settings.json")

  await ctx.send(
    f"Auto slowmode activated for this channel: "
    f"{mpm} messages per 60 seconds.\n"
    f"Slow mode will be set to {slowmode_amount} seconds on high traffic."
  )

  # Start the inactivity loop for this channel
  # If there's already a loop running for this channel, you may need to handle that.
  bot.loop.create_task(reset_slowmode_if_inactive(ctx.channel))

async def reset_slowmode_if_inactive(channel):
  while slowmode_settings.get(channel.id, {}).get("active", False):
    # Wait 5 minutes
    await asyncio.sleep(300)

    data = slowmode_settings.get(channel.id)
    # If the channel’s data was removed or inactive, break
    if not data or not data.get("active", False):
      break

    # If there's been no messages since the last cycle, disable slow mode
    if data["message_count"] == 0:
      await channel.edit(slowmode_delay=0)
      data["active"] = False
      await channel.send("Slow mode disabled due to inactivity.")

    # Reset message count for the next 5-minute window
    data["message_count"] = 0
    save_data(slowmode_settings, "slowmode_settings.json")

@bot.event
async def on_message(message):
  if message.author.bot:
    return

  channel_id = message.channel.id

  user_id = str(message.author.id)

  print(f"User ID: {user_id}")  
  print(f"Current points: {check_points(user_id)}")  
  update_points(user_id, 0.0625)  
  print(f"Updated points: {check_points(user_id)}")  


  # Check if this channel has autoslowmode enabled
  if channel_id in slowmode_settings and slowmode_settings[channel_id]["active"]:
    settings = slowmode_settings[channel_id]
    settings["message_count"] += 1
    elapsed_time = time.time() - settings["last_check"]

    # Check the traffic every 30 seconds
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
    save_data(slowmode_settings, "slowmode_settings.json")

  # Continue processing other commands
  await bot.process_commands(message) # (this made every command run, run twice)
  # return ok msybe i broke it

@bot.command(help="Deactivate auto slow mode in the current channel.",
             usage="7/deactivateautoslowmode", aliases=["dasm"])
@commands.has_permissions(manage_guild=True)
async def deactivateautoslowmode(ctx):
  channel_id = ctx.channel.id

  # Make sure the channel actually has autoslowmode enabled
  if channel_id in slowmode_settings and slowmode_settings[channel_id].get("active"):
    slowmode_settings[channel_id]["active"] = False
    slowmode_settings[channel_id]["message_count"] = 0
    await ctx.channel.edit(slowmode_delay=0)  # Reset slowmode in Discord
    save_data(slowmode_settings, "slowmode_settings.json")

    await ctx.send("Auto slow mode has been **deactivated** for this channel.")
  else:
    await ctx.send("Auto slow mode is not active in this channel.")


sudo_explanation = """
***Info:***
This will copy the display name and the profile picture of a
mentioned user and make it into a fake bot account
that sends a custom specified message.

**Usage:**
`7/sudo <@username> <custom message> {end}`

**Example:**
`7/sudo @7x Hello World!`

***Tip:***
- Don't use a role in place of @username, it will not work.
"""


@bot.command(help="This command impersonates someone",
             usage="7/sudo @username <message>")
@commands.has_permissions(manage_guild=True)  
async def sudo(ctx,
               member: Optional[discord.Member] = None,
               *,
               message: Optional[str] = None):
  if message and message.lower() == "help":
    embed = discord.Embed(title="Sudo Command",
                          description=sudo_explanation,
                          color=0x00ff00)
    await ctx.send(embed=embed)
  elif member is None or message is None:
    await ctx.send(
        "Usage: `7/sudo @user <message>` or `7/sudo help` for more info.")
  elif member and message:
    try:

      await ctx.message.delete()


      webhook = await ctx.channel.create_webhook(name="SudoWebhook")


      avatar_url = member.avatar.url if member.avatar else None


      await webhook.send(content=message,
                         username=member.display_name,
                         avatar_url=avatar_url)


      await webhook.delete()

    except Exception as e:
      await ctx.send(f"An error occurred: {e}")


SLOTS_FILE = "role_slots.json"


MAX_SLOTS = 3


def load_slots():
    if os.path.exists(SLOTS_FILE):
        with open(SLOTS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_slots(slots):
    with open(SLOTS_FILE, 'w') as f:
        json.dump(slots, f, indent=4)

@bot.group(invoke_without_command=True)
async def role(ctx):
    await ctx.send("Usage: 7/role create <role name> <hex color>, 7/role delete <@role>, 7/role list")


@role.command(help="Create a custom cosmetic role. Maximum 3 slots.")
async def create(ctx, role_name: str, role_color: str):
    try:
        user = ctx.author
        guild = ctx.guild
        slots = load_slots()

        user_slots = slots.get(str(user.id), [])
        if len(user_slots) >= MAX_SLOTS:
            await ctx.send(f"{user.mention}, you already have {MAX_SLOTS} custom roles. You need to delete or replace one to create a new one.")
            return


        role_name = role_name.strip('"')[:100]  

        if not role_color.startswith("#") or len(role_color) != 7:
            await ctx.send("Invalid hex color format. Please provide a valid hex color code in the format #RRGGBB.")
            return

        try:
            role_color = discord.Color(int(role_color.lstrip("#"), 16))
        except ValueError:
            await ctx.send("Invalid hex color code. Please provide a valid hex color in the format #RRGGBB.")
            return


        if existing_role := discord.utils.get(guild.roles, name=role_name):
            await ctx.send(f"{user.mention}, the role `{role_name}` already exists.")
            return

        try:
            new_role = await guild.create_role(name=role_name, color=role_color)
        except discord.Forbidden:
            await ctx.send("I don't have permission to create roles.")
            return
        except discord.HTTPException as e:
            await ctx.send(f"Failed to create role: {e}")
            return


        try:
            await user.add_roles(new_role)
        except discord.Forbidden:
            await ctx.send("I don't have permission to assign roles.")
            return
        except discord.HTTPException as e:
            await ctx.send(f"Failed to assign role: {e}")
            return

        user_slots.append(new_role.id)
        slots[str(user.id)] = user_slots
        save_slots(slots)

        await ctx.send(f"{user.mention}, the role `{role_name}` has been created with color `{role_color}` and assigned to you.")
    except Exception as e:
        print(f"Error in role create command: {e}")
        import traceback
        traceback.print_exc()
        await ctx.send("An error occurred while creating the role.")


@role.command(help="Delete one of your custom cosmetic roles.")
async def delete(ctx, role: discord.Role):
    user = ctx.author
    guild = ctx.guild
    slots = load_slots()


    user_slots = slots.get(str(user.id), [])
    if role.id not in user_slots:
        await ctx.send(f"{user.mention}, you did not create the role `{role.name}`, so you cannot delete it.")
        return


    await role.delete()
    user_slots.remove(role.id)
    slots[str(user.id)] = user_slots
    save_slots(slots)

    await ctx.send(f"{user.mention}, the role `{role.name}` has been deleted.")


@role.command(help="List your custom roles and remaining slots.")
async def list(ctx):
    user = ctx.author
    guild = ctx.guild
    slots = load_slots()


    user_slots = slots.get(str(user.id), [])

    embed = discord.Embed(title=f"{user.display_name}'s Custom Roles", color=discord.Color.blue())

    if user_slots:
        for role_id in user_slots:
            role = guild.get_role(role_id)
            embed.add_field(name=role.name, value=f"Color: {role.color}", inline=False)
    else:
        embed.add_field(name="No Custom Roles", value="You have not created any custom roles.", inline=False)

    embed.set_footer(text=f"Slots used: {len(user_slots)}/{MAX_SLOTS}")
    await ctx.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
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

poll_explanation = """
***Info:***
This will create poll that will only accept responses
within a specified amount of time, either with Yes/No or
Multiple Choice questions.

**Usage:**
`7/poll <duration: in seconds> "<custom question>" -yn {end} `
`7/poll <duration: in seconds> "<custom question>" -mc <options 1-10> {end}`

**Example:**
`7/poll 25 "Dogs, Cats, or neither?" -mc dogs cats neither`

***Tip:***
- Don't try to ping a role in the question,
  it will not work, do it beforehand.
"""


@bot.command(help="This command creates a poll",
             usage="7/poll <duration> <question> -yn / -mc <options 1-10>")
@commands.has_permissions(manage_guild=True)
async def poll(ctx, *args):
    if args and args[0].lower() == "help":
      embed = discord.Embed(title="Poll Command",
                            description=poll_explanation,
                            color=0x00ff00)
      await ctx.send(embed=embed)
      return

    if len(args) < 2:
      await ctx.send("Incorrect usage. For detailed help, type: `7/poll help`")
      return

    try:
      duration = int(args[0])
      question = args[1]
    except (ValueError, IndexError):
      await ctx.send("Invalid usage. Please specify a duration and a question.")
      return

    if "-yn" in args:
      options = ["Yes", "No"]
      reactions = ['✅', '❌']
      await ctx.message.delete()
    elif "-mc" in args:
      try:
        mc_index = args.index("-mc") + 1
        question = ' '.join(args[:mc_index - 1])
        options = args[mc_index:]
        if len(options) < 2:
          raise ValueError("Multiple choice polls require at least two options.")
        reactions = [
            '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'
        ][:len(options)]
      except ValueError as e:
        await ctx.send(str(e))
        return
      await ctx.message.delete()
    else:
      await ctx.send("Invalid usage. For detailed help, type: `7/poll help`")
      return

    description = []
    for x, option in enumerate(options):
      description += f'\n{reactions[x]} {option}'
    embed = discord.Embed(title=question, description=''.join(description))
    react_message = await ctx.send(embed=embed)
    for reaction in reactions[:len(options)]:
      await react_message.add_reaction(reaction)

    await asyncio.sleep(duration)
    react_message = await ctx.channel.fetch_message(react_message.id)

    results = {
        str(reaction.emoji): reaction.count - 1
        for reaction in react_message.reactions
        if str(reaction.emoji) in reactions
    }
    winner = max(results.items(), key=lambda x: x[1])[0] if results else None
    results_description = '\n'.join(
        [f'{emoji} - {count} votes' for emoji, count in results.items()])
    results_embed = discord.Embed(
        title=f"The winning option is: {winner} with {results[winner]} votes!",
        description=results_description)
    await ctx.send(embed=results_embed)


if __name__ == "__main__":
  bot.run(my_secret)
