# cogs/utility.py
import discord
import platform
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
from utils import log_command
from typing import Optional

class MyView(View):
    """Simple button view for testing"""
    
    @discord.ui.button(label="Say Hello", style=discord.ButtonStyle.green)
    async def hello_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Hello! 👋", ephemeral=True)

class Utility(commands.Cog):
    """Utility commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="List all available commands")
    @log_command
    async def dynamic_help(self, ctx):
        """Command to dynamically generate a help message with all commands."""
        embed = discord.Embed(
            title="✨ Rajjo Gujjar 💕 Bot - Command List",
            description="Here are all the commands you can use:",
            color=discord.Color.purple()
        )
        
        for command in self.bot.commands:
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

    @commands.command(help="Check if the bot is running")
    @log_command
    async def up(self, ctx):
        """Command to check if the bot is running."""
        await ctx.send("Got your message! Server is up and running! 💕")

    @commands.command(help="Check bot and API latency")
    @log_command
    async def ping(self, ctx):
        """Check bot and API latency"""
        # Calculate latencies
        bot_latency = round(self.bot.latency * 1000, 2)  # in ms
        shard_id = ctx.guild.shard_id if ctx.guild and ctx.guild.shard_id is not None else 0
        
        try:
            shard_latency = round(self.bot.shards[shard_id].latency * 1000, 2)
        except (AttributeError, KeyError):
            shard_latency = bot_latency

        embed = discord.Embed(
            title="Pong! 💕",
            description="**Response!**",
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
    
        # New slash command
    @app_commands.command(name="ping", description="Check bot and API latency")
    async def ping_slash(self, interaction: discord.Interaction):
        bot_latency = round(self.bot.latency * 1000, 2)  # in ms
        shard_id = interaction.guild.shard_id if interaction.guild and interaction.guild.shard_id is not None else 0

        try:
            shard_latency = round(self.bot.shards[shard_id].latency * 1000, 2)
        except (AttributeError, KeyError):
            shard_latency = bot_latency

        embed = discord.Embed(
            title="Pong! 💕",
            description="**Response!**",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Bot Latency", value=f"{bot_latency}ms", inline=True)
        embed.add_field(name="Shard", value=f"{shard_id}", inline=True)
        embed.add_field(name="Shard Latency", value=f"{shard_latency}ms", inline=True)
        embed.add_field(name="Node", value=platform.node(), inline=False)
        embed.set_footer(text="Time")
        embed.set_thumbnail(url="https://i.postimg.cc/nr25D2YG/5d07ad02-b75f-4eb2-b454-77a0e67b39a8.png")

        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Shows information about a user.")
    @app_commands.describe(member="User to inspect (optional)")
    @app_commands.guild_only()
    async def userinfo(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        embed = discord.Embed(title=f"{target}'s Info", color=discord.Color.blue())
        embed.add_field(name="ID", value=(f"`{target.id}`"), inline=True)
        embed.add_field(name="Display Name", value=getattr(target, "display_name", target.name), inline=True)

        joined_at = getattr(target, "joined_at", None)
        created_at = getattr(target, "created_at", None)
        embed.add_field(
            name="Joined Server At",
            value=joined_at.strftime("`%Y-%m-%d %H:%M:%S`") if joined_at else "`Unknown`",
            inline=False
        )
        embed.add_field(
            name="Account Created At",
            value=created_at.strftime("`%Y-%m-%d %H:%M:%S`") if created_at else "`Unknown`",
            inline=False
        )

        roles = [r.name for r in getattr(target, "roles", []) if r.name != "@everyone"]
        embed.add_field(name=f"Roles (`{len(roles)}`)", value=", ".join(roles) if roles else "`No roles`", inline=False)
        embed.set_thumbnail(url=target.display_avatar.url if hasattr(target, "display_avatar") else target.avatar.url)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)


    @commands.command(help="Shows information about a user.")
    @log_command
    async def userinfo(self, ctx, member: discord.Member = None):
        """Shows information about a user"""
        member = member or ctx.author
        
        embed = discord.Embed(title=f"{member}'s Info", color=discord.Color.blue())
        embed.add_field(name="ID", value=(f"`{member.id}`"), inline=True)
        embed.add_field(name="Display Name", value=(f"`{member.display_name}`"), inline=True)
        embed.add_field(name="Joined Server At", value=member.joined_at.strftime("`%Y-%m-%d %H:%M:%S`"), inline=False)
        embed.add_field(name="Account Created At", value=member.created_at.strftime("`%Y-%m-%d %H:%M:%S`"), inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        roles = [role.name for role in member.roles if role.name != "@everyone"]
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles) if roles else "No roles", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(help="Shows detailed information about the server.")
    @log_command
    async def serverinfo(self, ctx):
        """Shows detailed information about the server"""
        guild = ctx.guild
        owner = guild.owner
        
        if owner is None:
            owner = await self.bot.fetch_user(guild.owner_id)

        embed = discord.Embed(
            title=f"Server Info - {guild.name}",
            color=discord.Color.green(),
            timestamp=guild.created_at
        )

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

        # Roles
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)

        embed.set_footer(text=f"Server ID: {guild.id}")
        await ctx.send(embed=embed)

    @commands.command(help="Send a markdown message to a specified channel by name or ID, optionally inside an embed")
    @log_command
    async def markdown(self, ctx, channel: str, embed: bool = True, *, markdown_text: str):
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

        await ctx.send(f"✅ Message posted to {target_channel.mention} {'(embed)' if embed else '(plain text)'}")

    @commands.command(help="Shows a button you can click.")
    @log_command
    async def button(self, ctx):
        """Shows a button you can click"""
        view = MyView()
        await ctx.send("Press the button!", view=view)

async def setup(bot):
    await bot.add_cog(Utility(bot))