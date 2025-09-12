# cogs/events.py
import discord
from discord.ext import commands

class Events(commands.Cog):
    """Event handlers for the bot"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message to new members"""
        try:
            await member.send(f"Welcome to **{member.guild.name}**, {member.mention}! Enjoy your stay. 💕")
        except Exception:
            # Could not send DM (user disabled or blocked)
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates for Lavalink"""
        # Only process bot's own voice state changes
        if member.id == self.bot.user.id:
            await self.bot.lavalink.voice_update_handler({
                't': 'VOICE_STATE_UPDATE',
                'd': {
                    'guild_id': str(member.guild.id),
                    'user_id': str(member.id),
                    'session_id': after.session_id if after else None,
                    'channel_id': str(after.channel.id) if after and after.channel else None
                }
            })

    @commands.Cog.listener()
    async def on_raw_voice_server_update(self, payload):
        """Handle voice server updates for Lavalink"""
        await self.bot.lavalink.voice_update_handler({
            't': 'VOICE_SERVER_UPDATE',
            'd': payload
        })

async def setup(bot):
    await bot.add_cog(Events(bot))
    