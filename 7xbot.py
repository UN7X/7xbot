import asyncio
import base64
import json
import time
import os
import random
import string
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import discord
from discord.channel import TextChannel
import openai
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument, has_any_role

load_dotenv()


#If you can see this, the git commit worked.

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

status_hold = False
temporary_status = None
temporary_status_time = None
ecancel = False
shutdown_in_progress = False
status_queue = []
new_status = f"{days_until_christmas()} Days until Christmas!"
status_hold = False
my_secret = os.getenv('BOT_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ND_API_KEY = os.getenv('ND_API_KEY')
openai.api_key = OPENAI_API_KEY
fallback_model = "gpt-3.5-turbo-1106"
def get_build_id():
  # This could be a Git commit hash, tag, or a simple counter
  return "v1.0.123"
os.system('cls' if os.name == 'nt' else 'clear')

tips = [
    "Did you know? Of course you didn't.", "Run 7/help for help", "Made by UN7X",
    "Thank you to 7x's beta testers!", "Want your message on here? Ping @UN7X",
    "Hiya!", "Blaze_is_Tiny = True", "Hello, world!", ":3", "I'm alive!", "You", "For 7/ commands", "awa"
]

intents = discord.Intents.default()
intents.message_content = True  # Ensure this is set to True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("7/"),
                   intents=intents,
                   case_insensitive=True,
                   help_command=None)

@bot.group(invoke_without_command=True)
async def beta(ctx, option: str = None):
    if option is None:
        await ctx.send("Please provide a valid option: tester, info")
    elif option == "info":
        await ctx.send(f"Build ID: {get_build_id()} | Uptime: {get_uptime()}")
    elif option == "tester":
        await ctx.invoke(bot.get_command('beta tester'))

@bot.group(name="tester", invoke_without_command=True)
@commands.is_owner()
async def beta_tester(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("Valid subcommands are: add, remove, list")
@beta_tester.command(name="add")
async def beta_tester_add(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Please specify a member to add as a beta tester.")
        return
    role = discord.utils.get(ctx.guild.roles, name="7x Waitlist")
    if role:
        await member.add_roles(role)
        await ctx.send(f"Added {member.mention} as a beta tester.")
    else:
        await ctx.send("Role '7x Waitlist' not found.")

@beta_tester.command(name="remove")
async def beta_tester_remove(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Please specify a member to remove from beta testers.")
        return
    role = discord.utils.get(ctx.guild.roles, name="7x Waitlist")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"Removed {member.mention} from beta testers.")
    else:
        await ctx.send(f"{member.mention} is not a tester.")

@beta_tester.command(name="list")
async def beta_tester_list(ctx):
    role = discord.utils.get(ctx.guild.roles, name="7x Waitlist")
    if role:
        testers = [member.mention for member in role.members]
        await ctx.send("Beta Testers: " + ", ".join(testers))
    else:
        await ctx.send("No beta testers found.")

@bot.command(name="query-status")
@commands.has_permissions(manage_guild=True)
async def query_status(ctx, *, messages: str):
    global status_queue

    # Split the messages by quotes and filter out any empty strings
    messages_list = [msg for msg in messages.split('"') if msg.strip()]
    status_queue.extend(messages_list)

    await ctx.send(f"Queued {len(messages_list)} statuses.")

@bot.command(name="force-status")
@commands.has_permissions(manage_guild=True)
async def force_status(ctx, *, status: str):
  global status_hold, temporary_status, temporary_status_time

  # Check for the '-indf' flag
  if '-indf' in status:
    status_hold = True  # Hold this status indefinitely
    status = status.replace('-indf', '').strip()  # Clean the status message
  else:
    status_hold = False  # Do not hold status indefinitely

  # Update the bot's presence
  await bot.change_presence(activity=discord.Activity(
      type=discord.ActivityType.watching, name=status))

  # If not indefinite, set a temporary status and record the time
  if not status_hold:
    temporary_status = status
    temporary_status_time = datetime.now()
    await asyncio.sleep(10)  # Wait for 10 seconds before clearing the temporary status
    temporary_status = None
    temporary_status_time = None

  await ctx.send(f"Status changed to: {status}")


async def change_status_task():
  global status_hold, temporary_status, temporary_status_time, status_queue
  last_status = None

  while True:
    if temporary_status and (datetime.now() - temporary_status_time).seconds > 10:
      temporary_status = None

    if status_hold:
      await asyncio.sleep(10)
    elif temporary_status:
      await bot.change_presence(activity=discord.Activity(
          type=discord.ActivityType.watching, name=temporary_status))
      await asyncio.sleep(10)
    elif status_queue:
      next_status = status_queue.pop(0)
      await bot.change_presence(activity=discord.Activity(
          type=discord.ActivityType.watching, name=next_status))
      await asyncio.sleep(10)
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
    # Add more items as needed
}


@bot.command(name="shop")
async def shop(ctx):
  embed = discord.Embed(title="7x Shop",
                        description="Available items to purchase with points:",
                        color=0x00ff00)
  for item_id, details in shop_items.items():
    embed.add_field(name=f"{item_id} - {details['price']} points",
                    value=details['description'],
                    inline=False)
  await ctx.send(embed=embed)


@bot.command(
    name="fillerspam",
    aliases=["fs"],
    help="Creates a channel and generates spam test messages. DEVS ONLY")
@has_any_role("mod")
async def filler_spam(ctx):

  new_channel = await ctx.guild.create_text_channel("test-http-channel")

  for _ in range(10):
    gibberish = ''.join(
        random.choices(string.ascii_letters + string.digits, k=20))
    await new_channel.send(gibberish)

  await ctx.send(
      f"Channel {new_channel.mention} created and filled with test messages.")

# Define strike roles in order
strike_roles = [
    "Warning 1", 
    "Warning 2", 
    "Warning 3", 
    "Time out warning 1",  # 10 minutes
    "Time out warning 2",  # 1 hour
    "Time out warning 3",  # 1 day
    "Kick warning 1", 
    "Ban on Sight"
]

@bot.command(help="Warn a user and escalate their strike.")
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    guild = ctx.guild
    current_role = None
    
    # Identify user's current warning role
    for role in member.roles:
        if role.name in strike_roles:
            current_role = role
            break

    # Find the next role in the strike list
    if current_role is None:
        next_role = discord.utils.get(guild.roles, name="Warning 1")
    else:
        current_index = strike_roles.index(current_role.name)
        next_role_name = strike_roles[min(current_index + 1, len(strike_roles) - 1)]
        next_role = discord.utils.get(guild.roles, name=next_role_name)

    # Remove previous role, if any
    if current_role:
        await member.remove_roles(current_role)

    # Add the next role
    await member.add_roles(next_role)
    await ctx.send(f"{member.mention} has been warned and given the role: {next_role.name} for: {reason}")

    # Handle special actions for specific roles
    if next_role.name == "Time out warning 1":
        await member.timeout_for(minutes=10)
    elif next_role.name == "Time out warning 2":
        await member.timeout_for(hours=1)
    elif next_role.name == "Time out warning 3":
        await member.timeout_for(days=1)
    elif next_role.name == "Kick warning 1":
        await member.kick(reason=f"Accumulated strikes: {reason}")
    elif next_role.name == "Ban on Sight":
        await member.ban(reason=f"Accumulated strikes: {reason}")

    # Log the warning to the audit log
    await ctx.guild.audit_logs(reason=f"Warned {member.display_name}: {reason}")

# 7/pardon command implementation
@bot.command(help="Reverse the last warning of a user.")
@commands.has_permissions(manage_messages=True)
async def pardon(ctx, member: discord.Member):
    guild = ctx.guild
    current_role = None

    # Find the current strike role of the user
    for role in member.roles:
        if role.name in strike_roles:
            current_role = role
            break

    # If no current warning role, cannot pardon
    if current_role is None:
        await ctx.send(f"{member.mention} has no warnings to pardon.")
        return

    # Determine the previous role (if any)
    current_index = strike_roles.index(current_role.name)
    if current_index == 0:
        await member.remove_roles(current_role)
        await ctx.send(f"{member.mention} has been fully pardoned. They now have no warning roles.")
    else:
        previous_role_name = strike_roles[current_index - 1]
        previous_role = discord.utils.get(guild.roles, name=previous_role_name)

        # Remove the current role and apply the previous one
        await member.remove_roles(current_role)
        if previous_role:
            await member.add_roles(previous_role)
            await ctx.send(f"{member.mention} has been pardoned and demoted to {previous_role.name}.")
        else:
            await ctx.send(f"{member.mention} has been pardoned. They now have no warning roles.")

@bot.command(help="Initiate or deactivate lockdown mode.")
@commands.has_permissions(administrator=True)
async def lockdown(ctx, action: str):
    guild = ctx.guild

    if action.lower() == "initiate":
        for channel in guild.text_channels:
            await channel.edit(slowmode_delay=10)  # Set slow mode to 10 seconds

        invites = await guild.invites()
        for invite in invites:
            await invite.delete()  # Delete all active invites

        await ctx.send("Lockdown initiated. All invites have been paused, and slow mode is set to 10 seconds for all channels.")
    
    elif action.lower() == "deactivate":
        for channel in guild.text_channels:
            await channel.edit(slowmode_delay=0)  # Reset slow mode

        await ctx.send("Lockdown deactivated. Channels are back to normal.")
    else:
        await ctx.send("Invalid action. Use 'initiate' or 'deactivate'.")

@bot.command(name="spamping",
             help="Spam pings a user a specfied amount.",
             usage="7/spam-ping <user> <amount>")
@has_any_role("mod", "7x Waitlist")
async def spamping(ctx,
                   member: Optional[discord.Member] = None,
                   *,
                   ping_count: Optional[int] = None):
  await ctx.message.delete()

  if member is None:
    await ctx.send("Please specify a user to ping.")
    return

  if ping_count is None:
    ping_count = 5
  if ping_count > 25:
    ping_count = 25
  for i in range(ping_count):
    if ecancel is False:
      await ctx.send(f"{member.mention} | {i+1}/{ping_count} Pings left")
      await asyncio.sleep(1)
    else:
      await ctx.send("Spam pings cancelled.")
      return


@bot.command()
async def cancel(ctx, ecancel: bool = False):
  if ecancel is True:
    ecancel = False
  elif ecancel is False:
    ecancel = True
  else:
    await ctx.send("Invalid option.")
    return
  await ctx.send(f"ecancel set to {ecancel}")


@bot.command(name="help")
async def help_command(ctx):
  embed = discord.Embed(title="7x Command List",
                        description="List of available commands:",
                        color=0x00ff00)
  for command in bot.commands:
    command_usage = f"7/{command.name} {' ' + command.usage if command.usage else ''}"  # Correct command usage display
    embed.add_field(name=command_usage,
                    value=command.help or "No description provided.",
                    inline=False)
  await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, MissingRequiredArgument):
    command = ctx.command
    await ctx.send(f"""
        Missing required argument for {command.name}: {error.param.name}. Usage: {command.usage}
        """)


tc_explanation = """
***Info:***
This will make 7x send a "Success" message to check
if 7x can send a message in that channel.

**Usage:**
`7/tc {end}`

**Example:**
`7/tc`

***Tip:***
- Don't try to add any arguments, none, except help, are supported.
"""


@bot.command(name='TC',
             ignore_extra=False,
             help="This command tests if 7x can send a message in a channel.",
             usage="7/tc")
async def tc_command(ctx, *args):
  if 'help' in args or len(args) > 0:
    embed = discord.Embed(title="TC Command Help",
                          description=tc_explanation,
                          color=0x00ff00)
    await ctx.send(embed=embed)
  else:
    await ctx.send("Success")


@bot.command()
@commands.is_owner()
async def shutdown(ctx, *args):
  global shutdown_in_progress

  if '-e' in args:
    await ctx.send("Emergency Shutdown Bypass: Activated | Force Quiting All Running Services...")
    await bot.close()

  if shutdown_in_progress:
    shutdown_in_progress = False
    await ctx.send("Shutdown sequence halted.")
    return

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


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name}')
  print(f'With ID: {bot.user.id}')
  print('------')
  bot.loop.create_task(change_status_task())
  channel = bot.get_channel(1300600203442913290)
  if isinstance(channel, TextChannel):
      await channel.send("7x - Now listening for commands!")



# Function to encode images in Base64
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    print(f"Encoding image {image_path}")
    return base64.b64encode(image_file.read()).decode("utf-8")


# Function to save messages to Database
def save_message(guild_id, user_id, message):
  key = f"{guild_id}-{user_id}"
  messages = db.get(key, [])
  messages.append(message)
  db[key] = messages
  print(messages)


# Function to retrieve messages from Database
def get_messages(guild_id, user_id):
  key = f"{guild_id}-{user_id}"
  print(f"Key: {key}")
  return db.get(key, [])




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
@commands.has_permissions(manage_guild=True)  # Changed to manage server permission
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
    # Store channel info
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
      # Transfer messages
      await transfer_messages(ctx, channel, target_channel, args)

    if "-rm" in args or "-rmc" in args or "-rmc.trf" in args:
      await channel.delete(reason="7/http command with -rm, -rmc or -rmc.trf flag")

      if "-rmc" in args or "-rmc.trf" in args:
        await channel_category.create_text_channel(
          name=channel_name,
          topic=channel_topic,
          position=channel_position,
          reason="7/http command with -rmc or -rmc.trf flag")

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

@bot.command()
@commands.is_owner()
async def test_fetch(ctx, source: discord.TextChannel, limit: int = 2):
  try:
    # Check Permissions
    if not source.permissions_for(ctx.me).read_message_history:
      await ctx.send("I don't have permission to read the message history.")
      return
    if not source.permissions_for(ctx.me).read_messages:
      await ctx.send("I don't have permission to read messages in the source channel.")
      return

    await ctx.send(f"Attempting to fetch {limit} messages from {source.mention}...")

    # Fetch messages using async for (since flatten is no longer valid)
    print("Fetching messages...")
    messages = []
    async for message in source.history(limit=limit):
      messages.append(message)

    if not messages:
      await ctx.send("No messages were fetched.")
      return

    # Print each message to debug
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

  # Create a list to store fetched messages
  messages = []
  async for message in source_channel.history(limit=limit):
    messages.append(message)
  if not messages:
    await ctx.send("No messages found in the source channel.")
    return


  print("Fetched messages successfully")
  messages.reverse()

  # Transfer each message
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

@bot.command(help="Logs deleted messages for moderation purposes.",
             usage="7/logger <activation length (-indf or -num)>")
@commands.has_permissions(manage_guild=True)
async def logger(ctx, activation_length: str):
    # Logging toggle
    logging_enabled = False

    # Open the log file in append mode
    log_filename = f"{ctx.guild.name}_deleted_logs.txt"
    with open(log_filename, "a") as log_file:
        # Check if indefinite or timed logging is requested
        if activation_length.startswith("-indf"):
            logging_enabled = True
            print("Logger activated indefinitely.")
        elif activation_length.startswith("-num"):
            try:
                minutes = int(activation_length[4:])
                logging_enabled = True
                print(f"Logger activated for {minutes} minutes.")
                await asyncio.sleep(minutes * 60)  # Log for the specified time
                logging_enabled = False
                print("Logging stopped after the time limit.")
            except ValueError:
                await ctx.send("Invalid logging time. Please enter a valid number.")

        # Event listener for deleted messages
        @bot.event
        async def on_message_delete(message):
            if logging_enabled:
                try:
                    # Log message details directly to file
                    log_entry = f"{message.author} ({message.author.id}) at {message.created_at} in {message.channel.name}: {message.content}\n"
                    log_file.write(log_entry)
                    log_file.flush()  # Ensures that each log entry is written immediately
                except Exception as e:
                    print(f"Error while logging message: {e}")

    # End message once the log is done or interrupted
    if not logging_enabled:
        print(f"Logging stopped. Log saved to {log_filename}.")

# Save dictionary to a JSON file
def save_data(data, filename="data.json"):
  with open(filename, 'w') as f:
    json.dump(data, f)

# Load data from a JSON file if it exists
def load_data(filename="data.json"):
  try:
    if os.path.exists(filename):
      with open(filename, 'r') as f:
        return json.load(f)
    return {}
  except FileNotFoundError:
     with open(filename, 'w') as f:
        return {}


slowmode_settings = load_data("slowmode_settings.json")  # Retrieve saved slow mode settings
print("Loaded slow mode settings:", slowmode_settings)

@bot.command(help="Automatically enables slow mode when message traffic is high.",
             usage="7/autoslowmode <mpm> <slowmode amount>")
@commands.has_permissions(manage_guild=True)
async def autoslowmode(ctx, mpm: int, slowmode_amount: int = 5):
    # Register slow mode settings for the current channel
    slowmode_settings[ctx.channel.id] = {
        "mpm": mpm,
        "slowmode_amount": slowmode_amount,
        "message_count": 0,
        "last_check": time.time(),
        "active": True
    }
    save_data(slowmode_settings[ctx.channel.id], "slowmode_settings.json")

    await ctx.send(f"Auto slowmode activated: {mpm} messages per 30 seconds. Slow mode will be set to {slowmode_amount} seconds.")
 
    # Reset the slow mode to the normal value after 10 minutes if activity drops
    await reset_slowmode_if_inactive(ctx.channel)

# Function to check if the channel is still active
async def reset_slowmode_if_inactive(channel):
    while slowmode_settings.get(channel.id, {}).get("active", False):
        await asyncio.sleep(300)  # Check every 5 minutes

        if slowmode_settings[channel.id]["message_count"] == 0:
            await channel.edit(slowmode_delay=0)  # Disable slow mode if no activity
            slowmode_settings[channel.id]["active"] = False
            await channel.send("Slow mode disabled due to inactivity.")
        else:
            slowmode_settings[channel.id]["message_count"] = 0  # Reset counter for next interval

# Monitor message traffic
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    channel_id = message.channel.id

    # Check if auto-slowmode is enabled in this channel
    if channel_id in slowmode_settings and slowmode_settings[channel_id]["active"]:
        settings = slowmode_settings[channel_id]

        # Increment the message count and check if it exceeds the mpm threshold
        settings["message_count"] += 1
        elapsed_time = time.time() - settings["last_check"]

        if elapsed_time >= 30:  # Half a minute has passed
            if settings["message_count"] > settings["mpm"]:
                # Apply slow mode to the channel
                await message.channel.edit(slowmode_delay=settings["slowmode_amount"])
                await message.channel.send(f"Slow mode activated: {settings['slowmode_amount']} second slowmode due to high activity.")
           
            # Reset for the next minute
            settings["message_count"] = 0
            settings["last_check"] = time.time()

    await bot.process_commands(message)  # Ensure other commands are processed


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
@commands.has_permissions(manage_guild=True)  # Check for Manage Server permissions
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
      # Delete the command message first
      await ctx.message.delete()

      # Create a webhook
      webhook = await ctx.channel.create_webhook(name="SudoWebhook")

      # Check if the member has an avatar and get the URL
      avatar_url = member.avatar.url if member.avatar else None

      # Send the message through the webhook
      await webhook.send(content=message,
                         username=member.display_name,
                         avatar_url=avatar_url)

      # Delete the webhook immediately after sending the message
      await webhook.delete()

    except Exception as e:
      await ctx.send(f"An error occurred: {e}")


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

  results = {}
  for reaction in react_message.reactions:
    if str(reaction.emoji) in reactions:
      results[str(reaction.emoji)] = reaction.count - 1

  winner = max(results.items(), key=lambda x: x[1])[0] if results else None
  results_description = '\n'.join(
      [f'{emoji} - {count} votes' for emoji, count in results.items()])
  results_embed = discord.Embed(
      title=f"The winning option is: {winner} with {results[winner]} votes!",
      description=results_description)
  await ctx.send(embed=results_embed)


bot.run(my_secret)



