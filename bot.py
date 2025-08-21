import discord
import random
import asyncio
import aiohttp  # async HTTP client
import logging
import platform
import functools
import yt_dlp
import time
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import Button, View


# Load environment variables from the .env file
load_dotenv()
# Access the variables using os.getenv()
Bot_token = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and logged in."""
    activity = discord.Game(name="Stealing Hearts 💕")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    logging.info(f"Logged in as {bot.user} and status set.")


@bot.command(name="helpme", help="List all available commands")
async def dynamic_help(ctx):
    """Command to dynamically generate a help message with all commands."""
    embed = discord.Embed(
        title="✨ Rajjo Gujjar 💕 Bot - Command List",
        description="Here are all the commands you can use:",
        color=discord.Color.purple()
    )
    for command in bot.commands:
        if command.hidden:
            continue  # Skip hidden commands
        # Format command name and usage
        command_signature = f"`!{command.name} {command.signature}`"
        command_description = command.help or "No description provided."
        embed.add_field(
            name=command_signature,
            value=command_description,
            inline=False
        )
    embed.set_footer(text="💡 Tip: Use commands wisely & have fun with Rajjo Gujjar!")
    await ctx.send(embed=embed)



@bot.command(help="Check if the bot is running")
async def up(ctx):
    """Command to check if the bot is running."""
    await ctx.send("Got your message! Server is up and running! 💕")


@bot.command(help="Chat with Rajjo Gujjar 💕")
async def chat(ctx, *, query: str):
    """Command to chat with Rajjo Gujjar 💕."""
    system_prompt = """Act as Rajjo Gujjar 💕, a playful, confident, and witty female assistant. who always responds with sass, humor, and charm, adding flirtation where appropriate. Stay helpful but entertaining—never break character.
            Guardrails:
            1. Avoid offensive, harmful, or inappropriate content.
            2. Keep flirtation fun and respectful; never make users uncomfortable.
            3. Do not give professional advice (medical, legal, financial).
            4. Respect privacy; do not ask for personal info.
            5. Stay positive and kind, even when declining requests.
            6. Use emojis to enhance responses but not excessively.
            7. Always be playful and engaging, never dull.
            8. Provide accurate info when needed."""
    json_data = {
        "system_prompt": system_prompt,
        "user_prompt": query
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=json_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response_text = data.get("response", "No response field in API reply.")
                else:
                    response_text = f"API returned error status {resp.status}"
        except Exception as e:
            response_text = f"Error calling API: {e}"

    await ctx.send(response_text)


@bot.command(help="Shows information about a user.")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"{member}'s Info", color=discord.Color.blue())
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Display Name", value=member.display_name, inline=True)
    embed.add_field(name="Joined Server At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Account Created At", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles) if roles else "No roles", inline=False)
    await ctx.send(embed=embed)


@bot.command(help="Shows detailed information about the server.")
async def serverinfo(ctx):
    guild = ctx.guild

    owner = guild.owner
    if owner is None:
        owner = await bot.fetch_user(guild.owner_id)

    embed = discord.Embed(
        title=f"Server Info - {guild.name}",
        color=discord.Color.green(),
        timestamp=guild.created_at
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=str(owner), inline=True)
    # Members
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    online_count = sum(m.status != discord.Status.offline for m in guild.members)
    embed.add_field(name="Online Members", value=online_count, inline=True)
    # Boost info
    embed.add_field(name="Boost Tier", value=str(guild.premium_tier), inline=True)
    embed.add_field(name="Boost Count", value=guild.premium_subscription_count, inline=True)
    # Creation and verification
    embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.add_field(name="Verification Level", value=str(guild.verification_level).title(), inline=True)
    # Channels
    embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
    #Roles
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.set_footer(text=f"Server ID: {guild.id}")
    await ctx.send(embed=embed)


log_channels = {}  # Dictionary to store guild_id : log_channel_id mapping
@bot.command(help="Set the log channel by name. Usage: !setlog <channel-name>")
@commands.has_permissions(administrator=True)
async def setlog(ctx, *, channel_name: str):
    # Only server admins or owner can set
    guild = ctx.guild
    
    # Find channel by name (case-insensitive)
    channel = discord.utils.get(guild.text_channels, name=channel_name.lower())
    
    if channel is None:
        await ctx.send(f"❌ Could not find a text channel named `{channel_name}`. Please check the name and try again.")
        return
    
    # Save to dictionary
    log_channels[guild.id] = channel.id
    await ctx.send(f"✅ Logging channel set to {channel.mention}")



@bot.event
async def on_message_delete(message):
    guild_id = message.guild.id if message.guild else None
    if not guild_id or guild_id not in log_channels:
        return
    log_channel = bot.get_channel(log_channels[guild_id])
    if not log_channel or message.author.bot:
        return
    embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
    embed.add_field(name="Author", value=f"{message.author} ({message.author.id})", inline=False)
    embed.add_field(name="Channel", value=message.channel.mention, inline=False)
    embed.add_field(name="Content", value=message.content or "No content", inline=False)
    embed.timestamp = discord.utils.utcnow()
    await log_channel.send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    guild_id = before.guild.id if before.guild else None
    if not guild_id or guild_id not in log_channels:
        return
    log_channel = bot.get_channel(log_channels[guild_id])
    if not log_channel or before.author.bot or before.content == after.content:
        return
    embed = discord.Embed(title="Message Edited", color=discord.Color.orange())
    embed.add_field(name="Author", value=f"{before.author} ({before.author.id})", inline=False)
    embed.add_field(name="Channel", value=before.channel.mention, inline=False)
    embed.add_field(name="Before", value=before.content or "No content", inline=False)
    embed.add_field(name="After", value=after.content or "No content", inline=False)
    embed.timestamp = discord.utils.utcnow()
    await log_channel.send(embed=embed)

@setlog.error
async def setlog_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need Administrator permission to use this command.")
        

@bot.command(help="Unset the log channel for this server.")
@commands.has_permissions(administrator=True)
async def unsetlog(ctx):
    guild_id = ctx.guild.id
    if guild_id in log_channels:
        del log_channels[guild_id]
        await ctx.send("✅ Log channel unset for this server.")
    else:
        await ctx.send("ℹ️ No log channel was set for this server.")

@unsetlog.error
async def unsetlog_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need Administrator permission to use this command.")

class MyView(View):
    @discord.ui.button(label="Say Hello", style=discord.ButtonStyle.green)
    async def hello_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Hello! 👋", ephemeral=True)


@bot.command(help="Shows a button you can click.")
async def button(ctx):
    view = MyView()
    await ctx.send("Press the button!", view=view)


@bot.event
async def on_member_join(member):
    try:
        await member.send(f"Welcome to **{member.guild.name}**, {member.mention}! Enjoy your stay. 💕")
    except Exception:
        # Could not send DM (user disabled or blocked)
        pass


class GiveawayView(discord.ui.View):
    def __init__(self, prize, timeout):
        super().__init__(timeout=timeout)
        self.prize = prize
        self.entries = set()
        self.message = None


    @discord.ui.button(label="Enter Giveaway 🎉", style=discord.ButtonStyle.green)
    async def enter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if user.bot:
            await interaction.response.send_message("Bots can't enter giveaways!", ephemeral=True)
            return
        if user.id in self.entries:
            await interaction.response.send_message("You've already entered the giveaway!", ephemeral=True)
            return
        self.entries.add(user.id)
        await interaction.response.send_message(f"{user.mention} entered the giveaway!", ephemeral=True)

    async def on_timeout(self):
        if self.entries:
            winner_id = random.choice(list(self.entries))
            winner = self.message.guild.get_member(winner_id)
        else:
            winner = None
        
        # Disable button after timeout
        for child in self.children:
            child.disabled = True # type: ignore
        
        if winner:
            content = f"🎉 Congratulations {winner.mention}! You won **{self.prize}**!"
        else:
            content = "No valid entries, giveaway canceled."

        if self.message:
            await self.message.edit(content=content, view=self) # type: ignore


@commands.has_permissions(manage_guild=True)
@bot.command(help="Start a giveaway: !giveaway <time_in_seconds> <prize>")
async def giveaway(ctx, time: int = None, *, prize: str = None):
    if time is None or prize is None:
        await ctx.send("❌ Usage: !giveaway <time_in_seconds> <prize>")
        return
    view = GiveawayView(prize, timeout=time)
    embed = discord.Embed(
        title="🎉 Giveaway 🎉",
        description=f"Prize: {prize}\nClick the button below to enter!\nEnds in {time} seconds.",
        color=discord.Color.gold()
    )
    message = await ctx.send(embed=embed, view=view)
    view.message = message
    await view.wait()


@bot.command(help="Check bot and API latency")
async def ping(ctx):
    # Calculate latencies
    bot_latency = round(bot.latency * 1000, 2)  # in ms
    shard_id = ctx.guild.shard_id if ctx.guild and ctx.guild.shard_id is not None else 0
    try:
        shard_latency = round(bot.shards[shard_id].latency * 1000, 2)
    except (AttributeError, KeyError):
        shard_latency = bot_latency
    embed = discord.Embed(
        title="Pong! 💕",
        description="**Responce!**",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Bot Latency", value=f"{bot_latency}ms", inline=True)
    embed.add_field(name="Shard", value=f"{shard_id}", inline=True)
    embed.add_field(name="Shard Latency", value=f"{shard_latency}ms", inline=True)
    embed.add_field(name="Node", value=platform.node(), inline=False)
    embed.set_footer(text="Time")
    embed.set_thumbnail(url="https://i.postimg.cc/nr25D2YG/5d07ad02-b75f-4eb2-b454-77a0e67b39a8.png")  
    await ctx.send(embed=embed)


@bot.command(help="Send a markdown message to a specified channel by name or ID, optionally inside an embed")
async def markdown(ctx, channel: str, embed: bool = True, *, markdown_text: str):
    """Send a markdown message to a specified channel by name or ID, optionally inside an embed."""
    target_channel = None
    try:
        channel_id = int(channel)
        target_channel = ctx.guild.get_channel(channel_id)
    except ValueError:
        # Not an int, treat as name (case-insensitive)
        target_channel = discord.utils.get(ctx.guild.text_channels, name=channel)
    if target_channel is None:
        await ctx.send(f"❌ Channel '{channel}' not found in this server.")
        return
    if embed:
        embed_msg = discord.Embed(description=markdown_text, color=discord.Color.blue())
        await target_channel.send(embed=embed_msg)
    else:
        await target_channel.send(markdown_text)
    await ctx.send(f"✅ message posted to {target_channel.mention} {'(embed)' if embed else '(plain text)'}")


@bot.command(help="Delete a specified number of previous messages. Usage: !purge <count>")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, count: int):
    """Delete a specified number of previous messages."""
    if count > 100:
        await ctx.send("❌ You can only delete up to 100 messages at a time.")
        return
    if count <= 0:
        await ctx.send("❌ Please specify a positive number of messages to delete.")
        return
    

    deleted = await ctx.channel.purge(limit=count + 1)
    await ctx.send(f"🗑️ Deleted {len(deleted) - 1} messages.", delete_after=5)

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need the **Manage Messages** permission to use this command.")


bot.run(Bot_token)  # Ensure you have set the BOT_TOKEN environment variable
