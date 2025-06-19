import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import datetime
import platform
import psutil
import os
import math

class HelpView(discord.ui.View):
    """Paginated help view with buttons"""
    
    def __init__(self, bot, ctx, cogs_data):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.cogs_data = cogs_data
        self.current_page = 0
        self.max_pages = len(cogs_data)
    
    def create_embed(self):
        """Create embed for current page"""
        if self.current_page == 0:
            # Main help page
            embed = discord.Embed(
                title="📖 Bot Help Menu",
                description=f"Use the buttons below to navigate or use `{self.ctx.prefix}help <category>` for specific categories.",
                color=self.bot.config.PRIMARY_COLOR
            )
            
            for cog_name, cog_info in self.cogs_data.items():
                if cog_name == "Main":
                    continue
                embed.add_field(
                    name=f"{cog_info['emoji']} {cog_name}",
                    value=f"{cog_info['description']}\n`{self.ctx.prefix}help {cog_name.lower()}`",
                    inline=True
                )
            
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages + 1} • Use {self.ctx.prefix}help <command> for detailed info")
        else:
            # Category page
            cog_name = list(self.cogs_data.keys())[self.current_page - 1]
            cog_info = self.cogs_data[cog_name]
            
            embed = discord.Embed(
                title=f"{cog_info['emoji']} {cog_name} Commands",
                description=cog_info['description'],
                color=self.bot.config.PRIMARY_COLOR
            )
            
            for cmd in cog_info['commands']:
                embed.add_field(
                    name=f"`{self.ctx.prefix}{cmd['name']}`",
                    value=f"{cmd['description']}\n**Usage:** `{self.ctx.prefix}{cmd['usage']}`",
                    inline=False
                )
            
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages + 1}")
        
        return embed
    
    @discord.ui.button(label='◀️', style=discord.ButtonStyle.gray)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Only the command user can navigate!", ephemeral=True)
        
        self.current_page = (self.current_page - 1) % (self.max_pages + 1)
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='🏠', style=discord.ButtonStyle.green)
    async def home_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Only the command user can navigate!", ephemeral=True)
        
        self.current_page = 0
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='▶️', style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Only the command user can navigate!", ephemeral=True)
        
        self.current_page = (self.current_page + 1) % (self.max_pages + 1)
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label='❌', style=discord.ButtonStyle.red)
    async def close_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Only the command user can navigate!", ephemeral=True)
        
        await interaction.response.edit_message(content="Help menu closed.", embed=None, view=None)

class Utility(commands.Cog):
    """🔧 Utility commands for server information and tools"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(
        name="ping",
        description="Check the bot's latency and response time",
        usage="ping",
        aliases=["latency"]
    )
    async def ping(self, ctx):
        """Check the bot's latency"""
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {round(self.bot.latency * 1000)}ms",
            color=self.bot.config.PRIMARY_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="serverinfo",
        description="Get detailed information about the current server",
        usage="serverinfo",
        aliases=["si", "guildinfo"]
    )
    async def server_info(self, ctx):
        """Get information about the server"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Server Info",
            color=self.bot.config.PRIMARY_COLOR,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        # Basic info
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        
        # Channels
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Categories", value=categories, inline=True)
        
        # Other info
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        
        embed.set_footer(text=f"Server ID: {guild.id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="userinfo",
        description="Get detailed information about a user",
        usage="userinfo [user]",
        aliases=["ui", "whois"]
    )
    async def user_info(self, ctx, member: discord.Member = None):
        """Get information about a user"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color if member.color != discord.Color.default() else self.bot.config.PRIMARY_COLOR,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Basic info
        embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        
        # Dates
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        
        # Roles
        if len(member.roles) > 1:
            roles = [role.mention for role in member.roles[1:]]  # Skip @everyone
            if len(roles) > 10:
                roles = roles[:10] + [f"... and {len(roles) - 10} more"]
            embed.add_field(name="Roles", value=" ".join(roles), inline=False)
        
        embed.set_footer(text=f"User ID: {member.id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="avatar",
        description="Get a user's avatar in full resolution",
        usage="avatar [user]",
        aliases=["av", "pfp"]
    )
    async def avatar(self, ctx, member: discord.Member = None):
        """Get a user's avatar"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=self.bot.config.PRIMARY_COLOR
        )
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="Download", value=f"[Click here]({member.display_avatar.url})", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="botinfo",
        description="Get information about the bot and its statistics",
        usage="botinfo",
        aliases=["about", "stats"]
    )
    async def botinfo(self, ctx):
        """Get information about the bot"""
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=self.bot.config.PRIMARY_COLOR,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Basic info
        embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        
        # Uptime
        uptime = datetime.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
        
        # System info
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="invite",
        description="Get the bot's invite link to add it to other servers",
        usage="invite"
    )
    async def invite(self, ctx):
        """Get the bot's invite link"""
        permissions = discord.Permissions(
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            add_reactions=True,
            connect=True,
            speak=True,
            manage_messages=True,
            kick_members=True,
            ban_members=True,
            manage_roles=True,
            moderate_members=True
        )
        
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        
        embed = discord.Embed(
            title="📨 Invite Me!",
            description=f"[Click here to invite me to your server!]({invite_url})",
            color=self.bot.config.SUCCESS_COLOR
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="prefix",
        description="View or change the server's command prefix",
        usage="prefix [new_prefix]"
    )
    async def prefix(self, ctx, new_prefix: str = None):
        """View or change the server prefix"""
        if new_prefix is None:
            current_prefix = await self.bot.db.get_guild_prefix(ctx.guild.id) or self.bot.config.DEFAULT_PREFIX
            embed = discord.Embed(
                title="🔧 Server Prefix",
                description=f"Current prefix: `{current_prefix}`",
                color=self.bot.config.PRIMARY_COLOR
            )
            await ctx.send(embed=embed)
        else:
            if not ctx.author.guild_permissions.manage_guild:
                return await ctx.send("❌ You need 'Manage Server' permission to change the prefix!")
            
            if len(new_prefix) > 5:
                return await ctx.send("❌ Prefix cannot be longer than 5 characters!")
            
            await self.bot.db.set_guild_prefix(ctx.guild.id, new_prefix)
            
            embed = discord.Embed(
                title="✅ Prefix Changed",
                description=f"Server prefix changed to: `{new_prefix}`",
                color=self.bot.config.SUCCESS_COLOR
            )
            await ctx.send(embed=embed)
    
    @commands.command(
        name="help",
        description="Show help information for commands and categories",
        usage="help [command/category]"
    )
    async def help_command(self, ctx, *, query: str = None):
        """Show help information"""
        if query:
            # Check if it's a specific command
            command = self.bot.get_command(query.lower())
            if command:
                embed = discord.Embed(
                    title=f"📖 Help: {command.name}",
                    description=command.description or "No description available",
                    color=self.bot.config.PRIMARY_COLOR
                )
                
                if hasattr(command, 'usage'):
                    embed.add_field(name="Usage", value=f"`{ctx.prefix}{command.usage}`", inline=False)
                else:
                    embed.add_field(name="Usage", value=f"`{ctx.prefix}{command.name} {command.signature}`", inline=False)
                
                if command.aliases:
                    embed.add_field(name="Aliases", value=", ".join([f"`{alias}`" for alias in command.aliases]), inline=False)
                
                return await ctx.send(embed=embed)
            
            # Check if it's a category
            cog = self.bot.get_cog(query.title())
            if cog:
                embed = discord.Embed(
                    title=f"📖 {cog.qualified_name} Commands",
                    description=cog.description or "No description available",
                    color=self.bot.config.PRIMARY_COLOR
                )
                
                commands_list = []
                for cmd in cog.get_commands():
                    if not cmd.hidden:
                        usage = getattr(cmd, 'usage', f"{cmd.name} {cmd.signature}")
                        commands_list.append(f"`{ctx.prefix}{usage}` - {cmd.description or 'No description'}")
                
                if commands_list:
                    # Split into chunks if too long
                    chunk_size = 10
                    for i in range(0, len(commands_list), chunk_size):
                        chunk = commands_list[i:i + chunk_size]
                        embed.add_field(
                            name=f"Commands ({i+1}-{min(i+chunk_size, len(commands_list))})",
                            value="\n".join(chunk),
                            inline=False
                        )
                
                return await ctx.send(embed=embed)
            
            return await ctx.send(f"❌ No command or category found for `{query}`")
        
        # General help with pagination
        cogs_data = {}
        
        for cog_name, cog in self.bot.cogs.items():
            if cog_name in ['Jishaku', 'Help']:  # Skip internal cogs
                continue
            
            commands_list = []
            for cmd in cog.get_commands():
                if not cmd.hidden:
                    commands_list.append({
                        'name': cmd.name,
                        'description': cmd.description or 'No description',
                        'usage': getattr(cmd, 'usage', f"{cmd.name} {cmd.signature}")
                    })
            
            if commands_list:
                # Get emoji from cog description
                emoji = "🔧"
                if "🛡️" in cog.description: emoji = "🛡️"
                elif "🎵" in cog.description: emoji = "🎵"
                elif "🎮" in cog.description: emoji = "🎮"
                elif "💰" in cog.description: emoji = "💰"
                elif "📊" in cog.description: emoji = "📊"
                elif "⚙️" in cog.description: emoji = "⚙️"
                elif "🎯" in cog.description: emoji = "🎯"
                elif "🤖" in cog.description: emoji = "🤖"
                
                cogs_data[cog_name] = {
                    'emoji': emoji,
                    'description': cog.description or 'No description',
                    'commands': commands_list
                }
        
        if not cogs_data:
            return await ctx.send("❌ No commands available!")
        
        view = HelpView(self.bot, ctx, cogs_data)
        embed = view.create_embed()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Utility(bot))
