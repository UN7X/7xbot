# 7xBot Cog System Migration

This document explains the new cog-based architecture of 7xBot v2.0.

## Overview

The monolithic `7xbot.py` file has been restructured into a modular cog system that allows for:

- **Runtime reloading** of individual bot components without restarting
- **Selective enabling/disabling** of bot features
- **Better code organization** and maintainability  
- **Emergency restart capability** with external script monitoring

## File Structure

```
7xbot/
├── bot_main.py              # New main bot entry point
├── 7xbot.py                 # Original monolithic file (preserved)
├── restart_bot.sh           # Bot restart monitoring script
├── .env.example             # Environment variables template
├── cogs/
│   ├── __init__.py
│   ├── admin.py             # Owner commands (shutdown, eval, repl)
│   ├── ai.py                # AI functionality (placeholder)
│   ├── channel_management.py # Channel/message management
│   ├── database.py          # Shared database utilities
│   ├── events.py            # Event handlers (on_ready, on_message, etc.)
│   ├── moderation.py        # Moderation commands
│   ├── points.py            # Points system and shop
│   └── utility.py           # Basic utility commands
└── test_cogs.py            # Cog system testing script
```

## Usage

### Starting the Bot

1. **Standard startup:**
   ```bash
   python3 bot_main.py
   ```

2. **With restart monitoring:**
   ```bash
   ./restart_bot.sh &
   python3 bot_main.py
   ```

### Cog Management Commands

All cog management commands are owner-only:

- **Load a cog:** `7/load_cog <cog_name>`
- **Unload a cog:** `7/unload_cog <cog_name>`  
- **Reload a cog:** `7/reload_cog <cog_name>`
- **List loaded cogs:** `7/list_cogs`
- **Restart entire bot:** `7/restart_bot`

### Examples

```bash
# Reload the admin cog after making changes
7/reload_cog admin

# Temporarily disable AI functionality
7/unload_cog ai

# List all currently loaded cogs
7/list_cogs

# Emergency restart the entire bot process
7/restart_bot
```

## Cog Descriptions

### admin.py
**Owner-only administrative commands:**
- `7/shutdown` - Graceful bot shutdown with countdown
- `7/eval` - Execute Python code
- `7/repl` - Interactive Python REPL in Discord
- `7/debug` - Debug command for testing

### utility.py  
**Basic utility commands:**
- `7/tc` - Test channel connectivity
- `7/echo` - Echo messages
- `7/man` - Command manual/help
- `7/beta` - Beta tester management
- `7/cancel` - Toggle ecancel setting
- `7/derhop` - Fun command

### points.py
**Points system and shop:**
- `7/points add/remove/query` - Manage user points
- `7/shop` - Display purchasable items

### events.py
**Event handlers:**
- `on_ready` - Bot startup with status rotation
- `on_message` - Message processing and points awarding
- `on_command_error` - Error handling
- `on_guild_role_delete` - Role cleanup

### AI, Moderation, Channel Management
**Currently contain placeholder implementations** - the full functionality from the original monolithic file can be migrated to these cogs as needed.

## Migration Benefits

1. **Hot Reloading:** Fix bugs or add features without bot downtime
2. **Selective Disabling:** Turn off problematic features instantly
3. **Development Flexibility:** Work on individual components in isolation
4. **Emergency Recovery:** Full bot restart capability via external monitoring
5. **Code Organization:** Logical separation of concerns

## Restart System

The `restart_bot.sh` script provides a monitoring system that:

1. Watches for a `restart_flag` file
2. Kills the Python bot process when flag is detected
3. Waits for cleanup, then restarts the bot
4. Logs all restart activity to `bot_restart.log`

This allows the `7/restart_bot` command to trigger a complete process restart without manual intervention.

## Environment Setup

1. Copy `.env.example` to `.env`
2. Fill in your Discord bot token and API keys
3. Ensure Python dependencies are installed from `requirements.txt`

## Backward Compatibility

The original `7xbot.py` file is preserved for reference and emergency fallback. The new system maintains all existing command functionality while adding the modular architecture benefits.

## Development Workflow

1. Make changes to individual cog files
2. Use `7/reload_cog <cog_name>` to test changes instantly
3. Use `7/list_cogs` to verify loaded modules
4. Use `7/restart_bot` for full restart if needed

This system transforms 7xBot from a monolithic application into a flexible, maintainable, and hot-reloadable Discord bot framework.