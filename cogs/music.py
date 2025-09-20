# cogs/music.py
import discord
import asyncio
import lavalink
import re
from discord.ext import commands
from discord.ui import Button, View
from utils.utility import log_command

class MusicControls(discord.ui.View):
    def __init__(self, player, ctx):
        super().__init__(timeout=300)  # 5 minute timeout
        self.player = player
        self.ctx = ctx

    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.primary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.paused:
            await self.player.set_pause(False)
            await interaction.response.send_message("▶ Resumed", ephemeral=True)
            button.label = "⏸ Pause"
        else:
            await self.player.set_pause(True)
            await interaction.response.send_message("⏸ Paused", ephemeral=True)
            button.label = "▶ Resume"
        
        await update_queue_message(self.player, self.ctx)
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.primary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.player.queue) == 0 and not self.player.current:
            await interaction.response.send_message("❌ Nothing to skip!", ephemeral=True)
            return
        
        await self.player.skip()
        await interaction.response.send_message("⏭ Skipped!", ephemeral=True)
        await update_queue_message(self.player, self.ctx)
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player.queue.clear()
        await self.player.stop()
        await self.player.disconnect()
        
        for child in self.children:
            child.disabled = True
        
        await update_queue_message(self.player, self.ctx)
        await interaction.response.send_message("⏹ Stopped and disconnected.", ephemeral=True)
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label="🔁 Loop", style=discord.ButtonStyle.secondary)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.repeat:
            self.player.set_repeat(False)
            await interaction.response.send_message("🔁 Loop disabled", ephemeral=True)
            button.label = "🔁 Loop"
        else:
            self.player.set_repeat(True)
            await interaction.response.send_message("🔂 Loop enabled", ephemeral=True)
            button.label = "🔂 Looping"
        
        await update_queue_message(self.player, self.ctx)
        await interaction.edit_original_response(view=self)

    @discord.ui.button(label="📜 Queue", style=discord.ButtonStyle.secondary)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await update_queue_message(self.player, self.ctx)
        await interaction.response.send_message("Queue updated!", ephemeral=True)

async def update_queue_message(player, ctx):
    """Update or send the queue message with the latest queue info."""
    if not player.queue:
        content = "📜 Queue is empty!"
        embed = None
    else:
        queue_text = []
        for i, track in enumerate(player.queue[:10], 1):
            length_ms = getattr(track, 'length', getattr(track, 'duration', 0))
            minutes, seconds = divmod(length_ms // 1000, 60)
            queue_text.append(f"{i}. {track.title} - `{minutes}:{seconds:02d}`")
        
        embed = discord.Embed(
            title="📜 Queue",
            description="\n".join(queue_text),
            color=discord.Color.green()
        )
        
        if len(player.queue) > 10:
            embed.set_footer(text=f"... and {len(player.queue) - 10} more tracks")
        
        content = None

    # If we already have a queue message, edit it
    if hasattr(player, 'queue_message') and player.queue_message:
        try:
            await player.queue_message.edit(content=content, embed=embed)
        except Exception:
            # If editing fails (e.g., message deleted), send a new one
            player.queue_message = await ctx.send(content=content, embed=embed)
    else:
        player.queue_message = await ctx.send(content=content, embed=embed)

class Music(commands.Cog):
    """Music commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='play', aliases=['p'])
    @log_command
    async def play(self, ctx, *, query: str):
        """Play a song or add it to queue"""
        try:
            # Ensure the user is in a voice channel
            if not ctx.author.voice or not ctx.author.voice.channel:
                return await ctx.send("❌ You must be in a voice channel to play music.")
            
            voice_channel = ctx.author.voice.channel
            
            # Connect to voice if bot isn't already
            if not ctx.voice_client:
                permissions = voice_channel.permissions_for(ctx.guild.me)
                if not permissions.connect or not permissions.speak:
                    return await ctx.send("❌ I need the `CONNECT` and `SPEAK` permissions.")
                
                try:
                    await voice_channel.connect(cls=self.bot.LavalinkVoiceClient, self_deaf=True)
                except asyncio.TimeoutError:
                    return await ctx.send("❌ Connection timed out.")
            else:
                # Move to user's channel if different
                if ctx.voice_client.channel.id != voice_channel.id:
                    try:
                        await ctx.voice_client.move_to(voice_channel)
                    except Exception as e:
                        return await ctx.send(f"❌ Failed to move to your voice channel: {e}")

            # Get the player for this guild
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            if not player:
                player = self.bot.lavalink.player_manager.create(ctx.guild.id)

            # Remove angle brackets that might be around URLs
            query = query.strip('<>')

            # Check if it's a URL
            url_rx = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?)?')
            
            if not url_rx.match(query):
                # Try multiple search sources in order of preference
                search_queries = [
                    f'ytmsearch:{query}',
                    f'scsearch:{query}',
                    f'ytsearch:{query}'
                ]
                
                results = None
                for search_query in search_queries:
                    try:
                        temp_results = await player.node.get_tracks(search_query)
                        if temp_results and temp_results.tracks:
                            results = temp_results
                            break
                    except:
                        continue
            else:
                try:
                    results = await player.node.get_tracks(query)
                except Exception as e:
                    return await ctx.send(f'❌ Error loading URL: {str(e)}')

            if not results or not results.tracks:
                return await ctx.send('❌ Nothing found! Try a different search term.')

            embed = discord.Embed(color=discord.Color.blue())

            if results.load_type == 'PLAYLIST_LOADED':
                tracks = results.tracks
                for track in tracks:
                    player.add(requester=ctx.author.id, track=track)
                
                embed.title = '📋 Playlist Enqueued!'
                embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
            else:
                track = results.tracks[0]
                embed.title = '🎵 Track Enqueued' if player.current else '🎵 Now Playing'
                
                length_ms = getattr(track, 'length', getattr(track, 'duration', 0))
                minutes, seconds = divmod(length_ms // 1000, 60)
                embed.description = f'[{track.title}]({track.uri})\n`{minutes}:{seconds:02d}`'
                
                if 'youtube' in track.uri or 'youtu.be' in track.uri:
                    video_id = track.identifier
                    embed.set_thumbnail(url=f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg')
                
                embed.add_field(name='Artist', value=track.author if track.author else 'Unknown', inline=True)
                embed.add_field(name='Requested by', value=ctx.author.mention, inline=True)
                embed.add_field(name='Position in queue', value=str(len(player.queue) + 1) if player.current else 'Now playing', inline=True)
                
                player.add(requester=ctx.author.id, track=track)

            controls = MusicControls(player, ctx)
            await ctx.send(embed=embed, view=controls)

            # Start playing if nothing is currently playing
            if not player.is_playing:
                await player.play()

            # Update queue message after adding tracks
            await update_queue_message(player, ctx)

        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")
            print(f"Error in play command: {e}")

    @commands.command(aliases=['dc', 'leave'])
    @log_command
    async def disconnect(self, ctx):
        """Disconnect the bot from voice"""
        try:
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            
            if not player or not player.is_connected:
                return await ctx.send('❌ Not connected to a voice channel.')

            player.queue.clear()
            await player.stop()
            await player.disconnect()

            if ctx.voice_client and ctx.voice_client.is_connected():
                await ctx.voice_client.disconnect()

            await ctx.send('⏹ Disconnected.')

        except Exception as e:
            await ctx.send(f"❌ Error disconnecting: {str(e)}")
            print(f"Error in disconnect command: {e}")

    @commands.command()
    async def pause(self, ctx):
        """Pause the current track"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player:
            return await ctx.send('❌ No player found. Use `play` command first.')
        
        if not player.is_playing:
            return await ctx.send('❌ Not playing.')
        
        if player.paused:
            await player.set_pause(False)
            await ctx.send('▶ Resumed.')
        else:
            await player.set_pause(True)
            await ctx.send('⏸ Paused.')

    @commands.command()
    async def skip(self, ctx):
        """Skip the current track"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player:
            return await ctx.send('❌ No player found. Use `play` command first.')
        
        if not player.is_playing:
            return await ctx.send('❌ Not playing.')
        
        await player.skip()
        await ctx.send('⏭ Skipped.')
        
        await update_queue_message(player, ctx)

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        """Show the current queue"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player:
            return await ctx.send('❌ No player found. Use `play` command first.')
        
        if not player.queue:
            return await ctx.send('📜 Nothing queued.')

        items_per_page = 10
        pages = []
        
        for page_num in range(0, len(player.queue), items_per_page):
            page_queue = player.queue[page_num:page_num + items_per_page]
            queue_list = []
            
            for i, track in enumerate(page_queue, start=page_num + 1):
                length_ms = getattr(track, 'length', getattr(track, 'duration', 0))
                minutes, seconds = divmod(length_ms // 1000, 60)
                queue_list.append(f'{i}. **{track.title}** - `{minutes}:{seconds:02d}`')
            
            embed = discord.Embed(
                title=f'📜 Queue - Page {len(pages) + 1}',
                description='\n'.join(queue_list),
                color=discord.Color.green()
            )
            
            if player.current:
                current_length_ms = getattr(player.current, 'length', getattr(player.current, 'duration', 0))
                current_minutes, current_seconds = divmod(current_length_ms // 1000, 60)
                embed.add_field(
                    name='Currently Playing',
                    value=f'**{player.current.title}** - `{current_minutes}:{current_seconds:02d}`',
                    inline=False
                )
            
            pages.append(embed)

        await ctx.send(embed=pages[0])

    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx):
        """Show the current playing track"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not player:
            return await ctx.send('❌ No player found. Use `play` command first.')
        
        if not player.current:
            return await ctx.send('❌ Nothing playing.')

        length_ms = player.current.length
        position_ms = player.position
        length_minutes, length_seconds = divmod(length_ms // 1000, 60)
        position_minutes, position_seconds = divmod(position_ms // 1000, 60)

        progress = int((position_ms / length_ms) * 30) if length_ms > 0 else 0
        progress_bar = '█' * progress + '░' * (30 - progress)

        embed = discord.Embed(
            title='🎵 Now Playing',
            description=f'**{player.current.title}**\n{player.current.author}',
            color=discord.Color.blue()
        )

        embed.add_field(
            name='Progress',
            value=f'`{position_minutes}:{position_seconds:02d}` {progress_bar} `{length_minutes}:{length_seconds:02d}`',
            inline=False
        )

        if 'youtube' in player.current.uri:
            embed.set_thumbnail(url=f'https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg')

        embed.add_field(name='Paused', value='Yes' if player.paused else 'No', inline=True)
        embed.add_field(name='Queue Length', value=str(len(player.queue)), inline=True)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
    