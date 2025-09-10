# cogs/fun.py
import discord
import random
import aiohttp
import logging
from typing import List, Optional, Dict, Set, Literal
from discord import app_commands
from discord.ext import commands

# --------- Game State Models ---------
class RRMode:
    def __init__(self, name: str, chambers: int = 6, bullets: int = 1, spin_each_turn: bool = True):
        self.name = name
        self.chambers = chambers
        self.bullets = bullets
        self.spin_each_turn = spin_each_turn

MODES: Dict[str, RRMode] = {
    "normal": RRMode("Normal", chambers=6, bullets=1, spin_each_turn=True),       # 1/6 each pull
    "hard": RRMode("Hard", chambers=6, bullets=2, spin_each_turn=True),           # 2/6 each pull
    "hardcore": RRMode("Hardcore", chambers=6, bullets=1, spin_each_turn=False),  # cylinder advances; no spin
}

class RRGame:
    def __init__(self, channel: discord.TextChannel, host: discord.Member, mode: RRMode, ante: int):
        self.channel = channel
        self.host = host
        self.mode = mode
        self.ante = ante
        self.players: List[discord.Member] = []
        self.alive: Set[int] = set()
        self.current_index: int = 0
        self.started: bool = False
        self.message: Optional[discord.Message] = None

        # Cylinder state for hardcore (no spin each turn)
        self.cylinder_pos: int = random.randrange(self.mode.chambers)
        bullet_slots = set()
        while len(bullet_slots) < self.mode.bullets:
            bullet_slots.add(random.randrange(self.mode.chambers))
        self.bullet_slots: Set[int] = bullet_slots

    def add_player(self, m: discord.Member) -> bool:
        if self.started or m.id in self.alive:
            return False
        self.players.append(m)
        self.alive.add(m.id)
        return True

    def remove_player(self, m: discord.Member) -> bool:
        if m.id not in self.alive:
            return False
        self.alive.remove(m.id)
        return True

    def next_living_index(self) -> Optional[int]:
        if len(self.alive) <= 1:
            return None
        for _ in range(len(self.players)):
            self.current_index = (self.current_index + 1) % len(self.players)
            if self.players[self.current_index].id in self.alive:
                return self.current_index
        return None

    def current_player(self) -> Optional[discord.Member]:
        if not self.players:
            return None
        if self.players[self.current_index].id not in self.alive:
            ni = self.next_living_index()
            if ni is None:
                return None
        return self.players[self.current_index]

    def pull_trigger(self) -> bool:
        if self.mode.spin_each_turn:
            chamber = random.randrange(self.mode.chambers)
            return chamber in self.bullet_slots
        else:
            dead = self.cylinder_pos in self.bullet_slots
            self.cylinder_pos = (self.cylinder_pos + 1) % self.mode.chambers
            return dead

    def winner(self) -> Optional[discord.Member]:
        if len(self.alive) == 1:
            pid = next(iter(self.alive))
            for p in self.players:
                if p.id == pid:
                    return p
        return None

# --------- Views ---------
class LobbyView(discord.ui.View):
    def __init__(self, game: RRGame, author: discord.Member, timeout: Optional[float] = 60.0):
        super().__init__(timeout=timeout)
        self.game = game
        self.author = author

    def _is_host(self, user: discord.abc.User) -> bool:
        return user.id == self.game.host.id

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.game.message:
            await self.game.message.edit(view=self)

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success, emoji="➕")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.started:
            return await interaction.response.send_message("Game already started.", ephemeral=True)
        if interaction.user.id in self.game.alive:
            return await interaction.response.send_message("Already joined.", ephemeral=True)
        added = self.game.add_player(interaction.user)  # type: ignore
        if not added:
            return await interaction.response.send_message("Cannot join right now.", ephemeral=True)
        await interaction.response.send_message(f"{interaction.user.mention} joined the roulette.", ephemeral=True)
        await self._refresh_embed()

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.secondary, emoji="➖")
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.game.alive:
            return await interaction.response.send_message("Not in the lobby.", ephemeral=True)
        self.game.remove_player(interaction.user)  # type: ignore
        await interaction.response.send_message(f"{interaction.user.mention} left the roulette.", ephemeral=True)
        await self._refresh_embed()

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary, emoji="🎲")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_host(interaction.user):
            return await interaction.response.send_message("Only the host can start.", ephemeral=True)
        if len(self.game.alive) < 2:
            return await interaction.response.send_message("Need at least 2 players.", ephemeral=True)
        self.game.started = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        gv = GameView(self.game)
        await gv.post_or_update()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🛑")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_host(interaction.user):
            return await interaction.response.send_message("Only the host can cancel.", ephemeral=True)
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Roulette lobby cancelled.", view=self)

    async def _refresh_embed(self):
        if not self.game.message:
            return
        embed = build_lobby_embed(self.game)
        await self.game.message.edit(embed=embed, view=self)

class GameView(discord.ui.View):
    def __init__(self, game: RRGame, timeout: Optional[float] = 180.0):
        super().__init__(timeout=timeout)
        self.game = game

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.game.message:
            await self.game.message.edit(view=self)

    async def post_or_update(self):
        cur = self.game.current_player()
        embed = build_game_embed(self.game, cur)
        if self.game.message:
            await self.game.message.edit(content=None, embed=embed, view=self)
        else:
            self.game.message = await self.game.channel.send(embed=embed, view=self)

    @discord.ui.button(label="Pull Trigger", style=discord.ButtonStyle.danger, emoji="🔫")
    async def pull(self, interaction: discord.Interaction, button: discord.ui.Button):
        cur = self.game.current_player()
        if cur is None:
            w = self.game.winner()
            if w:
                return await interaction.response.send_message(f"Game already finished. Winner: {w.mention}", ephemeral=True)
            return await interaction.response.send_message("No active player.", ephemeral=True)

        if interaction.user.id != cur.id:
            return await interaction.response.send_message("Not your turn.", ephemeral=True)

        died = self.game.pull_trigger()
        if died:
            self.game.alive.discard(cur.id)
            await interaction.response.send_message(f"💥 {cur.mention} pulled the trigger and died!", ephemeral=False)
            w = self.game.winner()
            if w:
                for item in self.children:
                    item.disabled = True
                if self.game.message:
                    embed = build_win_embed(self.game, w)
                    await self.game.message.edit(embed=embed, view=self)
                return
            self.game.next_living_index()
        else:
            self.game.next_living_index()
            await interaction.response.send_message(f"😮 {cur.mention} survived.", ephemeral=True)

        await self.post_or_update()

    @discord.ui.button(label="Forfeit", style=discord.ButtonStyle.secondary, emoji="🏳️")
    async def forfeit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.game.alive:
            return await interaction.response.send_message("Not in this game.", ephemeral=True)
        cur = self.game.current_player()
        self.game.alive.discard(interaction.user.id)
        await interaction.response.send_message(f"{interaction.user.mention} forfeited.", ephemeral=True)
        if cur and cur.id == interaction.user.id:
            self.game.next_living_index()
        w = self.game.winner()
        if w:
            for item in self.children:
                item.disabled = True
            if self.game.message:
                embed = build_win_embed(self.game, w)
                return await self.game.message.edit(embed=embed, view=self)
        await self.post_or_update()

# --------- Embeds ---------
def build_lobby_embed(game: RRGame) -> discord.Embed:
    em = discord.Embed(
        title=f"Russian Roulette Lobby — {game.mode.name}",
        description="Press Join to enter; host can Start when ready.",
        color=discord.Color.blurple()
    )
    plist = "\n".join(f"{i+1}. {p.mention}" for i, p in enumerate(game.players) if p.id in game.alive) or "No players yet"
    em.add_field(name="Players", value=plist, inline=False)
    em.add_field(name="Chambers", value=str(game.mode.chambers))
    em.add_field(name="Bullets", value=str(game.mode.bullets))
    em.add_field(name="Spin Each Turn", value="Yes" if game.mode.spin_each_turn else "No")
    if game.ante > 0:
        em.add_field(name="Pot (display only)", value=f"{game.ante * len(game.alive)}", inline=False)
    em.set_footer(text=f"Host: {game.host.display_name}")
    return em

def build_game_embed(game: RRGame, current: Optional[discord.Member]) -> discord.Embed:
    em = discord.Embed(
        title=f"Russian Roulette — {game.mode.name}",
        color=discord.Color.red()
    )
    lines = []
    for i, p in enumerate(game.players):
        alive = "🟢" if p.id in game.alive else "🔴"
        turn = "➡️" if current and p.id == current.id else ""
        lines.append(f"{alive} {p.mention} {turn}")
    em.description = "\n".join(lines) or "No players"
    em.add_field(name="Chambers", value=str(game.mode.chambers))
    em.add_field(name="Bullets", value=str(game.mode.bullets))
    em.add_field(name="Spin Each Turn", value="Yes" if game.mode.spin_each_turn else "No")
    if game.ante > 0:
        em.add_field(name="Pot (display only)", value=f"{game.ante * len(game.alive)}", inline=False)
    return em

def build_win_embed(game: RRGame, winner: discord.Member) -> discord.Embed:
    em = discord.Embed(
        title=f"🏆 Winner: {winner.display_name}",
        description=f"{winner.mention} survived the roulette.",
        color=discord.Color.green()
    )
    if game.ante > 0:
        em.add_field(name="Pot (display only)", value=f"{game.ante * (len(game.players))}")
    return em

# --------- Cog ---------
class Fun(commands.Cog):
    """Fun commands and games for the bot"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._games: Dict[int, RRGame] = {}  # channel_id -> game

    # ---- Prefix command (kept) ----
    @commands.command(name="roulette", aliases=["rr"])
    @commands.guild_only()
    async def roulette_prefix(
        self,
        ctx: commands.Context,
        mode: Optional[str] = "normal",
        ante: Optional[int] = 0
    ):
        mode_key = (mode or "normal").lower()
        if mode_key not in MODES:
            return await ctx.reply(f"Unknown mode '{mode}'. Choose: normal | hard | hardcore")

        if ctx.channel.id in self._games:
            return await ctx.reply("A roulette game is already running in this channel.")

        ante_val = max(0, int(ante or 0))
        game = RRGame(channel=ctx.channel, host=ctx.author, mode=MODES[mode_key], ante=ante_val)
        game.add_player(ctx.author)
        self._games[ctx.channel.id] = game

        lobby = LobbyView(game, ctx.author, timeout=90.0)
        embed = build_lobby_embed(game)
        msg = await ctx.send(embed=embed, view=lobby)
        game.message = msg

        async def wait_and_cleanup():
            await lobby.wait()
            if ctx.channel.id in self._games and not game.started:
                self._games.pop(ctx.channel.id, None)
        self.bot.loop.create_task(wait_and_cleanup())

    @commands.command(name="roulette-cancel")
    @commands.has_permissions(manage_messages=True)
    async def roulette_cancel(self, ctx: commands.Context):
        game = self._games.pop(ctx.channel.id, None)
        if not game:
            return await ctx.reply("No roulette game in this channel.")
        try:
            if game.message:
                await game.message.edit(content="Roulette forcibly cancelled by moderator.", view=None)
        except discord.HTTPException:
            pass
        await ctx.message.add_reaction("✅")

    # ---- Slash command ----
    @app_commands.command(name="roulette", description="Play Russian Roulette")
    @app_commands.describe(mode="Mode: normal | hard | hardcore", ante="Display-only pot amount")
    @app_commands.guild_only()
    async def roulette_slash(
        self,
        interaction: discord.Interaction,
        mode: Literal["normal", "hard", "hardcore"] = "normal",
        ante: app_commands.Range[int, 0, 1_000_000] = 0
    ):
        if interaction.channel is None or not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("This command must be used in a text channel.", ephemeral=True)

        if interaction.channel.id in self._games:
            return await interaction.response.send_message("A roulette game is already running in this channel.", ephemeral=True)

        game = RRGame(channel=interaction.channel, host=interaction.user, mode=MODES[mode], ante=int(ante))
        game.add_player(interaction.user)  # type: ignore

        self._games[interaction.channel.id] = game
        lobby = LobbyView(game, interaction.user, timeout=90.0)
        embed = build_lobby_embed(game)
        await interaction.response.send_message(embed=embed, view=lobby)
        msg = await interaction.original_response()
        game.message = msg

        async def wait_and_cleanup():
            await lobby.wait()
            if interaction.channel and interaction.channel.id in self._games and not game.started:
                self._games.pop(interaction.channel.id, None)
        self.bot.loop.create_task(wait_and_cleanup())

    # ---- On-demand sync helper (optional) ----
    @commands.command(name="sync-roulette")
    @commands.has_permissions(manage_guild=True)
    async def sync_roulette(self, ctx: commands.Context, scope: Optional[str] = None):
        """
        Sync slash commands.
        Usage:
          - !sync-roulette        -> global sync (slow to propagate)
          - !sync-roulette ~      -> sync to this guild only (instant)
        """
        try:
            if scope == "~":
                synced = await self.bot.tree.sync(guild=ctx.guild)
                return await ctx.reply(f"Synced {len(synced)} app commands to this guild.")
            else:
                synced = await self.bot.tree.sync()
                return await ctx.reply(f"Globally synced {len(synced)} app commands (may take up to 1 hour to appear).")
        except Exception as e:
            return await ctx.reply(f"Sync failed: {e}")
    
    async def fetch_reddit_meme(self, sort_type="hot", time_filter="day", subreddit="memes"):
        """Fetch a random meme from Reddit using their public JSON API with sorting options"""
        try:
            headers = {"User-Agent": "DiscordBot:MemeBot:v1.0 (by u/yourname)"}
            
            # Build URL based on sort type and time filter
            base_url = f"https://www.reddit.com/r/{subreddit}/{sort_type}.json"
            params = {"limit": 100}
            
            # Add time filter for 'top' and 'controversial' sorts
            if sort_type in ['top', 'controversial']:
                params['t'] = time_filter
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        posts = data["data"]["children"]
                        
                        # Filter for image posts only
                        image_posts = []
                        for post in posts:
                            post_data = post["data"]
                            url_lower = post_data.get("url", "").lower()
                            
                            # Check if it's an image and not NSFW/stickied
                            if (not post_data.get("over_18", True) and 
                                not post_data.get("stickied", False) and
                                (url_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) or 
                                 'i.redd.it' in url_lower or 'i.imgur.com' in url_lower)):
                                
                                image_posts.append(post_data)
                        
                        if image_posts:
                            return random.choice(image_posts)
                            
        except Exception as e:
            print(f"Error fetching meme: {e}")
        
        return None

    @commands.command(name="meme")
    async def meme_prefix(self, ctx, sort_type: str = "best", time_filter: str = "day"):
        """Fetch a random meme from r/memes with sorting options
        
        Sort types: hot, new, top, rising, controversial
        Time filters (for top/controversial): hour, day, week, month, year, all
        """
        valid_sorts = ['best','hot', 'new', 'top', 'rising', 'controversial']
        valid_times = ['hour', 'day', 'week', 'month', 'year', 'all']
        
        if sort_type not in valid_sorts:
            return await ctx.send(f"Invalid sort type. Use: {', '.join(valid_sorts)}")
        
        if time_filter not in valid_times:
            return await ctx.send(f"Invalid time filter. Use: {', '.join(valid_times)}")

        async with ctx.typing():
            meme_data = await self.fetch_reddit_meme(sort_type, time_filter)
        
        if not meme_data:
            return await ctx.send("Could not fetch a meme right now. Try again later!")

        embed = discord.Embed(
            title=meme_data["title"],
            url=f"https://reddit.com{meme_data['permalink']}",
            color=discord.Color.orange()
        )
        embed.set_image(url=meme_data["url"])
        embed.set_footer(text=f"👍 {meme_data['ups']} | r/{meme_data['subreddit']} | {sort_type.title()} | by u/{meme_data['author']}")

        await ctx.send(embed=embed)

    @app_commands.command(name="meme", description="Get a random meme from r/memes with sorting options")
    @app_commands.describe(
        sort_type="How to sort the memes",
        time_filter="Time period for top/controversial sorts"
    )
    async def meme_slash(
        self, 
        interaction: discord.Interaction,
        sort_type: Literal["best", "new", "top", "rising", "controversial"] = "hot",
        time_filter: Literal["hour", "day", "week", "month", "year", "all"] = "day"
    ):
        """Fetch a random meme from r/memes with sorting options"""
        await interaction.response.defer()
        meme_data = await self.fetch_reddit_meme(sort_type, time_filter)
        
        if not meme_data:
            return await interaction.followup.send("Could not fetch a meme right now. Try again later!")

        embed = discord.Embed(
            title=meme_data["title"],
            url=f"https://reddit.com{meme_data['permalink']}",
            color=discord.Color.orange()
        )
        embed.set_image(url=meme_data["url"])
        embed.set_footer(text=f"👍 {meme_data['ups']} | r/{meme_data['subreddit']} | {sort_type.title()} | by u/{meme_data['author']}")

        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
