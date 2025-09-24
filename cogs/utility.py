from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
import discord
from typing import Optional
from datetime import datetime

def get_uptime():
    """Get bot uptime - needs to be imported from main"""
    from bot_main import bot_start_time
    delta = datetime.now() - bot_start_time
    return str(delta)

def get_build_id():
    """Get build ID"""
    return "v2.0-cogs"

class UtilityCommands(commands.Cog):
    """Basic utility commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True)
    async def beta(self, ctx, option: str = None):
        """Beta command group"""
        if option is None:
            await ctx.send("Please provide a valid option: tester, info")
        elif option == "info":
            await ctx.send(f"Build ID: {get_build_id()} | Uptime: {get_uptime()}")
        elif option == "tester":
            await ctx.invoke(self.bot.get_command('beta tester'))
    
    @commands.group(name="tester", invoke_without_command=True, help="Beta tester management commands.")
    @commands.is_owner()
    async def beta_tester(self, ctx):
        """Beta tester management"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Valid subcommands are: add, remove, list")
    
    @beta_tester.command(name="add")
    async def beta_tester_add(self, ctx, member: discord.Member = None):
        """Add beta tester"""
        if member is None:
            await ctx.send("Please specify a member to add as a beta tester.")
            return
        if role := discord.utils.get(ctx.guild.roles, name="7x Waitlist"):
            await member.add_roles(role)
            await ctx.send(f"Added {member.mention} as a beta tester.")
        else:
            await ctx.send("Role '7x Waitlist' not found.")
    
    @beta_tester.command(name="remove")
    async def beta_tester_remove(self, ctx, member: discord.Member = None):
        """Remove beta tester"""
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
    async def beta_tester_list(self, ctx):
        """List beta testers"""
        if role := discord.utils.get(ctx.guild.roles, name="7x Waitlist"):
            testers = [member.mention for member in role.members]
            await ctx.send("Beta Testers: " + ", ".join(testers))
        else:
            await ctx.send("No beta testers found.")
    
    @commands.command(name="echo")
    async def echo(self, ctx, *args):
        """Echo back the provided message"""
        message = " ".join(args)
        await ctx.send(message)
    
    @commands.command()
    async def cancel(self, ctx, ecancel: bool = False):
        """Toggle ecancel setting"""
        ecancel = not ecancel
        await ctx.send(f"ecancel set to {ecancel}")
    
    @commands.command(name="man")
    async def man_command(self, ctx, *, arg: Optional[str] = None):
        """Manual pages for commands"""
        if arg is None or arg.strip() == "":
            await ctx.send("Please provide a command name to get the manual entry.")
        elif arg.strip() in ['--list', '--l']:
            command_names = [f"`{command.name}`" for command in self.bot.commands]
            command_list = ', '.join(command_names)
            await ctx.send(f"Available commands:\n{command_list}")
        elif command := self.bot.get_command(arg):
            usage_text = command.usage
            if not usage_text or usage_text == "":
                usage_text = f"No detailed usage information available for `{command.name}`."
            embed = discord.Embed(
                title=f"Manual Entry for `{command.name}`",
                description=usage_text,
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No command named '{arg}' found.")
    
    @commands.command(name='tc',
                     ignore_extra=False,
                     help="This command tests if 7x can send a message in a channel.",
                     usage="7/tc")
    async def tc_command(self, ctx, *args):
        """Test channel command"""
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
        if 'help' in args or args:
            embed = discord.Embed(title="TC Command Help",
                                  description=tc_explanation,
                                  color=0x00ff00)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Success")
    
    @commands.command(name="query-status")
    @commands.has_permissions(manage_guild=True)
    async def query_status(self, ctx, *, messages: str):
        """Queue status messages"""
        # Import status_queue from events cog
        events_cog = self.bot.get_cog('BotEvents')
        if events_cog:
            # Split the messages by quotes and filter out any empty strings
            messages_list = [msg for msg in messages.split('"') if msg.strip()]
            # Access the status_queue from events
            from cogs.events import status_queue
            status_queue.extend(messages_list)
            
            await ctx.send(f"Queued {len(messages_list)} statuses.")
        else:
            await ctx.send("Events cog not loaded - cannot queue statuses.")
    
    @commands.command()
    async def derhop(self, ctx, *args):
        """Derhop command"""
        await ctx.send("Derhop is a nerd or something idk")

async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))