import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import random

class Leveling(commands.Cog):
    """📊 Leveling system to track user activity and engagement"""
    
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns = {}  # Track XP cooldowns
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Give XP for messages"""
        if message.author.bot or not message.guild:
            return
        
        # Check cooldown
        user_key = f"{message.author.id}_{message.guild.id}"
        now = datetime.utcnow()
        
        if user_key in self.xp_cooldowns:
            if now < self.xp_cooldowns[user_key]:
                return
        
        # Set cooldown
        self.xp_cooldowns[user_key] = now + timedelta(seconds=self.bot.config.XP_COOLDOWN)
        
        # Give XP
        xp_gained = random.randint(10, self.bot.config.XP_PER_MESSAGE)
        leveled_up = await self.bot.db.add_xp(message.author.id, message.guild.id, xp_gained)
        
        if leveled_up:
            user_data = await self.bot.db.get_user_level(message.author.id, message.guild.id)
            new_level = user_data['level']
            
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} reached level **{new_level}**!",
                color=self.bot.config.SUCCESS_COLOR
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            await message.channel.send(embed=embed, delete_after=10)
    
    @commands.command(
        name="level",
        description="Check your or someone's current level and XP",
        usage="level [user]",
        aliases=["lvl", "xp"]
    )
    async def level(self, ctx, member: discord.Member = None):
        """Check your or someone's level"""
        member = member or ctx.author
        user_data = await self.bot.db.get_user_level(member.id, ctx.guild.id)
        
        current_xp = user_data['xp']
        current_level = user_data['level']
        
        # Calculate XP needed for next level
        next_level_xp = (current_level + 1) ** 4
        xp_needed = next_level_xp - current_xp
        
        # Calculate progress percentage
        current_level_xp = current_level ** 4
        progress = ((current_xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100
        
        embed = discord.Embed(
            title=f"📊 {member.display_name}'s Level",
            color=self.bot.config.PRIMARY_COLOR
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="Level", value=current_level, inline=True)
        embed.add_field(name="XP", value=f"{current_xp:,}", inline=True)
        embed.add_field(name="XP to Next Level", value=f"{xp_needed:,}", inline=True)
        
        # Progress bar
        filled = int(progress // 10)
        bar = "█" * filled + "░" * (10 - filled)
        embed.add_field(name="Progress", value=f"{bar} {progress:.1f}%", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="levelboard",
        description="Show the top leveled users in the server",
        usage="levelboard",
        aliases=["xlb", "toplevel"]
    )
    async def leaderboard(self, ctx):
        """Show the server leaderboard"""
        results = await self.bot.db.pool.fetch("""
            SELECT user_id, xp, level FROM levels
            WHERE guild_id = $1 ORDER BY xp DESC LIMIT 10
        """, ctx.guild.id)
        
        if not results:
            return await ctx.send("❌ No leveling data found!")
        
        embed = discord.Embed(
            title="🏆 Level Leaderboard",
            color=self.bot.config.PRIMARY_COLOR
        )
        
        leaderboard = []
        for i, record in enumerate(results, 1):
            user_id = record['user_id']
            xp = record['xp']
            level = record['level']
            
            user = self.bot.get_user(user_id)
            name = user.display_name if user else "Unknown User"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard.append(f"{medal} {name} - Level {level} ({xp:,} XP)")
        
        embed.description = "\n".join(leaderboard)
        await ctx.send(embed=embed)
    
    @commands.command(
        name="rank",
        description="Check your server rank based on XP",
        usage="rank [user]"
    )
    async def rank(self, ctx, member: discord.Member = None):
        """Check your server rank"""
        member = member or ctx.author
        
        # Get user's rank
        result = await self.bot.db.pool.fetchrow("""
            SELECT rank FROM (
                SELECT user_id, ROW_NUMBER() OVER (ORDER BY xp DESC) as rank
                FROM levels WHERE guild_id = $1
            ) ranked WHERE user_id = $2
        """, ctx.guild.id, member.id)
        
        if not result:
            return await ctx.send(f"❌ {member.display_name} is not ranked yet!")
        
        rank = result['rank']
        user_data = await self.bot.db.get_user_level(member.id, ctx.guild.id)
        
        embed = discord.Embed(
            title=f"🏅 {member.display_name}'s Rank",
            description=f"Rank: **#{rank}**\nLevel: **{user_data['level']}**\nXP: **{user_data['xp']:,}**",
            color=self.bot.config.PRIMARY_COLOR
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
