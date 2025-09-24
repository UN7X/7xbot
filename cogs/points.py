from discord.ext import commands
import discord
from typing import Optional
from .database import load_db, save_db

# Shop items configuration
shop_items = {
    'item1': {
        'price': 100,
        'description': 'Item 1 Description'
    },
    'item2': {
        'price': 200,  
        'description': 'Item 2 Description'
    },
    # placeholder for later updates
}

class PointsSystem(commands.Cog):
    """Points and shop system"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def check_points(self, user_id):
        """Check user points"""
        print("Checking points...")
        db = load_db()
        return db.get(f"points_{user_id}", 0)
    
    def set_points(self, user_id, points):
        """Set user points"""
        db = load_db()
        db[f"points_{user_id}"] = points
        save_db(db)
        print(f"Set points for user {user_id} to {points}")
    
    def update_points(self, user_id, points):
        """Update user points"""
        current_points = self.check_points(user_id)
        new_points = max(current_points + points, 0)
        self.set_points(user_id, new_points)
        print(f"Updated points for user {user_id} to {new_points}")
    
    @commands.group(invoke_without_command=True)
    async def points(self, ctx):
        """Points management commands"""
        await ctx.send("Usage: `7/points <add/remove/query> <@user> [amount]`")
    
    @points.command()
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx, member: discord.Member, amount: int):
        """Add points to a user"""
        user_id = str(member.id)
        self.update_points(user_id, amount)
        await ctx.send(f"Added {amount} points to {member.mention}. They now have {self.check_points(user_id)} points.")
    
    @points.command()
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx, member: discord.Member, amount: int):
        """Remove points from a user"""
        user_id = str(member.id)
        self.update_points(user_id, -amount)
        await ctx.send(f"Removed {amount} points from {member.mention}. They now have {self.check_points(user_id)} points.")
    
    @points.command()
    async def query(self, ctx, member: Optional[discord.Member] = None):
        """Query user points"""
        if member is None:
            member = ctx.author
        user_id = str(member.id)
        points = self.check_points(user_id)
        await ctx.send(f"{member.mention} has {points} points.")
    
    @commands.command(name="shop")
    async def shop(self, ctx):
        """Display the shop"""
        embed = discord.Embed(title="7x Shop",
                              description="Available items to purchase with points:",
                              color=0x00ff00)
        for item_id, details in shop_items.items():
            embed.add_field(name=f"{item_id} - {details['price']} points",
                            value=details['description'],
                            inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PointsSystem(bot))