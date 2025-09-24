#!/usr/bin/env python3
"""Simple test script to verify cog loading works"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bot_main import CogBot

async def test_cog_loading():
    """Test that cogs can be loaded without errors"""
    print("Testing cog system...")
    
    # Create bot instance  
    bot = CogBot()
    
    # Test loading individual cogs
    cogs_to_test = [
        'cogs.admin',
        'cogs.utility', 
        'cogs.points',
        'cogs.events',
        'cogs.ai',
        'cogs.moderation',
        'cogs.channel_management'
    ]
    
    for cog in cogs_to_test:
        try:
            await bot.load_extension(cog)
            print(f"✓ {cog} loaded successfully")
        except Exception as e:
            print(f"✗ {cog} failed to load: {e}")
    
    # List loaded cogs
    print(f"\nLoaded cogs: {list(bot.cogs.keys())}")
    
    # Test unloading
    try:
        await bot.unload_extension('cogs.admin')
        print("✓ Cog unloading works")
    except Exception as e:
        print(f"✗ Cog unloading failed: {e}")
    
    # Test reloading
    try:
        await bot.load_extension('cogs.admin')
        print("✓ Cog reloading works")
    except Exception as e:
        print(f"✗ Cog reloading failed: {e}")
    
    await bot.close()
    print("\nCog system test completed!")

if __name__ == "__main__":
    asyncio.run(test_cog_loading())