import discord
from discord.ext import commands
import asyncio
import sys
import traceback

class Admin(commands.Cog):
    """⚙️ Admin-only commands for bot management and maintenance"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_owner():
        """Check if user is bot owner"""
        async def predicate(ctx):
            return ctx.author.id in ctx.bot.config.OWNER_IDS
        return commands.check(predicate)
    
    @commands.command(
        name="reload",
        description="Reload a specific cog/extension",
        usage="reload <cog_name>"
    )
    @is_owner()
    async def reload_cog(self, ctx, *, cog: str):
        """Reload a cog"""
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            embed = discord.Embed(
                title="✅ Cog Reloaded",
                description=f"Successfully reloaded `{cog}`",
                color=self.bot.config.SUCCESS_COLOR
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Reload Failed",
                description=f"Failed to reload `{cog}`:\n```{str(e)}```",
                color=self.bot.config.ERROR_COLOR
            )
            await ctx.send(embed=embed)
    
    @commands.command(
        name="load",
        description="Load a new cog/extension",
        usage="load <cog_name>"
    )
    @is_owner()
    async def load_cog(self, ctx, *, cog: str):
        """Load a cog"""
        try:
            await self.bot.load_extension(f"cogs.{cog}")
            embed = discord.Embed(
                title="✅ Cog Loaded",
                description=f"Successfully loaded `{cog}`",
                color=self.bot.config.SUCCESS_COLOR
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Load Failed",
                description=f"Failed to load `{cog}`:\n```{str(e)}```",
                color=self.bot.config.ERROR_COLOR
            )
            await ctx.send(embed=embed)
    
    @commands.command(
        name="unload",
        description="Unload a cog/extension",
        usage="unload <cog_name>"
    )
    @is_owner()
    async def unload_cog(self, ctx, *, cog: str):
        """Unload a cog"""
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
            embed = discord.Embed(
                title="✅ Cog Unloaded",
                description=f"Successfully unloaded `{cog}`",
                color=self.bot.config.SUCCESS_COLOR
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unload Failed",
                description=f"Failed to unload `{cog}`:\n```{str(e)}```",
                color=self.bot.config.ERROR_COLOR
            )
            await ctx.send(embed=embed)
    
    @commands.command(
        name="shutdown",
        description="Safely shutdown the bot",
        usage="shutdown"
    )
    @is_owner()
    async def shutdown(self, ctx):
        """Shutdown the bot"""
        embed = discord.Embed(
            title="🔌 Shutting Down",
            description="Bot is shutting down...",
            color=self.bot.config.WARNING_COLOR
        )
        await ctx.send(embed=embed)
        await self.bot.close()
    
    @commands.command(
        name="eval",
        description="Evaluate Python code (dangerous - owner only)",
        usage="eval <code>"
    )
    @is_owner()
    async def eval_code(self, ctx, *, code: str):
        """Evaluate Python code"""
        if code.startswith("```python"):
            code = code[9:-3]
        elif code.startswith("```"):
            code = code[3:-3]
        
        try:
            result = eval(code)
            if asyncio.iscoroutine(result):
                result = await result
            
            embed = discord.Embed(
                title="✅ Evaluation Result",
                description=f"```python\n{result}\n```",
                color=self.bot.config.SUCCESS_COLOR
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Evaluation Error",
                description=f"```python\n{str(e)}\n```",
                color=self.bot.config.ERROR_COLOR
            )
            await ctx.send(embed=embed)
    
    @commands.command(
        name="sql",
        description="Execute SQL query on the database",
        usage="sql <query>"
    )
    @is_owner()
    async def execute_sql(self, ctx, *, query: str):
        """Execute SQL query"""
        if query.startswith("```sql"):
            query = query[6:-3]
        elif query.startswith("```"):
            query = query[3:-3]
        
        try:
            if query.strip().upper().startswith("SELECT"):
                results = await self.bot.db.pool.fetch(query)
                if results:
                    output = "\n".join([str(dict(record)) for record in results[:5]])
                    if len(results) > 5:
                        output += f"\n... and {len(results) - 5} more rows"
                else:
                    output = "No results"
            else:
                await self.bot.db.pool.execute(query)
                output = "Query executed successfully"
            
            embed = discord.Embed(
                title="✅ SQL Result",
                description=f"```\n{output}\n```",
                color=self.bot.config.SUCCESS_COLOR
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ SQL Error",
                description=f"```\n{str(e)}\n```",
                color=self.bot.config.ERROR_COLOR
            )
            await ctx.send(embed=embed)
    
    @commands.command(
        name="guilds",
        description="List all guilds the bot is in",
        usage="guilds"
    )
    @is_owner()
    async def list_guilds(self, ctx):
        """List all guilds the bot is in"""
        guilds = self.bot.guilds
        
        embed = discord.Embed(
            title=f"🏰 Bot Guilds ({len(guilds)})",
            color=self.bot.config.PRIMARY_COLOR
        )
        
        guild_list = []
        for guild in guilds[:10]:  # Show first 10
            guild_list.append(f"{guild.name} ({guild.id}) - {guild.member_count} members")
        
        if len(guilds) > 10:
            guild_list.append(f"... and {len(guilds) - 10} more guilds")
        
        embed.description = "\n".join(guild_list)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
