"""Core helpers and commands for the 7x bot.
This module exposes utility functions and a Cog so the bot
matches the rest of the codebase's structure.
"""

from __future__ import annotations

import asyncio
import json
import psutil
from datetime import datetime
from typing import Optional, Callable, Any

import discord
from discord.ext import commands

from config import Config

bot: Optional[commands.Bot] = None
bot_start_time = datetime.now()

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def get_uptime(start_time: Optional[datetime] = None) -> str:
    start_time = start_time or bot_start_time
    return str(datetime.now() - start_time)


def days_until_christmas() -> int:
    today = datetime.now()
    christmas = datetime(today.year, 12, 25)
    if today > christmas:
        christmas = datetime(today.year + 1, 12, 25)
    return (christmas - today).days


def get_bot_info(dbot: commands.Bot, ctx: Optional[commands.Context] = None) -> dict[str, Any]:
    ping_ms = round(dbot.latency * 1000)
    shard_id = ctx.guild.shard_id if ctx and ctx.guild else 0
    try:
        load = psutil.Process().cpu_percent(interval=0.1)
    except Exception:
        load = psutil.cpu_percent(interval=0.1)
    return {"ping_ms": ping_ms, "shard_id": shard_id, "cpu_load": load}


def get_build_id() -> str:
    return "v1.9"

# ---------------------------------------------------------------------------
# Simple JSON database helpers
# ---------------------------------------------------------------------------

def load_db(filename: str = "database.json") -> dict:
    try:
        with open(filename, "r") as f:
            first = f.read(1)
            if not first:
                return {}
            f.seek(0)
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_db(data: dict, filename: str = "database.json") -> None:
    with open(filename, "w") as f:
        json.dump(data or {}, f, indent=4)


db = load_db()


def get_server_config(guild_id: int) -> dict:
    return db.get("config", {}).get(str(guild_id), {})

# ---------------------------------------------------------------------------
# Economy helpers
# ---------------------------------------------------------------------------

shop_items_regular = {
    "vip": {"price": 100, "description": "Temporary VIP role"},
    "nickname": {"price": 50, "description": "Change your nickname"},
}

shop_items_prankful = {
    "spam_ping": {"price": 20, "description": "One use of spam ping"},
    "sudo": {"price": 30, "description": "Impersonate another user once"},
}


def get_shop_items_for_guild(guild_id: int) -> dict:
    eco = get_server_config(guild_id).get("economy", "none")
    if eco == "regular":
        return shop_items_regular
    if eco == "prankful":
        return shop_items_prankful
    return {}


def check_points(user_id: str) -> int:
    return db.get(f"points_{user_id}", 0)


def set_points(user_id: str, pts: int) -> None:
    db[f"points_{user_id}"] = pts
    save_db(db)


def update_points(user_id: str, pts: int) -> None:
    new_total = max(check_points(user_id) + pts, 0)
    set_points(user_id, new_total)

# ---------------------------------------------------------------------------
# Setup wizard
# ---------------------------------------------------------------------------

setup_explanation = (
    "**Info:**\n"
    "Interactive server setup wizard.\n"
    "**Usage:** `7/setup` to begin or `7/setup help` for this message."
)

man_pages: dict[str, str] = {"setup": setup_explanation}


async def setup_wizard(ctx: commands.Context, *, args: Optional[str] = None) -> None:
    if args and args.lower() == "help":
        embed = discord.Embed(
            title="Setup Command Help",
            description=setup_explanation,
            color=Config.PRIMARY_COLOR,
        )
        await ctx.send(embed=embed)
        return
    if args:
        embed = discord.Embed(
            title="Setup Command Help",
            description=setup_explanation,
            color=Config.PRIMARY_COLOR,
        )
        await ctx.send(embed=embed)
        return

    await ctx.send("Starting setup wizard. Reply with 'cancel' to stop.")

    class SetupCancelled(Exception):
        pass

    async def ask(prompt: str, parser: Callable[[discord.Message], Any]):
        await ctx.send(prompt)
        try:
            msg = await bot.wait_for(
                "message",
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=60,
            )
        except asyncio.TimeoutError:
            await ctx.send("Timed out waiting for a response. Setup cancelled.")
            raise SetupCancelled
        if msg.content.lower() == "cancel":
            await ctx.send("Setup cancelled.")
            raise SetupCancelled
        return parser(msg)

    questions = [
        (
            "strike_roles",
            "Enter strike roles by mentioning them separated by spaces or 'none':",
            lambda m: [r.id for r in m.role_mentions],
        ),
        (
            "ai_enabled",
            "Enable AI features? (yes/no):",
            lambda m: m.content.lower().startswith("y"),
        ),
        (
            "economy",
            "Economy type (regular/prankful/none):",
            lambda m: m.content.lower(),
        ),
    ]

    config = {}
    try:
        for key, prompt, parser in questions:
            value = await ask(prompt, parser)
            if key == "economy" and value not in {"regular", "prankful", "none"}:
                await ctx.send("Invalid economy type. Choose regular, prankful or none.")
                raise SetupCancelled
            config[key] = value
    except SetupCancelled:
        return

    db.setdefault("config", {})[str(ctx.guild.id)] = config
    save_db(db)
    await ctx.send("Setup complete.")

# ---------------------------------------------------------------------------
# Manual page command
# ---------------------------------------------------------------------------

async def man_command(ctx: commands.Context, *, arg: Optional[str] = None) -> None:
    if arg is None or arg.strip() == "":
        await ctx.send("Please provide a command name or `--list`.")
    elif arg.strip() in ["--list", "--l"]:
        names = ", ".join(f"`{name}`" for name in man_pages.keys())
        await ctx.send(f"Available commands:\n{names}")
    elif arg.strip() in man_pages:
        embed = discord.Embed(
            title=f"Manual Entry for `{arg.strip()}`",
            description=man_pages[arg.strip()],
            color=Config.PRIMARY_COLOR,
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No manual entry for '{arg}'.")

# ---------------------------------------------------------------------------
# Core cog
# ---------------------------------------------------------------------------

class Core(commands.Cog):
    """Basic bot commands and setup flow"""

    def __init__(self, bot_: commands.Bot):
        global bot
        bot = bot_
        self.bot = bot_

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if channel := guild.system_channel or next(
            (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
            None,
        ):
            await channel.send("Thanks for adding me! Server admins can run `7/setup` to configure the bot.")

    @commands.group(invoke_without_command=True)
    async def beta(self, ctx: commands.Context, option: Optional[str] = None):
        if option == "help":
            embed = discord.Embed(
                title="Beta Command Help",
                description="Displays bot build information and tester commands.",
                color=Config.PRIMARY_COLOR,
            )
            await ctx.send(embed=embed)
            return

        if option is None or option == "info":
            info = get_bot_info(self.bot, ctx)
            embed = discord.Embed(
                title="7x Beta Info",
                color=Config.PRIMARY_COLOR,
            )
            embed.add_field(name="Build", value=get_build_id(), inline=False)
            embed.add_field(name="Uptime", value=get_uptime(), inline=False)
            embed.add_field(name="Ping", value=f"{info['ping_ms']}ms")
            embed.add_field(name="Shard", value=info['shard_id'])
            embed.add_field(name="CPU", value=f"{info['cpu_load']}%")
            await ctx.send(embed=embed)
            return

        await ctx.send(f"Unknown option: `{option}`. Use `7/beta help` for more info.")

    @commands.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def setup_cmd(self, ctx: commands.Context, *, args: Optional[str] = None):
        await setup_wizard(ctx, args=args)

    @commands.group(name="shop", invoke_without_command=True)
    async def shop(self, ctx: commands.Context, *, args: Optional[str] = None):
        if args and args.lower() == "help":
            embed = discord.Embed(title="Shop Command Help", description="View or buy items", color=Config.PRIMARY_COLOR)
            await ctx.send(embed=embed)
            return
        items = get_shop_items_for_guild(ctx.guild.id)
        embed = discord.Embed(title="7x Shop", color=Config.PRIMARY_COLOR)
        if not items:
            embed.description = "The shop is currently empty."
        else:
            for item_id, details in items.items():
                embed.add_field(name=f"{item_id} - {details['price']} points", value=details['description'], inline=False)
        await ctx.send(embed=embed)

    @shop.command(name="buy")
    async def shop_buy(self, ctx: commands.Context, item: Optional[str] = None):
        if not item:
            await ctx.send("Specify an item to buy. Use `7/shop` to view items.")
            return
        items = get_shop_items_for_guild(ctx.guild.id)
        details = items.get(item)
        if not details:
            await ctx.send("That item is not available.")
            return
        user_id = str(ctx.author.id)
        cost = details["price"]
        if check_points(user_id) < cost:
            await ctx.send("You don't have enough points.")
            return
        update_points(user_id, -cost)
        await ctx.send(f"Purchased {item} for {cost} points!")

    @commands.group(invoke_without_command=True)
    async def points(self, ctx: commands.Context):
        await ctx.send("Usage: `7/points <add/remove/query> <@user> [amount]`")

    @points.command()
    @commands.has_permissions(manage_guild=True)
    async def add(self, ctx: commands.Context, member: discord.Member, amount: int):
        user_id = str(member.id)
        update_points(user_id, amount)
        await ctx.send(f"Added {amount} points to {member.mention}. They now have {check_points(user_id)} points.")

    @points.command()
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx: commands.Context, member: discord.Member, amount: int):
        user_id = str(member.id)
        update_points(user_id, -amount)
        await ctx.send(f"Removed {amount} points from {member.mention}. They now have {check_points(user_id)} points.")

    @points.command(name="query")
    async def points_query(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        member = member or ctx.author
        user_id = str(member.id)
        await ctx.send(f"{member.mention} has {check_points(user_id)} points.")

    @commands.command(name="man")
    async def manual(self, ctx: commands.Context, *, arg: Optional[str] = None):
        await man_command(ctx, arg=arg)


async def setup(bot_: commands.Bot) -> None:
    await bot_.add_cog(Core(bot_))
