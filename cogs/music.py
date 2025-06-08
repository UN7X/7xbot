import discord
from discord.ext import commands
import asyncio
import aiohttp
import re
import json
import random
from async_timeout import timeout
import itertools
import functools
from collections import deque
from urllib.parse import urlparse
import mimetypes

class AudioSource(discord.PCMVolumeTransformer):
    """Represents an audio source from various platforms."""
    
    def __init__(self, ctx, source, url, title=None, duration=None, thumbnail=None, uploader=None):
        super().__init__(source, 0.5)
        self.requester = ctx.author
        self.channel = ctx.channel
        self.url = url
        self.title = title or "Unknown Track"
        self.duration = duration or "Unknown"
        self.thumbnail = thumbnail
        self.uploader = uploader or "Unknown Artist"
        self.stream_url = url
    
    @classmethod
    async def create_source(cls, ctx, url, *, title=None, duration=None, thumbnail=None, uploader=None):
        """Create a source from a URL."""
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        source = discord.FFmpegPCMAudio(url, **ffmpeg_options)
        return cls(ctx, source, url, title=title, duration=duration, thumbnail=thumbnail, uploader=uploader)

class RadioStation:
    """Represents a radio station."""
    
    STATIONS = {
        'lofi': {
            'name': 'Lo-Fi Hip Hop Radio',
            'url': 'http://hyades.shoutca.st:8043/stream',
            'genre': 'Lo-Fi Hip Hop'
        },
        'jazz': {
            'name': 'Smooth Jazz',
            'url': 'http://strm112.1.fm/smoothjazz_mobile_mp3',
            'genre': 'Jazz'
        },
        'classical': {
            'name': 'Classical Radio',
            'url': 'http://strm112.1.fm/classical_mobile_mp3',
            'genre': 'Classical'
        },
        'rock': {
            'name': 'Rock Classics',
            'url': 'http://strm112.1.fm/rockclassics_mobile_mp3',
            'genre': 'Rock'
        },
        'ambient': {
            'name': 'Ambient Dreams',
            'url': 'http://strm112.1.fm/ambientdreams_mobile_mp3',
            'genre': 'Ambient'
        },
        'top40': {
            'name': 'Top 40',
            'url': 'http://strm112.1.fm/top40_mobile_mp3',
            'genre': 'Pop'
        },
        'country': {
            'name': 'Country Radio',
            'url': 'http://strm112.1.fm/country_mobile_mp3',
            'genre': 'Country'
        },
        'dance': {
            'name': 'Dance Hits',
            'url': 'http://strm112.1.fm/club_mobile_mp3',
            'genre': 'Dance'
        }
    }
    
    @classmethod
    def get_station(cls, name):
        """Get a radio station by name."""
        return cls.STATIONS.get(name.lower())
    
    @classmethod
    def list_stations(cls):
        """List all available radio stations."""
        return cls.STATIONS

class MusicPlayer:
    """A class that handles music playback for a guild."""
    
    def __init__(self, ctx):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog
        
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        
        self.current = None
        self.volume = 0.5
        self.now_playing = None
        
        self.bot.loop.create_task(self.player_loop())
        
    async def player_loop(self):
        """Main player loop."""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            self.next.clear()
            
            # Try to get a song within 3 minutes
            try:
                async with timeout(180):  # 3 minutes
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                # No song was added to the queue in time
                await self.destroy(self.guild)
                return
            
            # Set volume
            source.volume = self.volume
            self.current = source
            
            # Play the song
            try:
                self.guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                
                # Create and send now playing embed
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    description=f"**{source.title}**",
                    color=self.bot.config.PRIMARY_COLOR
                )
                
                if source.thumbnail:
                    embed.set_thumbnail(url=source.thumbnail)
                
                embed.add_field(name="Duration", value=source.duration, inline=True)
                embed.add_field(name="Requested by", value=source.requester.mention, inline=True)
                embed.add_field(name="Source", value=source.uploader, inline=True)
                
                self.now_playing = await self.channel.send(embed=embed)
                
            except Exception as e:
                await self.channel.send(f"❌ Error playing audio: {str(e)}")
                self.current = None
                continue
            
            # Wait for the song to finish
            await self.next.wait()
            
            # Clean up
            self.current = None
            
            # Delete now playing message
            try:
                if self.now_playing:
                    await self.now_playing.delete()
            except discord.HTTPException:
                pass
    
    async def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self.cog.cleanup(guild))

class Music(commands.Cog):
    """🎵 Play music from direct URLs and radio stations"""
    
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        self.session = None
        self.check_empty_voice_task = self.bot.loop.create_task(self.check_empty_voice_channels())
    
    def cog_unload(self):
        """Cleanup when cog is unloaded."""
        if self.check_empty_voice_task:
            self.check_empty_voice_task.cancel()
        
        if self.session:
            asyncio.create_task(self.session.close())
    
    async def get_session(self):
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def cleanup(self, guild):
        """Cleanup the guild player."""
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass
            
        try:
            del self.players[guild.id]
        except KeyError:
            pass
    
    async def check_empty_voice_channels(self):
        """Check for empty voice channels and leave them."""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                voice_client = guild.voice_client
                if voice_client and voice_client.is_connected():
                    # Check if there are any non-bot members in the voice channel
                    if not any(member for member in voice_client.channel.members if not member.bot):
                        await voice_client.disconnect()
                        if guild.id in self.players:
                            await self.cleanup(guild)
                            try:
                                await self.players[guild.id].channel.send("👋 Left the voice channel because everyone left.")
                            except:
                                pass
            
            # Check every 30 seconds
            await asyncio.sleep(30)
    
    def get_player(self, ctx):
        """Get or create a player for a guild."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player
            
        return player
    
    async def is_valid_url(self, url):
        """Check if URL is valid and accessible."""
        try:
            session = await self.get_session()
            async with session.head(url, timeout=5) as resp:
                return resp.status == 200
        except:
            return False
    
    async def is_audio_url(self, url):
        """Check if URL points to an audio file."""
        try:
            # Check file extension
            audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma']
            if any(url.lower().endswith(ext) for ext in audio_extensions):
                return True
            
            # Check MIME type
            session = await self.get_session()
            async with session.head(url, timeout=5) as resp:
                content_type = resp.headers.get('content-type', '').lower()
                return content_type.startswith('audio/')
        except:
            return False
    
    @commands.command(
        name="join",
        description="Join your voice channel",
        usage="join"
    )
    async def join(self, ctx):
        """Join the user's voice channel."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You are not connected to a voice channel.")
            
        voice_client = ctx.voice_client
        
        if voice_client:
            if voice_client.channel.id == ctx.author.voice.channel.id:
                return await ctx.send("✅ I'm already in your voice channel!")
            await voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.author.voice.channel.connect()
            
        await ctx.send(f"✅ Joined {ctx.author.voice.channel.mention}")
    
    @commands.command(
        name="play",
        description="Play audio from direct URLs or radio stations",
        usage="play <direct audio URL | radio:station_name>",
        aliases=["p"]
    )
    async def play(self, ctx, *, query: str):
        """Play audio from various sources."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You are not connected to a voice channel.")
            
        voice_client = ctx.voice_client
        
        if not voice_client:
            await ctx.invoke(self.join)
            voice_client = ctx.voice_client
        
        # Check if it's a radio station request
        if query.startswith('radio:'):
            station_name = query[6:]  # Remove 'radio:' prefix
            station = RadioStation.get_station(station_name)
            
            if not station:
                return await ctx.send(f"❌ Radio station '{station_name}' not found. Use `!radio` to see available stations.")
            
            url = station['url']
            title = station['name']
            uploader = f"Radio - {station['genre']}"
            
        else:
            # Assume it's a direct URL
            url = query
            
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                embed = discord.Embed(
                    title="❌ Invalid URL",
                    description="Please provide a valid URL starting with http:// or https://\n"
                              "Or use `radio:station_name` to play a radio station.\n"
                              "Use `!radio` to see available stations.",
                    color=self.bot.config.ERROR_COLOR
                )
                return await ctx.send(embed=embed)
            
            # Check if URL is accessible
            if not await self.is_valid_url(url):
                return await ctx.send("❌ Could not access the provided URL.")
            
            # Extract filename from URL for title
            filename = url.split('/')[-1].split('?')[0]
            title = filename
            uploader = "Direct Link"
        
        # Send loading message
        loading_msg = await ctx.send("🔄 Loading audio source...")
        
        try:
            # Create audio source
            source = await AudioSource.create_source(
                ctx, url, title=title, uploader=uploader
            )
            
            # Add to queue
            player = self.get_player(ctx)
            await player.queue.put(source)
            
            await loading_msg.edit(content=f"✅ Added to queue: **{title}**")
            
        except Exception as e:
            await loading_msg.edit(content=f"❌ Error: {str(e)}")
    
    @commands.command(
        name="radio",
        description="List available radio stations or play a specific station",
        usage="radio [station_name]"
    )
    async def radio(self, ctx, station_name: str = None):
        """Play radio stations or list available ones."""
        if station_name:
            # Play specific radio station
            await ctx.invoke(self.play, query=f"radio:{station_name}")
        else:
            # List available stations
            stations = RadioStation.list_stations()
            
            embed = discord.Embed(
                title="📻 Available Radio Stations",
                description="Use `!play radio:station_name` or `!radio station_name` to play",
                color=self.bot.config.PRIMARY_COLOR
            )
            
            for key, station in stations.items():
                embed.add_field(
                    name=f"🎵 {key}",
                    value=f"**{station['name']}**\n{station['genre']}",
                    inline=True
                )
            
            await ctx.send(embed=embed)
    
    @commands.command(
        name="pause",
        description="Pause the currently playing audio",
        usage="pause"
    )
    async def pause(self, ctx):
        """Pause the currently playing audio."""
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_playing():
            return await ctx.send("❌ I am not currently playing anything.")
            
        if voice_client.is_paused():
            return await ctx.send("⚠️ The audio is already paused.")
            
        voice_client.pause()
        await ctx.send("⏸️ Paused the audio.")
    
    @commands.command(
        name="resume",
        description="Resume the currently paused audio",
        usage="resume"
    )
    async def resume(self, ctx):
        """Resume the currently paused audio."""
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_connected():
            return await ctx.send("❌ I am not connected to a voice channel.")
            
        if not voice_client.is_paused():
            return await ctx.send("⚠️ The audio is not paused.")
            
        voice_client.resume()
        await ctx.send("▶️ Resumed the audio.")
    
    @commands.command(
        name="skip",
        description="Skip the currently playing audio",
        usage="skip"
    )
    async def skip(self, ctx):
        """Skip the currently playing audio."""
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_playing():
            return await ctx.send("❌ I am not currently playing anything.")
            
        voice_client.stop()
        await ctx.send("⏭️ Skipped the audio.")
    
    @commands.command(
        name="queue",
        description="View the current audio queue",
        usage="queue",
        aliases=["q"]
    )
    async def queue_info(self, ctx):
        """Display the current audio queue."""
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_connected():
            return await ctx.send("❌ I am not connected to a voice channel.")
            
        player = self.get_player(ctx)
        
        if player.queue.empty() and not player.current:
            return await ctx.send("❌ The queue is empty.")
            
        # Get up to 10 items from the queue
        upcoming = list(itertools.islice(player.queue._queue, 0, 10))
        
        embed = discord.Embed(
            title="🎵 Audio Queue",
            color=self.bot.config.PRIMARY_COLOR
        )
        
        if player.current:
            embed.add_field(
                name="Now Playing",
                value=f"**{player.current.title}** | Requested by {player.current.requester.mention}",
                inline=False
            )
        
        if upcoming:
            queue_list = "\n".join(f"`{i+1}.` **{audio.title}** | Requested by {audio.requester.mention}"
                                for i, audio in enumerate(upcoming))
            embed.add_field(name="Up Next", value=queue_list, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="now_playing",
        description="Show information about the currently playing audio",
        usage="now_playing",
        aliases=["np", "current", "playing"]
    )
    async def now_playing(self, ctx):
        """Display information about the currently playing audio."""
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_playing():
            return await ctx.send("❌ I am not currently playing anything.")
            
        player = self.get_player(ctx)
        source = player.current
        
        if not source:
            return await ctx.send("❌ No current track information available.")
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{source.title}**",
            color=self.bot.config.PRIMARY_COLOR
        )
        
        if source.thumbnail:
            embed.set_thumbnail(url=source.thumbnail)
        
        embed.add_field(name="Duration", value=source.duration, inline=True)
        embed.add_field(name="Requested by", value=source.requester.mention, inline=True)
        embed.add_field(name="Source", value=source.uploader, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(
        name="volume",
        description="Change the player volume",
        usage="volume [0-100]"
    )
    async def volume(self, ctx, *, volume: int = None):
        """Change the player volume."""
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_connected():
            return await ctx.send("❌ I am not connected to a voice channel.")
            
        player = self.get_player(ctx)
        
        if volume is None:
            return await ctx.send(f"🔊 The current volume is {int(player.volume * 100)}%")
            
        if not 0 <= volume <= 100:
            return await ctx.send("❌ Please enter a value between 0 and 100.")
            
        player.volume = volume / 100
        if voice_client.is_playing():
            voice_client.source.volume = player.volume
            
        await ctx.send(f"🔊 Set the volume to {volume}%")
    
    @commands.command(
        name="stop",
        description="Stop playing and clear the queue",
        usage="stop"
    )
    async def stop(self, ctx):
        """Stop playing and clear the queue."""
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_connected():
            return await ctx.send("❌ I am not connected to a voice channel.")
            
        await self.cleanup(ctx.guild)
        await ctx.send("⏹️ Stopped the audio and cleared the queue.")
    
    @commands.command(
        name="leave",
        description="Leave the voice channel",
        usage="leave",
        aliases=["disconnect"]
    )
    async def leave(self, ctx):
        """Leave the voice channel."""
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_connected():
            return await ctx.send("❌ I am not connected to a voice channel.")
            
        await self.cleanup(ctx.guild)
        await ctx.send("👋 Left the voice channel.")
    
    @play.before_invoke
    async def ensure_voice(self, ctx):
        """Ensure the bot is in a voice channel before playing."""
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("❌ You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

async def setup(bot):
    await bot.add_cog(Music(bot))
