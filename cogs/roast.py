import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
from typing import Optional

class Roast(commands.Cog):
    """Clean roasting commands for friendly banter, with optional roast GIF command."""

    def __init__(self, bot):
        self.bot = bot
        
        # Collection of clean, funny roasts
        self.clean_roasts = [
            "{user}, you're like a software update - whenever I see you, I think 'not now.'",
            "{user}, if you were any slower, you'd be going backwards!",
            "{user}, you're not stupid, you just have bad luck thinking.",
            "{user}, you bring everyone so much joy... when you leave the room.",
            "{user}, I'd agree with you, but then we'd both be wrong.",
            "{user}, you're like Monday mornings - nobody's excited to see you.",
            "{user}, if ignorance is bliss, you must be the happiest person alive!",
            "{user}, you're proof that evolution can go in reverse.",
            "{user}, I'm not saying you're dumb, but you'd struggle to pour water out of a boot with instructions on the heel.",
            "{user}, you have an entire life to be an idiot. Why not take today off?",
            "{user}, you're like a cloud - when you disappear, it's a beautiful day.",
            "{user}, I don't know what makes you so stupid, but it really works!",
            "{user}, you're not the dumbest person in the world, but you better hope they don't die.",
            "{user}, if I wanted to kill myself, I'd climb your ego and jump to your IQ.",
            "{user}, you're about as useful as a chocolate teapot.",
            "{user}, I've seen people like you before, but I had to pay admission!",
            "{user}, you're like a participation trophy - everybody gets one, but nobody really wants it.",
            "{user}, if you were a spice, you'd be flour.",
            "{user}, you're not ugly, but you'd have to sneak up on a glass of water.",
            "{user}, you have the perfect face for radio!",
            "{user}, I'd call you a tool, but tools are actually useful.",
            "{user}, you're like a dictionary - you add meaning to my life, but only when I need to look something up.",
            "{user}, if brains were dynamite, you wouldn't have enough to blow your nose.",
            "{user}, you're living proof that anyone can survive without a brain!",
            "{user}, you're like a broken pencil - pointless!",
            "{user}, I'm not insulting you, I'm describing you.",
            "{user}, you're about as sharp as a bowling ball.",
            "{user}, if stupidity burned calories, you'd be a supermodel!",
            "{user}, you're like a GPS - you take forever to get to the point and half the time you're wrong.",
            "{user}, I would roast you, but my mom said I'm not allowed to burn trash.",
            "{user}, you're like a WiFi signal - weak and unreliable.",
            "{user}, if you were a vegetable, you'd be a cabbage - bland and nobody's first choice.",
            "{user}, you're not completely useless - you can always serve as a bad example!",
            "{user}, you have delusions of adequacy.",
            "{user}, you're like a screen door on a submarine - completely pointless!",
        ]

        # Compliment roasts (backhanded compliments)
        self.compliment_roasts = [
            "{user}, you're really unique! Just like everyone else.",
            "{user}, I admire your confidence in being so wrong about everything.",
            "{user}, you have such a great personality! It really makes up for your face.",
            "{user}, you're not as dumb as you look! Wait, that's impossible.",
            "{user}, I love how you're always yourself - authentic mediocrity is rare!",
            "{user}, you have a face only a mother could love... if she were legally blind.",
            "{user}, your sense of humor is great! Too bad you're not funny.",
            "{user}, you're so smart! In an alternate universe where smart means the opposite.",
        ]

    async def get_random_roast(self, user: discord.Member, roast_type: str = "normal") -> str:
        roasts = self.compliment_roasts if roast_type == "compliment" else self.clean_roasts
        return random.choice(roasts).format(user=user.mention)

    @commands.command(name="roast")
    async def roast_prefix(self, ctx: commands.Context, member: Optional[discord.Member] = None, roast_type: str = "normal"):
        target = member or ctx.author
        requester = ctx.author
        roast_message = await self.get_random_roast(target, roast_type)

        embed = discord.Embed(
            title="🔥 ROASTED! 🔥" if roast_type != "compliment" else "💅 BACKHANDED COMPLIMENT! 💅",
            description=roast_message,
            color=discord.Color.red() if roast_type != "compliment" else discord.Color.purple()
        )
        embed.set_author(name=f"Requested by {requester.display_name}", icon_url=requester.display_avatar.url)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="This is all in good fun! Don't take it seriously 😄")
        embed.timestamp = discord.utils.utcnow()

        await ctx.send(embed=embed)

    @app_commands.command(name="roast", description="Roast someone with a clean, funny insult!")
    @app_commands.describe(member="The person to roast (optional)", roast_type="Type of roast: normal or compliment")
    async def roast_slash(self, interaction: discord.Interaction, member: Optional[discord.Member] = None, roast_type: Optional[str] = None):
        target = member or interaction.user
        requester = interaction.user
        roast_style = roast_type or "normal"
        roast_message = await self.get_random_roast(target, roast_style)

        embed = discord.Embed(
            title="🔥 ROASTED! 🔥" if roast_style != "compliment" else "💅 BACKHANDED COMPLIMENT! 💅",
            description=roast_message,
            color=discord.Color.red() if roast_style != "compliment" else discord.Color.purple()
        )
        embed.set_author(name=f"Requested by {requester.display_name}", icon_url=requester.display_avatar.url)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="This is all in good fun! Don't take it seriously 😄")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)


    @roast_slash.autocomplete('roast_type')
    async def roast_type_autocomplete(self, interaction: discord.Interaction, current: str):
        choices = [
            app_commands.Choice(name="Normal Roast", value="normal"),
            app_commands.Choice(name="Backhanded Compliment", value="compliment"),
        ]
        return [choice for choice in choices if current.lower() in choice.name.lower()]

async def setup(bot):
    await bot.add_cog(Roast(bot))
