# Migration Guide: Monolithic to Cog System

This guide explains how to complete the migration of remaining functionality from the original monolithic `7xbot.py` to the new cog system.

## Migration Status

### ✅ **Completed**
- Core bot infrastructure and cog loading system
- Admin commands (shutdown, eval, repl, debug)
- Basic utility commands (tc, echo, man, beta management)
- Points system and shop functionality
- Event handlers (on_ready, on_message, error handling)
- Database utilities and shared functions
- Restart monitoring system
- Documentation and examples

### 🔄 **Partially Migrated** (Placeholders Created)
- AI functionality (`cogs/ai.py`)
- Moderation system (`cogs/moderation.py`) 
- Channel management (`cogs/channel_management.py`)

### 📋 **Remaining to Migrate**

#### From Original `7xbot.py` Lines ~900-1950:

1. **Full AI System** (lines 901-1050)
   - Complex AI chat functionality with multiple models
   - Flag parsing (`-s`, `-search`, `-model`)
   - NotDiamond API integration
   - Web search capabilities
   - Response formatting and chunking

2. **Complete Moderation System** (lines 436-570)
   - Strike/warning system with role escalation
   - Filler spam command
   - Warning and pardon commands with database tracking
   - Lockdown mode implementation
   - Spam ping detection

3. **Full Channel Management** (lines 1132-1560)
   - HTTP command with complex deletion logic
   - Message scanning and AI-based flagging
   - Bulk message transfer between channels
   - Auto-slowmode with traffic monitoring
   - Message fetching and processing utilities

4. **Role Management System** (lines 1700-1850)
   - Custom role creation with color support
   - Role slot limitations (3 slots per user)
   - Role deletion and cleanup
   - Role slots persistence

5. **Poll System** (lines 1885-1950)
   - Yes/No and multiple choice polls
   - Timed poll management
   - Vote collection and results

## Migration Instructions

### Step 1: AI System Migration

```python
# Move from 7xbot.py lines 901-1050 to cogs/ai.py
# Key components to migrate:
- parse_flags_and_content() function
- AI model integration (NotDiamond, g4f)
- Web search functionality
- Response chunking logic
- Model selection and routing
```

### Step 2: Moderation System Migration

```python
# Move from 7xbot.py lines 436-570 to cogs/moderation.py
# Key components to migrate:
- strike_roles array
- warn() command with role escalation
- pardon() command with database updates
- lockdown() implementation
- fillerspam() development tool
```

### Step 3: Channel Management Migration

```python
# Move from 7xbot.py lines 1132-1560 to cogs/channel_management.py
# Key components to migrate:
- http() command with all deletion modes
- AI message scanning functions
- Message transfer utilities
- Auto-slowmode traffic monitoring
- Data persistence functions
```

### Step 4: Role Management Migration

```python
# Create new cogs/roles.py
# Move from 7xbot.py lines 1700-1850
# Key components to migrate:
- role() command group
- Custom role creation logic
- Role slot management (SLOTS_FILE)
- Color validation and parsing
- Role cleanup on deletion
```

### Step 5: Poll System Migration

```python
# Create new cogs/polls.py or add to utility.py
# Move from 7xbot.py lines 1885-1950
# Key components to migrate:
- poll() command with timing
- Yes/No and multiple choice modes
- Vote collection via reactions
- Results calculation and display
```

## Migration Process

For each system:

1. **Extract Functions**: Copy relevant functions from `7xbot.py`
2. **Update Imports**: Add necessary imports to the cog file
3. **Adapt to Cog Structure**: Wrap in cog class and use `self.bot`
4. **Update Database Access**: Use shared database utilities from `cogs/database.py`
5. **Test Functionality**: Use `7/reload_cog <name>` to test changes
6. **Update Documentation**: Add commands to help system

## Example Migration Template

```python
# cogs/example.py
from discord.ext import commands
import discord
from .database import load_db, save_db

class ExampleCog(commands.Cog):
    """Description of cog functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        # Initialize any cog-specific data
        self.example_data = {}
    
    @commands.command()
    async def example_command(self, ctx, arg: str):
        """Example command implementation"""
        # Migrated functionality here
        await ctx.send(f"Example: {arg}")
    
    # Helper functions (previously global functions)
    def example_helper(self, data):
        """Helper function migrated from original file"""
        return processed_data

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
```

## Testing Migration

1. **Syntax Check**: `python3 -m py_compile cogs/new_cog.py`
2. **Load Test**: Use `7/load_cog new_cog` in Discord
3. **Functionality Test**: Test all commands in the cog
4. **Reload Test**: Use `7/reload_cog new_cog` to verify hot-reloading
5. **Integration Test**: Ensure cog works with other cogs

## Benefits After Full Migration

- **No Downtime Updates**: Fix any component without bot restart
- **Feature Toggles**: Disable problematic features instantly
- **Development Isolation**: Work on features independently
- **Better Testing**: Test individual components in isolation
- **Cleaner Codebase**: Logical organization of related functionality

## Rollback Plan

The original `7xbot.py` file is preserved and can be used as a fallback:

```bash
# Emergency rollback to monolithic system
mv bot_main.py bot_main.py.backup
mv 7xbot.py bot_main.py
python3 bot_main.py
```

## Priority Order

1. **AI System** - Most complex, highest impact
2. **Moderation** - Critical for server management
3. **Channel Management** - Important admin tools
4. **Role Management** - User-facing features
5. **Poll System** - Nice-to-have functionality

This migration can be done incrementally, with each cog providing immediate benefits as it's completed.