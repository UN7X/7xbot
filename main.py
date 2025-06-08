import discord
from discord.ext import commands
import asyncio
import logging
import os
from datetime import datetime
import aiohttp
import json
from config import Config
from database import Database

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log') if not os.getenv('HEROKU', False) else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)

class AdvancedBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True
        )
        
        self.config = Config()
        self.db = Database()
        self.session = None
        self.start_time = datetime.utcnow()
        
    async def get_prefix(self, message):
        """Dynamic prefix system"""
        if not message.guild:
            return commands.when_mentioned_or(self.config.DEFAULT_PREFIX)(self, message)
        
        prefix = await self.db.get_guild_prefix(message.guild.id)
        return commands.when_mentioned_or(prefix or self.config.DEFAULT_PREFIX)(self, message)

    
    async def setup_hook(self):
        """Setup hook called when bot starts"""
        self.session = aiohttp.ClientSession()
        await self.db.setup()
        
        # Load all cogs - only the ones that exist
        cogs = [
            'cogs.moderation',
            'cogs.music',
            'cogs.fun',
            'cogs.utility',
            'cogs.economy',
            'cogs.leveling',
            'cogs.admin',
            'cogs.games',
            'cogs.automod'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logging.info(f'✅ Loaded {cog}')
            except Exception as e:
                logging.error(f'❌ Failed to load {cog}: {e}')
    
    async def on_ready(self):
        """Called when bot is ready"""
        logging.info(f'🤖 {self.user} has connected to Discord!')
        logging.info(f'📊 Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | {self.config.DEFAULT_PREFIX}help"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Called when bot joins a guild"""
        await self.db.setup_guild(guild.id)
        logging.info(f'➕ Joined guild: {guild.name} ({guild.id})')
        
        # Send welcome message
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(
                    title="🎉 Thanks for adding me!",
                    description=f"Use `{self.config.DEFAULT_PREFIX}help` to get started!\n\nI'm a feature-rich bot with moderation, music, economy, games, and more!",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🚀 Quick Start",
                    value=f"• `{self.config.DEFAULT_PREFIX}help` - View all commands\n• `{self.config.DEFAULT_PREFIX}ping` - Check bot latency\n• `{self.config.DEFAULT_PREFIX}serverinfo` - Server information",
                    inline=False
                )
                await channel.send(embed=embed)
                break
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions!")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.2f}s")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param}`")
        else:
            logging.error(f'❌ Unhandled error in {ctx.command}: {error}')
            await ctx.send("❌ An unexpected error occurred!")
    
    async def close(self):
        """Cleanup when bot shuts down"""
        logging.info("🔌 Bot shutting down...")
        if self.session:
            await self.session.close()
        await self.db.close()
        await super().close()

    async def on_message(self, message):
        if not message.author.bot:
            print(f"Received message: {message.content} from {message.author}")
            await bot.process_commands(message)



if __name__ == "__main__":
    bot = AdvancedBot()
    
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logging.error("❌ DISCORD_TOKEN environment variable not found!")
        exit(1)
    
    try:
        bot.run(token)
    except Exception as e:
        logging.error(f"❌ Failed to start bot: {e}")
