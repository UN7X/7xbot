import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from typing import Optional

class Moderation(commands.Cog):
    """🛡️ Moderation commands for server management and user discipline"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(
        name="kick",
        description="Kick a member from the server",
        usage="kick <member> [reason]"
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ You cannot kick someone with a higher or equal role!")
        
        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("❌ I cannot kick someone with a higher or equal role!")
        
        try:
            await member.send(f"You have been kicked from {ctx.guild.name}. Reason: {reason}")
        except:
            pass
        
        await member.kick(reason=f"{ctx.author}: {reason}")
        
        embed = discord.Embed(
            title="Member Kicked",
            description=f"{member.mention} has been kicked",
            color=self.bot.config.WARNING_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="ban",
        description="Ban a member from the server",
        usage="ban <member> [reason]"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ You cannot ban someone with a higher or equal role!")
        
        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("❌ I cannot ban someone with a higher or equal role!")
        
        try:
            await member.send(f"You have been banned from {ctx.guild.name}. Reason: {reason}")
        except:
            pass
        
        await member.ban(reason=f"{ctx.author}: {reason}")
        
        embed = discord.Embed(
            title="Member Banned",
            description=f"{member.mention} has been banned",
            color=self.bot.config.ERROR_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="unban",
        description="Unban a user from the server",
        usage="unban <user_id> [reason]"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Unban a user from the server"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
            
            embed = discord.Embed(
                title="User Unbanned",
                description=f"{user.mention} has been unbanned",
                color=self.bot.config.SUCCESS_COLOR,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("❌ User not found or not banned!")
    
    @commands.command(
        name="mute",
        description="Mute a member using Discord's timeout feature",
        usage="mute <member> [duration] [reason]",
        aliases=["timeout"]
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: Optional[str] = None, *, reason: str = "No reason provided"):
        """Mute a member (timeout)"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ You cannot mute someone with a higher or equal role!")
        
        # Parse duration
        if duration:
            time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            try:
                duration_seconds = int(duration[:-1]) * time_dict[duration[-1]]
                until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
            except (ValueError, KeyError):
                return await ctx.send("❌ Invalid duration format! Use: 10s, 5m, 2h, 1d")
        else:
            until = discord.utils.utcnow() + timedelta(minutes=10)  # Default 10 minutes  # Default 10 minutes
        try:
            await member.timeout(until, reason=f"{ctx.author}: {reason}")
        except discord.Forbidden:
            return await ctx.send("❌ That person is either the server owner, or too powerful for me to mute!")
        
        embed = discord.Embed(
            title="Member Muted",
            description=f"{member.mention} has been muted",
            color=self.bot.config.WARNING_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Duration", value=f"Until <t:{int(until.timestamp())}:R>", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="unmute",
        description="Remove timeout from a member",
        usage="unmute <member> [reason]",
        aliases=["untimeout"]
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Unmute a member"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ You cannot unmute someone with a higher or equal role!")
        try:
            await member.timeout(None, reason=f"{ctx.author}: {reason}")
        except discord.Forbidden:
            return await ctx.send("❌ Either that person is the server owner, or too powerful for me to unmute!")

        embed = discord.Embed(
            title="Member Unmuted",
            description=f"{member.mention} has been unmuted",
            color=self.bot.config.SUCCESS_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="warn",
        description="Give a warning to a member",
        usage="warn <member> [reason]"
    )
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member"""
        await self.bot.db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        
        try:
            await member.send(f"You have been warned in {ctx.guild.name}. Reason: {reason}")
        except:
            pass
        
        embed = discord.Embed(
            title="Member Warned",
            description=f"{member.mention} has been warned",
            color=self.bot.config.WARNING_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="warnings",
        description="View a member's warning history",
        usage="warnings <member>",
        aliases=["warns"]
    )
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        """View a member's warnings"""
        warnings = await self.bot.db.get_warnings(ctx.guild.id, member.id)
        
        if not warnings:
            return await ctx.send(f"{member.mention} has no warnings!")
        
        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            color=self.bot.config.WARNING_COLOR
        )
        
        for i, warning in enumerate(warnings[:10], 1):  # Show last 10 warnings
            moderator = self.bot.get_user(warning["moderator_id"])
            mod_name = moderator.display_name if moderator else "Unknown"
            
            embed.add_field(
                name=f"Warning #{warning['id']}",
                value=f"**Reason:** {warning['reason']}\n**Moderator:** {mod_name}\n**Date:** {warning['timestamp'][:10]}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="clear",
        description="Clear messages from the channel",
        usage="clear [amount]",
        aliases=["purge", "delete"]
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        """Clear messages from the channel"""
        if amount > 100:
            return await ctx.send("❌ Cannot delete more than 100 messages at once!")
        
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for the command message
        
        embed = discord.Embed(
            title="Messages Cleared",
            description=f"Deleted {len(deleted) - 1} messages",
            color=self.bot.config.SUCCESS_COLOR
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()

async def setup(bot):
    await bot.add_cog(Moderation(bot))
