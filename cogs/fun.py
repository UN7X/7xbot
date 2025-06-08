import discord
from discord.ext import commands
import random
import aiohttp
import asyncio
from datetime import datetime

class Fun(commands.Cog):
    """🎮 Fun commands for entertainment and games"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(
        name="8ball",
        description="Ask the magic 8-ball a question and get a mystical answer",
        usage="8ball <question>"
    )
    async def eight_ball(self, ctx, *, question: str):
        """Ask the magic 8-ball a question"""
        responses = [
            "It is certain", "It is decidedly so", "Without a doubt",
            "Yes definitely", "You may rely on it", "As I see it, yes",
            "Most likely", "Outlook good", "Yes", "Signs point to yes",
            "Reply hazy, try again", "Ask again later", "Better not tell you now",
            "Cannot predict now", "Concentrate and ask again",
            "Don't count on it", "My reply is no", "My sources say no",
            "Outlook not so good", "Very doubtful"
        ]
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=self.bot.config.PRIMARY_COLOR
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(responses), inline=False)
        embed.set_footer(text=f"Asked by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="flip",
        description="Flip a coin and see if it lands on heads or tails",
        usage="flip",
        aliases=["coinflip", "coin"]
    )
    async def flip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🔄"
        
        embed = discord.Embed(
            title=f"{emoji} Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=self.bot.config.PRIMARY_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="roll",
        description="Roll a dice with specified number of sides",
        usage="roll [sides]",
        aliases=["dice"]
    )
    async def roll(self, ctx, sides: int = 6):
        """Roll a dice"""
        if sides < 2:
            return await ctx.send("❌ Dice must have at least 2 sides!")
        
        if sides > 100:
            return await ctx.send("❌ Dice can't have more than 100 sides!")
        
        result = random.randint(1, sides)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled a **{result}** on a {sides}-sided dice!",
            color=self.bot.config.PRIMARY_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="choose",
        description="Choose between multiple options (separate with commas)",
        usage="choose <option1, option2, option3...>",
        aliases=["pick", "decide"]
    )
    async def choose(self, ctx, *, choices: str):
        """Choose between multiple options (separate with commas)"""
        options = [choice.strip() for choice in choices.split(',')]
        
        if len(options) < 2:
            return await ctx.send("❌ Please provide at least 2 choices separated by commas!")
        
        chosen = random.choice(options)
        
        embed = discord.Embed(
            title="🤔 Choice Made",
            description=f"I choose: **{chosen}**",
            color=self.bot.config.PRIMARY_COLOR
        )
        embed.add_field(name="Options", value=", ".join(options), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="joke",
        description="Get a random joke to brighten your day",
        usage="joke"
    )
    async def joke(self, ctx):
        """Get a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why can't a bicycle stand up by itself? It's two tired!",
            "What do you call a fish wearing a bowtie? Sofishticated!",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus!"
        ]
        
        embed = discord.Embed(
            title="😂 Random Joke",
            description=random.choice(jokes),
            color=self.bot.config.PRIMARY_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="meme",
        description="Get a random meme from Reddit",
        usage="meme"
    )
    async def meme(self, ctx):
        """Get a random meme"""
        try:
            async with self.bot.session.get('https://meme-api.herokuapp.com/gimme') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    embed = discord.Embed(
                        title=data['title'],
                        url=data['postLink'],
                        color=self.bot.config.PRIMARY_COLOR
                    )
                    embed.set_image(url=data['url'])
                    embed.set_footer(text=f"👍 {data['ups']} | r/{data['subreddit']}")
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Couldn't fetch a meme right now!")
        except Exception as e:
            await ctx.send("❌ Error fetching meme!")
    
    @commands.command(
        name="fact",
        description="Get a random interesting fact",
        usage="fact"
    )
    async def fact(self, ctx):
        """Get a random fact"""
        try:
            async with self.bot.session.get('https://uselessfacts.jsph.pl/random.json?language=en') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    embed = discord.Embed(
                        title="🧠 Random Fact",
                        description=data['text'],
                        color=self.bot.config.PRIMARY_COLOR
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Couldn't fetch a fact right now!")
        except Exception as e:
            await ctx.send("❌ Error fetching fact!")
    
    @commands.command(
        name="quote",
        description="Get an inspirational quote",
        usage="quote"
    )
    async def quote(self, ctx):
        """Get an inspirational quote"""
        try:
            async with self.bot.session.get('https://api.quotable.io/random') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    embed = discord.Embed(
                        title="💭 Inspirational Quote",
                        description=f'"{data["content"]}"',
                        color=self.bot.config.PRIMARY_COLOR
                    )
                    embed.set_footer(text=f"— {data['author']}")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Couldn't fetch a quote right now!")
        except Exception as e:
            await ctx.send("❌ Error fetching quote!")
    
    @commands.command(
        name="reverse",
        description="Reverse the given text",
        usage="reverse <text>"
    )
    async def reverse(self, ctx, *, text: str):
        """Reverse the given text"""
        reversed_text = text[::-1]
        
        embed = discord.Embed(
            title="🔄 Text Reversed",
            color=self.bot.config.PRIMARY_COLOR
        )
        embed.add_field(name="Original", value=text, inline=False)
        embed.add_field(name="Reversed", value=reversed_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="ascii",
        description="Convert text to ASCII art (max 10 characters)",
        usage="ascii <text>"
    )
    async def ascii_art(self, ctx, *, text: str):
        """Convert text to ASCII art (simple version)"""
        if len(text) > 10:
            return await ctx.send("❌ Text too long! Maximum 10 characters.")
        
        # Simple ASCII art mapping
        ascii_chars = {
            'A': ['  █  ', ' █ █ ', '█████', '█   █', '█   █'],
            'B': ['████ ', '█   █', '████ ', '█   █', '████ '],
            'C': [' ████', '█    ', '█    ', '█    ', ' ████'],
            'D': ['████ ', '█   █', '█   █', '█   █', '████ '],
            'E': ['█████', '█    ', '███  ', '█    ', '█████'],
            # Add more letters as needed
        }
        
        lines = ['', '', '', '', '']
        for char in text.upper():
            if char in ascii_chars:
                for i, line in enumerate(ascii_chars[char]):
                    lines[i] += line + ' '
            elif char == ' ':
                for i in range(5):
                    lines[i] += '   '
        
        ascii_art = '\n'.join(lines)
        
        embed = discord.Embed(
            title="🎨 ASCII Art",
            description=f"```\n{ascii_art}\n```",
            color=self.bot.config.PRIMARY_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(
        name="poll",
        description="Create a poll with reactions for voting",
        usage="poll \"<question>\" \"<option1>\" \"<option2>\" [more options...]"
    )
    async def poll(self, ctx, question: str, *options):
        """Create a poll with reactions"""
        if len(options) < 2:
            return await ctx.send("❌ Please provide at least 2 options!")
        
        if len(options) > 10:
            return await ctx.send("❌ Maximum 10 options allowed!")
        
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=self.bot.config.PRIMARY_COLOR,
            timestamp=datetime.utcnow()
        )
        
        for i, option in enumerate(options):
            embed.add_field(
                name=f"{reactions[i]} Option {i+1}",
                value=option,
                inline=False
            )
        
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        
        message = await ctx.send(embed=embed)
        
        for i in range(len(options)):
            await message.add_reaction(reactions[i])

async def setup(bot):
    await bot.add_cog(Fun(bot))
