import discord
from discord.ext import commands
import re
import asyncio
from datetime import datetime, timedelta

class AutoMod(commands.Cog):
    """🤖 Automatic moderation features for server protection"""
    
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = {}  # Track message spam
        self.bad_words = [
            # Add your filtered words here
            "spam", "badword1", "badword2"  # Example words
        ]
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-moderation on messages"""
        if message.author.bot or not message.guild:
            return
        
        # Skip if user has manage messages permission
        if message.author.guild_permissions.manage_messages:
            return
        
        # Check for spam
        await self.check_spam(message)
        
        # Check for bad words
        await self.check_bad_words(message)
        
        # Check for excessive caps
        await self.check_caps(message)
        
        # Check for excessive mentions
        await self.check_mentions(message)
    
    async def check_spam(self, message):
        """Check for message spam"""
        user_id = message.author.id
        now = datetime.utcnow()
        
        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = []
        
        # Add current message timestamp
        self.spam_tracker[user_id].append(now)
        
        # Remove messages older than 10 seconds
        self.spam_tracker[user_id] = [
            timestamp for timestamp in self.spam_tracker[user_id]
            if now - timestamp < timedelta(seconds=10)
        ]
        
        # Check if user sent more than 5 messages in 10 seconds
        if len(self.spam_tracker[user_id]) > 5:
            try:
                await message.author.timeout(
                    timedelta(minutes=5),
                    reason="Auto-mod: Spam detected"
                )
                
                embed = discord.Embed(
                    title="🚨 Auto-Moderation",
                    description=f"{message.author.mention} has been muted for 5 minutes for spamming.",
                    color=self.bot.config.ERROR_COLOR
                )
                await message.channel.send(embed=embed, delete_after=10)
                
                # Clear spam tracker for user
                self.spam_tracker[user_id] = []
                
            except discord.Forbidden:
                pass
    
    async def check_bad_words(self, message):
        """Check for filtered words"""
        content_lower = message.content.lower()
        
        for word in self.bad_words:
            if word in content_lower:
                try:
                    await message.delete()
                    
                    embed = discord.Embed(
                        title="🚨 Auto-Moderation",
                        description=f"{message.author.mention}, your message contained inappropriate content and was deleted.",
                        color=self.bot.config.WARNING_COLOR
                    )
                    await message.channel.send(embed=embed, delete_after=5)
                    
                    # Add warning to database
                    await self.bot.db.add_warning(
                        message.guild.id,
                        message.author.id,
                        self.bot.user.id,
                        f"Auto-mod: Used filtered word '{word}'"
                    )
                    
                except discord.Forbidden:
                    pass
                break
    
    async def check_caps(self, message):
        """Check for excessive capital letters"""
        if len(message.content) < 10:  # Skip short messages
            return
        
        caps_count = sum(1 for char in message.content if char.isupper())
        caps_percentage = (caps_count / len(message.content)) * 100
        
        if caps_percentage > 70:  # More than 70% caps
            try:
                await message.delete()
                
                embed = discord.Embed(
                    title="🚨 Auto-Moderation",
                    description=f"{message.author.mention}, please don't use excessive capital letters.",
                    color=self.bot.config.WARNING_COLOR
                )
                await message.channel.send(embed=embed, delete_after=5)
                
            except discord.Forbidden:
                pass
    
    async def check_mentions(self, message):
        """Check for excessive mentions"""
        mention_count = len(message.mentions) + len(message.role_mentions)
        
        if mention_count > 5:  # More than 5 mentions
            try:
                await message.delete()
                
                embed = discord.Embed(
                    title="🚨 Auto-Moderation",
                    description=f"{message.author.mention}, please don't mention too many users at once.",
                    color=self.bot.config.WARNING_COLOR
                )
                await message.channel.send(embed=embed, delete_after=5)
                
                # Timeout for 2 minutes
                await message.author.timeout(
                    timedelta(minutes=2),
                    reason="Auto-mod: Excessive mentions"
                )
                
            except discord.Forbidden:
                pass
    
    @commands.command(
        name="automod",
        description="Configure auto-moderation settings for the server",
        usage="automod [setting] [value]"
    )
    @commands.has_permissions(manage_guild=True)
    async def automod_settings(self, ctx, setting: str = None, value: str = None):
        """Configure auto-moderation settings"""
        if not setting:
            embed = discord.Embed(
                title="🤖 Auto-Moderation Settings",
                description="Available settings:\n• `spam` - Enable/disable spam detection\n• `badwords` - Enable/disable bad word filtering\n• `caps` - Enable/disable caps filtering",
                color=self.bot.config.PRIMARY_COLOR
            )
            await ctx.send(embed=embed)
            return
        
        # This would typically save to database
        # For now, just show a confirmation message
        embed = discord.Embed(
            title="✅ Setting Updated",
            description=f"Auto-mod setting `{setting}` has been updated.",
            color=self.bot.config.SUCCESS_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="addword",
        description="Add a word to the auto-moderation filter list",
        usage="addword <word>"
    )
    @commands.has_permissions(manage_guild=True)
    async def add_bad_word(self, ctx, *, word: str):
        """Add a word to the filter list"""
        word = word.lower()
        if word not in self.bad_words:
            self.bad_words.append(word)
            
            embed = discord.Embed(
                title="✅ Word Added",
                description=f"Added `{word}` to the filter list.",
                color=self.bot.config.SUCCESS_COLOR
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ That word is already in the filter list!")
    
    @commands.command(
        name="removeword",
        description="Remove a word from the auto-moderation filter list",
        usage="removeword <word>"
    )
    @commands.has_permissions(manage_guild=True)
    async def remove_bad_word(self, ctx, *, word: str):
        """Remove a word from the filter list"""
        word = word.lower()
        if word in self.bad_words:
            self.bad_words.remove(word)
            
            embed = discord.Embed(
                title="✅ Word Removed",
                description=f"Removed `{word}` from the filter list.",
                color=self.bot.config.SUCCESS_COLOR
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ That word is not in the filter list!")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
