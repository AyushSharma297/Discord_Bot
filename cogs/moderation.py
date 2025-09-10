# cogs/moderation.py
import discord
import random
from discord.ext import commands

class Moderation(commands.Cog):
    """Moderation commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.log_channels = {}  # Dictionary to store guild_id : log_channel_id mapping

    @commands.command(help="Delete a specified number of previous messages. Usage: !purge <count>")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, count: int):
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
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need the **Manage Messages** permission to use this command.")

    @commands.command(help="Set the log channel by name. Usage: !setlog <channel_name>")
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, *, channel_name: str):
        """Set the log channel by name"""
        guild = ctx.guild
        
        # Find channel by name (case-insensitive)
        channel = discord.utils.get(guild.text_channels, name=channel_name.lower())
        
        if channel is None:
            await ctx.send(f"❌ Could not find a text channel named `{channel_name}`. Please check the name and try again.")
            return
        
        # Save to dictionary
        self.log_channels[guild.id] = channel.id
        await ctx.send(f"✅ Logging channel set to {channel.mention}")

    @setlog.error
    async def setlog_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need Administrator permission to use this command.")

    @commands.command(help="Unset the log channel for this server.")
    @commands.has_permissions(administrator=True)
    async def unsetlog(self, ctx):
        """Unset the log channel for this server"""
        guild_id = ctx.guild.id
        
        if guild_id in self.log_channels:
            del self.log_channels[guild_id]
            await ctx.send("✅ Log channel unset for this server.")
        else:
            await ctx.send("ℹ️ No log channel was set for this server.")

    @unsetlog.error
    async def unsetlog_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need Administrator permission to use this command.")

    @commands.command(help="Start a giveaway: !giveaway <time_in_seconds> <prize>")
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx, time: int = None, *, prize: str = None):
        """Start a giveaway"""
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

    # Event listeners for message logging
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log deleted messages"""
        guild_id = message.guild.id if message.guild else None
        if not guild_id or guild_id not in self.log_channels:
            return
        
        log_channel = self.bot.get_channel(self.log_channels[guild_id])
        if not log_channel or message.author.bot:
            return
        
        embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
        embed.add_field(name="Author", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Content", value=message.content or "No content", inline=False)
        embed.timestamp = discord.utils.utcnow()
        
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Log edited messages"""
        guild_id = before.guild.id if before.guild else None
        if not guild_id or guild_id not in self.log_channels:
            return
        
        log_channel = self.bot.get_channel(self.log_channels[guild_id])
        if not log_channel or before.author.bot or before.content == after.content:
            return
        
        embed = discord.Embed(title="Message Edited", color=discord.Color.orange())
        embed.add_field(name="Author", value=f"{before.author} ({before.author.id})", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=before.content or "No content", inline=False)
        embed.add_field(name="After", value=after.content or "No content", inline=False)
        embed.timestamp = discord.utils.utcnow()
        
        await log_channel.send(embed=embed)

class GiveawayView(discord.ui.View):
    """View for giveaway functionality"""
    
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
        """Handle giveaway timeout"""
        if self.entries:
            winner_id = random.choice(list(self.entries))
            winner = self.message.guild.get_member(winner_id)
        else:
            winner = None

        # Disable button after timeout
        for child in self.children:
            child.disabled = True

        if winner:
            content = f"🎉 Congratulations {winner.mention}! You won **{self.prize}**!"
        else:
            content = "No valid entries, giveaway canceled."

        if self.message:
            await self.message.edit(content=content, view=self)

async def setup(bot):
    await bot.add_cog(Moderation(bot))