# main.py - Main bot file
import discord
import asyncio
import logging
import os
import aiosqlite
import lavalink
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands

# Load environment variables
load_dotenv()
Bot_token = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

# Ensure /data directory exists
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "chat_log.db")

# Database initialization
async def init_db():
    if not os.path.isfile(DB_FILE):
        open(DB_FILE, "a").close()
    
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT,
                user TEXT,
                user_message TEXT,
                bot_response TEXT,
                location TEXT,
                channel_id INTEGER,
                server TEXT
            )
        """)
        await db.commit()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents,  help_command=None)

# Custom Lavalink Voice Client
class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        lavalink_data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        lavalink_data = {'t': 'VOICE_STATE_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        if not force and not player.is_connected:
            return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()

# Store the voice client class for cogs to use
bot.LavalinkVoiceClient = LavalinkVoiceClient

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and logged in."""
    await init_db()
    activity = discord.Game(name="Stealing Hearts 💕")
    
    # Initialize Lavalink
    bot.lavalink = lavalink.Client(bot.user.id)
    bot.lavalink.add_node(
        'localhost',  # Host
        2333,  # Port
        'youshallnotpass',  # Password
        'us',  # Region
        'default-node'  # Name
    )
    
    await bot.change_presence(status=discord.Status.online, activity=activity)
    logging.info(f"Logged in as {bot.user} and status set.(ID: {bot.user.id})")

# Load cogs
async def load_cogs():
    """Load all cogs"""
    initial_cogs = [
        'cogs.music',
        'cogs.moderation', 
        'cogs.utility',
        'cogs.ai_chat',
        'cogs.fun',
        'cogs.events',
        'cogs.roast'
    ]
    
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Global command error handler"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param}`")
    else:
        print(f"Error in {ctx.command}: {error}")
        await ctx.send("❌ An error occurred while executing this command.")

# Development commands for cog management
@bot.command(hidden=True)
@commands.is_owner()
async def reload(ctx, *, cog_name):
    """Reload a cog"""
    try:
        await bot.reload_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ Reloaded cogs.{cog_name}")
    except Exception as e:
        await ctx.send(f"❌ Error reloading cogs.{cog_name}: {e}")

@bot.command(hidden=True)
@commands.is_owner()
async def load(ctx, *, cog_name):
    """Load a cog"""
    try:
        await bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ Loaded cogs.{cog_name}")
    except Exception as e:
        await ctx.send(f"❌ Error loading cogs.{cog_name}: {e}")

@bot.command(hidden=True)
@commands.is_owner()
async def unload(ctx, *, cog_name):
    """Unload a cog"""
    try:
        await bot.unload_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ Unloaded cogs.{cog_name}")
    except Exception as e:
        await ctx.send(f"❌ Error unloading cogs.{cog_name}: {e}")

# Main execution
async def main():
    async with bot:
        await load_cogs()
        await bot.start(Bot_token)

if __name__ == "__main__":
    asyncio.run(main())