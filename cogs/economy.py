import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
import asyncio

class Economy(commands.Cog):
    """💰 Economy system with currency, jobs, gambling, and trading"""
    
    def __init__(self, bot):
        self.bot = bot
        self.currency = "💰"
    
    @commands.command(
        name="balance",
        description="Check your or someone's balance",
        usage="balance [user]",
        aliases=["bal", "money"]
    )
    async def balance(self, ctx, member: discord.Member = None):
        """Check your or someone's balance"""
        member = member or ctx.author
        balance_data = await self.bot.db.get_balance(member.id, ctx.guild.id)
        
        embed = discord.Embed(
            title=f"{member.display_name}'s Balance",
            color=self.bot.config.PRIMARY_COLOR
        )
        embed.add_field(name="Wallet", value=f"{self.currency} {balance_data['balance']:,}", inline=True)
        embed.add_field(name="Bank", value=f"{self.currency} {balance_data['bank']:,}", inline=True)
        embed.add_field(name="Total", value=f"{self.currency} {balance_data['balance'] + balance_data['bank']:,}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="daily",
        description="Claim your daily reward (24 hour cooldown)",
        usage="daily"
    )
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hours
    async def daily(self, ctx):
        """Claim your daily reward"""
        reward = self.bot.config.DAILY_REWARD
        await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, reward)
        
        embed = discord.Embed(
            title="💰 Daily Reward",
            description=f"You claimed your daily reward of {self.currency} {reward:,}!",
            color=self.bot.config.SUCCESS_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="work",
        description="Work to earn money (1 hour cooldown)",
        usage="work"
    )
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 hour
    async def work(self, ctx):
        """Work to earn money"""
        jobs = [
            "programmer", "teacher", "doctor", "chef", "artist", "musician",
            "writer", "engineer", "scientist", "designer", "photographer"
        ]
        
        job = random.choice(jobs)
        reward = random.randint(self.bot.config.WORK_REWARD_MIN, self.bot.config.WORK_REWARD_MAX)
        
        await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, reward)
        
        embed = discord.Embed(
            title="💼 Work Complete",
            description=f"You worked as a {job} and earned {self.currency} {reward:,}!",
            color=self.bot.config.SUCCESS_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="rob",
        description="Attempt to rob another user (2 hour cooldown)",
        usage="rob <user>"
    )
    @commands.cooldown(1, 7200, commands.BucketType.user)  # 2 hours
    async def rob(self, ctx, member: discord.Member):
        """Attempt to rob another user"""
        if member == ctx.author:
            return await ctx.send("❌ You can't rob yourself!")
        
        if member.bot:
            return await ctx.send("❌ You can't rob bots!")
        
        target_balance = await self.bot.db.get_balance(member.id, ctx.guild.id)
        
        if target_balance['balance'] < 100:
            return await ctx.send(f"❌ {member.display_name} doesn't have enough money to rob!")
        
        success_chance = 0.3  # 30% success rate
        
        if random.random() < success_chance:
            # Successful robbery
            stolen = min(target_balance['balance'] // 4, 1000)  # Max 25% or 1000
            
            await self.bot.db.update_balance(member.id, ctx.guild.id, -stolen)
            await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, stolen)
            
            embed = discord.Embed(
                title="🔫 Robbery Successful",
                description=f"You successfully robbed {self.currency} {stolen:,} from {member.display_name}!",
                color=self.bot.config.SUCCESS_COLOR
            )
        else:
            # Failed robbery - lose money
            fine = min(await self.bot.db.get_balance(ctx.author.id, ctx.guild.id)['balance'] // 10, 500)
            
            if fine > 0:
                await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, -fine)
            
            embed = discord.Embed(
                title="🚨 Robbery Failed",
                description=f"You got caught and paid a fine of {self.currency} {fine:,}!",
                color=self.bot.config.ERROR_COLOR
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="gamble",
        description="Gamble your money with a chance to win or lose",
        usage="gamble <amount|all|half>",
        aliases=["bet"]
    )
    async def gamble(self, ctx, amount: str):
        """Gamble your money"""
        balance_data = await self.bot.db.get_balance(ctx.author.id, ctx.guild.id)
        
        if amount.lower() == "all":
            bet_amount = balance_data['balance']
        elif amount.lower() == "half":
            bet_amount = balance_data['balance'] // 2
        else:
            try:
                bet_amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Invalid amount! Use a number, 'all', or 'half'")
        
        if bet_amount <= 0:
            return await ctx.send("❌ You need to bet a positive amount!")
        
        if bet_amount > balance_data['balance']:
            return await ctx.send("❌ You don't have enough money!")
        
        # 45% chance to win, 55% chance to lose
        if random.random() < 0.45:
            # Win
            winnings = int(bet_amount * 1.8)  # 80% profit
            await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, winnings - bet_amount)
            
            embed = discord.Embed(
                title="🎰 You Won!",
                description=f"You bet {self.currency} {bet_amount:,} and won {self.currency} {winnings:,}!",
                color=self.bot.config.SUCCESS_COLOR
            )
        else:
            # Lose
            await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, -bet_amount)
            
            embed = discord.Embed(
                title="💸 You Lost!",
                description=f"You bet {self.currency} {bet_amount:,} and lost it all!",
                color=self.bot.config.ERROR_COLOR
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="deposit",
        description="Deposit money from wallet to bank",
        usage="deposit <amount|all>",
        aliases=["dep"]
    )
    async def deposit(self, ctx, amount: str):
        """Deposit money to your bank"""
        balance_data = await self.bot.db.get_balance(ctx.author.id, ctx.guild.id)
        
        if amount.lower() == "all":
            deposit_amount = balance_data['balance']
        else:
            try:
                deposit_amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Invalid amount!")
        
        if deposit_amount <= 0:
            return await ctx.send("❌ You need to deposit a positive amount!")
        
        if deposit_amount > balance_data['balance']:
            return await ctx.send("❌ You don't have enough money in your wallet!")
        
        # Move money from wallet to bank
        async with self.bot.db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE economy SET balance = balance - $1, bank = bank + $1
                WHERE user_id = $2 AND guild_id = $3
            """, deposit_amount, ctx.author.id, ctx.guild.id)
        
        embed = discord.Embed(
            title="🏦 Deposit Successful",
            description=f"Deposited {self.currency} {deposit_amount:,} to your bank!",
            color=self.bot.config.SUCCESS_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="withdraw",
        description="Withdraw money from bank to wallet",
        usage="withdraw <amount|all>",
        aliases=["with"]
    )
    async def withdraw(self, ctx, amount: str):
        """Withdraw money from your bank"""
        balance_data = await self.bot.db.get_balance(ctx.author.id, ctx.guild.id)
        
        if amount.lower() == "all":
            withdraw_amount = balance_data['bank']
        else:
            try:
                withdraw_amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Invalid amount!")
        
        if withdraw_amount <= 0:
            return await ctx.send("❌ You need to withdraw a positive amount!")
        
        if withdraw_amount > balance_data['bank']:
            return await ctx.send("❌ You don't have enough money in your bank!")
        
        # Move money from bank to wallet
        async with self.bot.db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE economy SET balance = balance + $1, bank = bank - $1
                WHERE user_id = $2 AND guild_id = $3
            """, withdraw_amount, ctx.author.id, ctx.guild.id)
        
        embed = discord.Embed(
            title="💰 Withdrawal Successful",
            description=f"Withdrew {self.currency} {withdraw_amount:,} from your bank!",
            color=self.bot.config.SUCCESS_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="pay",
        description="Pay money to another user",
        usage="pay <user> <amount>",
        aliases=["give", "transfer"]
    )
    async def pay(self, ctx, member: discord.Member, amount: int):
        """Pay money to another user"""
        if member == ctx.author:
            return await ctx.send("❌ You can't pay yourself!")
        
        if member.bot:
            return await ctx.send("❌ You can't pay bots!")
        
        if amount <= 0:
            return await ctx.send("❌ You need to pay a positive amount!")
        
        balance_data = await self.bot.db.get_balance(ctx.author.id, ctx.guild.id)
        
        if amount > balance_data['balance']:
            return await ctx.send("❌ You don't have enough money!")
        
        await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, -amount)
        await self.bot.db.update_balance(member.id, ctx.guild.id, amount)
        
        embed = discord.Embed(
            title="💸 Payment Sent",
            description=f"You paid {self.currency} {amount:,} to {member.display_name}!",
            color=self.bot.config.SUCCESS_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="leaderboard",
        description="Show the richest users in the server",
        usage="leaderboard",
        aliases=["lb", "rich", "top"]
    )
    async def leaderboard(self, ctx):
        """Show the richest users in the server"""
        results = await self.bot.db.pool.fetch("""
            SELECT user_id, balance + bank as total FROM economy
            WHERE guild_id = $1 ORDER BY total DESC LIMIT 10
        """, ctx.guild.id)
        
        if not results:
            return await ctx.send("❌ No economy data found!")
        
        embed = discord.Embed(
            title="💰 Richest Users",
            color=self.bot.config.PRIMARY_COLOR
        )
        
        leaderboard = []
        for i, record in enumerate(results, 1):
            user_id = record['user_id']
            total = record['total']
            user = self.bot.get_user(user_id)
            name = user.display_name if user else "Unknown User"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard.append(f"{medal} {name}: {self.currency} {total:,}")
        
        embed.description = "\n".join(leaderboard)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
