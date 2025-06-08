import discord
from discord.ext import commands
import random
import asyncio

class Games(commands.Cog):
    """🎯 Interactive games to play with the bot and other users"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
    
    @commands.command(
        name="rps",
        description="Play Rock Paper Scissors against the bot",
        usage="rps <rock|paper|scissors>",
        aliases=["rockpaperscissors"]
    )
    async def rock_paper_scissors(self, ctx, choice: str = None):
        """Play Rock Paper Scissors"""
        if not choice:
            return await ctx.send("❌ Please choose: rock, paper, or scissors!")
        
        choice = choice.lower()
        if choice not in ['rock', 'paper', 'scissors']:
            return await ctx.send("❌ Invalid choice! Choose: rock, paper, or scissors")
        
        bot_choice = random.choice(['rock', 'paper', 'scissors'])
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = self.bot.config.WARNING_COLOR
        elif (choice == 'rock' and bot_choice == 'scissors') or \
             (choice == 'paper' and bot_choice == 'rock') or \
             (choice == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
            color = self.bot.config.SUCCESS_COLOR
        else:
            result = "I win!"
            color = self.bot.config.ERROR_COLOR
        
        embed = discord.Embed(
            title="🪨📄✂️ Rock Paper Scissors",
            color=color
        )
        embed.add_field(name="Your choice", value=choice.title(), inline=True)
        embed.add_field(name="My choice", value=bot_choice.title(), inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="guess",
        description="Start a number guessing game or make a guess",
        usage="guess [number]"
    )
    async def guess_number(self, ctx, number: int = None):
        """Guess a number between 1 and 100"""
        if ctx.author.id in self.active_games:
            return await ctx.send("❌ You already have an active game!")
        
        if number is None:
            # Start new game
            secret = random.randint(1, 100)
            self.active_games[ctx.author.id] = {
                'secret': secret,
                'attempts': 0,
                'max_attempts': 7
            }
            
            embed = discord.Embed(
                title="🎯 Number Guessing Game",
                description="I'm thinking of a number between 1 and 100!\nYou have 7 attempts to guess it.",
                color=self.bot.config.PRIMARY_COLOR
            )
            embed.add_field(name="How to play", value=f"Use `{ctx.prefix}guess <number>` to make a guess!", inline=False)
            
            await ctx.send(embed=embed)
        else:
            # Make a guess
            if ctx.author.id not in self.active_games:
                return await ctx.send("❌ You don't have an active game! Start one with `!guess`")
            
            game = self.active_games[ctx.author.id]
            game['attempts'] += 1
            
            if number == game['secret']:
                # Correct guess
                del self.active_games[ctx.author.id]
                
                embed = discord.Embed(
                    title="🎉 Congratulations!",
                    description=f"You guessed the number **{game['secret']}** in {game['attempts']} attempts!",
                    color=self.bot.config.SUCCESS_COLOR
                )
                await ctx.send(embed=embed)
            elif game['attempts'] >= game['max_attempts']:
                # Out of attempts
                del self.active_games[ctx.author.id]
                
                embed = discord.Embed(
                    title="💀 Game Over!",
                    description=f"You ran out of attempts! The number was **{game['secret']}**",
                    color=self.bot.config.ERROR_COLOR
                )
                await ctx.send(embed=embed)
            else:
                # Wrong guess
                hint = "higher" if number < game['secret'] else "lower"
                remaining = game['max_attempts'] - game['attempts']
                
                embed = discord.Embed(
                    title="❌ Wrong Guess!",
                    description=f"The number is **{hint}** than {number}",
                    color=self.bot.config.WARNING_COLOR
                )
                embed.add_field(name="Attempts remaining", value=remaining, inline=True)
                
                await ctx.send(embed=embed)
    
    @commands.command(
        name="trivia",
        description="Answer a random trivia question",
        usage="trivia"
    )
    async def trivia(self, ctx):
        """Answer a trivia question"""
        questions = [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "answer": 2
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                "answer": 1
            },
            {
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "answer": 1
            },
            {
                "question": "Who painted the Mona Lisa?",
                "options": ["Van Gogh", "Picasso", "Da Vinci", "Monet"],
                "answer": 2
            },
            {
                "question": "What is the largest ocean on Earth?",
                "options": ["Atlantic", "Pacific", "Indian", "Arctic"],
                "answer": 1
            }
        ]
        
        question_data = random.choice(questions)
        
        embed = discord.Embed(
            title="🧠 Trivia Question",
            description=question_data["question"],
            color=self.bot.config.PRIMARY_COLOR
        )
        
        for i, option in enumerate(question_data["options"]):
            embed.add_field(name=f"{i+1}.", value=option, inline=True)
        
        embed.set_footer(text="React with 1️⃣, 2️⃣, 3️⃣, or 4️⃣ to answer!")
        
        message = await ctx.send(embed=embed)
        
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
        for reaction in reactions:
            await message.add_reaction(reaction)
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            user_answer = reactions.index(str(reaction.emoji))
            correct_answer = question_data["answer"]
            
            if user_answer == correct_answer:
                result_embed = discord.Embed(
                    title="✅ Correct!",
                    description=f"The answer was **{question_data['options'][correct_answer]}**",
                    color=self.bot.config.SUCCESS_COLOR
                )
            else:
                result_embed = discord.Embed(
                    title="❌ Wrong!",
                    description=f"The correct answer was **{question_data['options'][correct_answer]}**",
                    color=self.bot.config.ERROR_COLOR
                )
            
            await ctx.send(embed=result_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ Time's Up!",
                description=f"The correct answer was **{question_data['options'][question_data['answer']]}**",
                color=self.bot.config.WARNING_COLOR
            )
            await ctx.send(embed=timeout_embed)
    
    @commands.command(
        name="tictactoe",
        description="Play Tic Tac Toe against another user",
        usage="tictactoe <@user>",
        aliases=["ttt"]
    )
    async def tic_tac_toe(self, ctx, member: discord.Member = None):
        """Play Tic Tac Toe"""
        if not member:
            return await ctx.send("❌ Please mention someone to play with!")
        
        if member == ctx.author:
            return await ctx.send("❌ You can't play against yourself!")
        
        if member.bot:
            return await ctx.send("❌ You can't play against bots!")
        
        # Create game board
        board = ["⬜"] * 9
        players = [ctx.author, member]
        current_player = 0
        symbols = ["❌", "⭕"]
        
        def create_board_embed():
            board_display = ""
            for i in range(3):
                board_display += "".join(board[i*3:(i+1)*3]) + "\n"
            
            embed = discord.Embed(
                title="🎮 Tic Tac Toe",
                description=board_display,
                color=self.bot.config.PRIMARY_COLOR
            )
            embed.add_field(
                name="Current Turn", 
                value=f"{players[current_player].display_name} ({symbols[current_player]})",
                inline=False
            )
            embed.set_footer(text="React with 1️⃣-9️⃣ to make your move!")
            return embed
        
        def check_winner():
            # Check rows, columns, and diagonals
            winning_combinations = [
                [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
                [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
                [0, 4, 8], [2, 4, 6]              # diagonals
            ]
            
            for combo in winning_combinations:
                if board[combo[0]] == board[combo[1]] == board[combo[2]] != "⬜":
                    return board[combo[0]]
            
            if "⬜" not in board:
                return "tie"
            
            return None
        
        message = await ctx.send(embed=create_board_embed())
        
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
        for emoji in number_emojis:
            await message.add_reaction(emoji)
        
        while True:
            def check(reaction, user):
                return (user == players[current_player] and 
                       str(reaction.emoji) in number_emojis and 
                       reaction.message.id == message.id)
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                
                position = number_emojis.index(str(reaction.emoji))
                
                if board[position] != "⬜":
                    await message.remove_reaction(reaction.emoji, user)
                    continue
                
                board[position] = symbols[current_player]
                
                winner = check_winner()
                if winner:
                    if winner == "tie":
                        final_embed = discord.Embed(
                            title="🤝 It's a Tie!",
                            description="".join([board[i*3:(i+1)*3][j] for i in range(3) for j in range(3) if j < 3]) + "\n" * 3,
                            color=self.bot.config.WARNING_COLOR
                        )
                    else:
                        winner_player = players[symbols.index(winner)]
                        final_embed = discord.Embed(
                            title=f"🎉 {winner_player.display_name} Wins!",
                            description="".join([board[i*3:(i+1)*3][j] for i in range(3) for j in range(3) if j < 3]) + "\n" * 3,
                            color=self.bot.config.SUCCESS_COLOR
                        )
                    
                    await message.edit(embed=final_embed)
                    await message.clear_reactions()
                    break
                
                current_player = 1 - current_player
                await message.edit(embed=create_board_embed())
                await message.remove_reaction(reaction.emoji, user)
                
            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title="⏰ Game Timed Out!",
                    description="The game has been cancelled due to inactivity.",
                    color=self.bot.config.ERROR_COLOR
                )
                await message.edit(embed=timeout_embed)
                await message.clear_reactions()
                break

async def setup(bot):
    await bot.add_cog(Games(bot))
