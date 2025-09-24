import asyncio
import io
import contextlib
import traceback
import textwrap
from datetime import datetime
from discord.ext import commands
import discord

# Global vars that need to be shared
shutdown_in_progress = False
REPL_TIMEOUT = 15 * 60  # seconds of inactivity before the session auto-closes
repl_sessions: dict[int, asyncio.Task] = {}  # channel-id → running task

# Create a persistent global environment for eval
global_env = {
    "__builtins__": __builtins__,
    "bot": None,
    "discord": discord,
    "commands": commands,
    "asyncio": asyncio,
}

class AdminCommands(commands.Cog):
    """Owner-only administrative commands"""
    
    def __init__(self, bot):
        self.bot = bot
        # Update global env with bot reference
        global_env["bot"] = bot
    
    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx, *args):
        """Shutdown the bot with countdown"""
        global shutdown_in_progress
        
        if '-e' in args:
            await ctx.send("Emergency Shutdown Bypass: Activated | Force Quiting All Running Services...")
            await self.bot.close()
            return
        
        if shutdown_in_progress:
            shutdown_in_progress = False
            await ctx.send("Shutdown sequence halted.")
            return
        
        shutdown_in_progress = True
        countdown_message = await ctx.send(
            "! - Shutdown Sequence Initiated: (--s) Run 7/shutdown again to cancel.")
        
        for i in range(10, 0, -1):
            if not shutdown_in_progress:
                return
            await countdown_message.edit(
                content=f"! - Shutdown Sequence Initiated: ({i}s) Run 7/shutdown again to cancel.")
            await asyncio.sleep(1)
        
        if shutdown_in_progress:
            await countdown_message.edit(content="! - Shutdown Sequence Initiated: (0s)")
            await asyncio.sleep(0.5)
            await countdown_message.edit(content="! - Shutdown Sequence Finished - 7x Shut Down.")
            await self.bot.close()
        
        shutdown_in_progress = False
    
    @commands.command(name="eval")
    @commands.is_owner()
    async def _eval(self, ctx, *, code: str):
        """Execute Python code"""
        # Update the persistent environment with current context and bot.
        global_env["bot"] = self.bot
        global_env["ctx"] = ctx
        
        # If the code is wrapped in a code block, remove those markers.
        if code.startswith("```") and code.endswith("```"):
            lines = code.splitlines()
            code = "\n".join(lines[1:-1]) if len(lines) >= 3 else code[3:-3].strip()
        
        try:
            # First, try to compile as an expression.
            compiled = compile(code, "<eval>", "eval")
            result = eval(compiled, global_env)
            if asyncio.iscoroutine(result):
                result = await result
            await ctx.send(f"Result: {result}")
        except SyntaxError:
            try:
                compiled = compile(code, "<exec>", "exec")
                with io.StringIO() as buffer:
                    with contextlib.redirect_stdout(buffer):
                        exec(compiled, global_env)
                    output = buffer.getvalue()
                if not output:
                    output = "Code executed without output."
                await ctx.send(f"Output:\n```py\n{output}\n```")
            except Exception:
                tb = traceback.format_exc()
                await ctx.send(f"Error during exec:\n```py\n{tb}\n```")
        except Exception:
            tb = traceback.format_exc()
            await ctx.send(f"Error during eval:\n```py\n{tb}\n```")
    
    @commands.command(name="repl", 
                     help="Start an owner-only live Python REPL in this channel.",
                     usage="7/repl   ← start | exit() / quit() to stop")
    @commands.is_owner()
    async def repl(self, ctx: commands.Context):
        """
        Interactive, *unsandboxed* Python – each line you send is executed.
        The bot edits one message so you get a scrolling terminal-style view.
        Use `exit()` or `quit()` (or let it time-out) to leave.
        """
        # If there's already a session in this channel, ignore the new request.
        if ctx.channel.id in repl_sessions:
            await ctx.send("A REPL is already active in this channel.")
            return
        
        # Persistent namespace for this session only
        env = {
            "__builtins__": __builtins__,
            "bot": self.bot,
            "ctx": ctx,
            "discord": discord,
            "asyncio": asyncio,
        }
        
        banner = "# ‣ Python REPL started – type exit() or quit() to stop\n>>> "
        log_lines: list[str] = [banner]
        
        # The message we'll keep editing so the log scrolls in place
        term_msg = await ctx.send(f"```py\n{banner}```")
        
        def fmt_log() -> str:
            """Return the current log chunk wrapped in a code-block, truncated to 2 000 chars."""
            txt = "\n".join(log_lines)[-1950:]  # keep breathing room for the ```py
            return f"```py\n{txt}\n```"
        
        # Helper to append & display new output
        async def push(line: str):
            log_lines.append(line)
            payload = fmt_log()
            # If the edited message would be too large, send a fresh one instead.
            if len(payload) > 2000:
                await ctx.send(payload)
                log_lines.clear()
            else:
                await term_msg.edit(content=payload)
        
        # Wait-loop lives in its own task so multiple channels can run REPLs concurrently
        async def repl_loop():
            try:
                while True:
                    # wait for the owner's next message in this channel
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    
                    try:
                        user_msg = await self.bot.wait_for("message",
                                                          check=check,
                                                          timeout=REPL_TIMEOUT)
                    except asyncio.TimeoutError:
                        await push("\n# Session timed-out, REPL closed.")
                        break
                    
                    src = user_msg.content.strip()
                    # Allow triple-back-tick blocks; strip fences if present
                    if src.startswith("```") and src.endswith("```"):
                        src = "\n".join(src.splitlines()[1:-1])
                    
                    if src in {"exit()", "quit()", "exit", "quit"}:
                        await push("\n# REPL closed.")
                        break
                    
                    # Echo the input to the log
                    await push(f">>> {src}")
                    
                    # Capture stdout/stderr
                    with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                        try:
                            try:
                                # try expression first, then statements
                                compiled = compile(src, "<repl>", "eval")
                                result = eval(compiled, env)
                                if asyncio.iscoroutine(result):
                                    result = await result
                            except SyntaxError:
                                compiled = compile(src, "<repl>", "exec")
                                exec(compiled, env)
                                result = None
                        except Exception:
                            result = traceback.format_exc()
                        
                        output = buf.getvalue()
                    
                    # Prepare what to print back
                    lines = []
                    if output:
                        lines.append(output.rstrip())
                    if result is not None:
                        lines.append(repr(result))
                    if not lines:
                        lines.append("None")
                    
                    await push("\n".join(lines))
            finally:
                # Clean-up so another session can be started later
                repl_sessions.pop(ctx.channel.id, None)
        
        # Store and start the task
        repl_sessions[ctx.channel.id] = asyncio.create_task(repl_loop())
    
    @commands.command()
    @commands.is_owner()
    async def debug(self, ctx, *args):
        """Debug command for testing purposes"""
        if args:
            await ctx.send(f"Debug args: {' '.join(args)}")
        else:
            await ctx.send("Debug mode active - no arguments provided")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))