import discord
from discord.ext import commands
import yt_dlp
import re

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = [] # A list to store the songs urls
        self.is_playing = False

    def is_url(self, string):
        # A simple check to see if the input is a valid URL
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, string) is not None

    @commands.command(name="play")
    async def play(self, ctx, *, query: str):
        if not query:
            await ctx.send("Please provide a valid search query or URL.")
            return
        
        # Ensure the bot is connected to a voice channel
        if ctx.author.voice is None:
            await ctx.send("You are not in a voice channel.")
            return

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            # If bot is not in a voice channel, join the author's channel
            await voice_channel.connect()
        elif ctx.voice_client.channel != voice_channel:
            # If the bot is in a different voice channel, move it
            await ctx.voice_client.move_to(voice_channel)

        # Get the song URL (whether it's a direct URL or search query)
        song_url = await self.get_song_url(query)



        # Add song to queue
        if not song_url:
            await ctx.send("Could not find any results for the search query.")
            return

        # Add song to queue
        self.queue.append(song_url)
        await ctx.send(f"Added to queue: {song_url}")

        # Play the next song if not already playing
        if not self.is_playing:
            await self.play_next(ctx)
            

    async def get_song_url(self, query: str):
        # If it's a URL, return the query as it is
        if self.is_url(query):
            return query

        # If it's not a URL, treat it as a search term
        # Use yt-dlp to search for the song and get the first result's URL
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch',  # Search directly on YouTube
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                # Get the first entry's URL from the search results
                return info['entries'][0]['url']
            else:
                return info['url']
                
    

    async def play_next(self, ctx):
        if not ctx.voice_client:
            if ctx.author.voice:
                voice_channel = ctx.author.voice_channel
                self.voice_client = await voice_channel.connect()
            else:

                await ctx.send("Bot is not connected to a voice channel.")
                self.is_playing = False
                return

        if len(self.queue) > 0:
            self.is_playing = True
        
            # Extract the first song in the queue
            song = self.queue.pop(0)

            # Use yt-dlp to extract audio stream info
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'opus',
                    'preferredquality': '192',
                }],
                'buffer_size': '16M'
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(song, download=False)

                    # Make sure to get the best available audio format (safely)
                    audio_formats = [f for f in info['formats'] if f.get('acodec') and f.get('acodec') != 'none' and f.get('url')]

                    if not audio_formats:
                        await ctx.send("No valid audio streams found.")
                        self.is_playing = False
                        return
                    
                    # Select the best valid audio format
                    best_format = audio_formats[0]
                    url = best_format['url']
                    title = info.get('title', 'Audio')

                    # FFmpeg options for streaming audio
                    ffmpeg_options = {
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        'options': '-vn -b:a 192k',
                    }

                    
                    source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
                    ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))

                    await ctx.send(f"Now playing: {title}")

            except Exception as e:
                await ctx.send(f"Error: {str(e)}")
                self.is_playing = False

        else:
            self.is_playing = False


    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel.")
        else:
            await ctx.send("The bot is not connected to any voice channel.")

    @commands.command()
    async def pidor(self, ctx):
        await ctx.send("Stas Pidor!")

   
    @commands.command(name="queue")
    async def queue_list(self, ctx):
        if len(self.queue) == 0:
            await ctx.send("The queue is empty.")
        else:
            queue_list = "\n".join([f"{i+1}. {song}" for i, song in enumerate(self.queue)])
            await ctx.send(f"Current queue:\n{queue_list}")
    
    @commands.command(name="skip")
    async def skip(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped to the next song!")
        else:
            await ctx.send("No song is currently playing.")
    


async def setup(client):
    await client.add_cog(Music(client))
