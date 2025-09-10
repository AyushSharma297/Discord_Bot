# Discord Bot - Cog Organization Guide

This guide shows how to organize your Discord bot code into cogs for better structure and maintainability.

## Directory Structure

Your project should be organized like this:

```
your-bot-project/
├── main.py                 # Main bot file
├── methods.py              # Utility functions
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (DON'T commit this)
├── data/                  # Database and data files
│   └── chat_log.db        # SQLite database (auto-created)
└── cogs/                  # Cog modules directory
    ├── __init__.py        # Empty file to make it a Python package
    ├── music.py           # Music commands
    ├── moderation.py      # Moderation commands
    ├── utility.py         # Utility commands
    ├── ai_chat.py         # AI chat and TTS commands
    ├── fun.py             # Fun commands and games
    └── events.py          # Event handlers
```

## Setup Instructions

### 1. Create the directory structure
```bash
mkdir your-bot-project
cd your-bot-project
mkdir cogs data
touch cogs/__init__.py
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup environment variables
Create a `.env` file in your project root:
```env
BOT_TOKEN=your_discord_bot_token_here
API_URL=your_api_endpoint_here
```

### 4. File Organization

#### Main Files:
- **main.py**: Contains bot initialization, Lavalink setup, database init, and cog loading
- **methods.py**: Keep your existing utility functions (conversation history, LLM calls)
- **requirements.txt**: All Python dependencies

#### Cog Files:
- **cogs/music.py**: All music-related commands (play, pause, skip, queue, etc.)
- **cogs/moderation.py**: Moderation commands (purge, setlog, giveaway)
- **cogs/utility.py**: General utility commands (ping, userinfo, serverinfo, helpme)
- **cogs/ai_chat.py**: AI chat functionality and TTS commands
- **cogs/fun.py**: Fun commands and interactive features
- **cogs/events.py**: Event listeners (on_member_join, voice updates)

## Key Changes from Original Code

### 1. Decorator Import
The cogs need to import the logging decorator. Add this line to cogs that need it:
```python
from main import log_command
```

### 2. Voice Client Access
Music cog accesses the voice client through:
```python
await voice_channel.connect(cls=self.bot.lavalink_voice_client, self_deaf=True)
```

### 3. Cog Setup Function
Each cog file must end with:
```python
async def setup(bot):
    await bot.add_cog(YourCogClass(bot))
```

### 4. Bot Attribute Access
Access bot attributes in cogs using:
```python
self.bot.lavalink  # Instead of bot.lavalink
```

## Benefits of Cog Organization

### ✅ **Better Organization**
- Commands are logically grouped
- Easier to find and modify specific functionality
- Cleaner code structure

### ✅ **Hot Reloading**
- Reload individual cogs without restarting the bot
- Use `!reload music` to reload just the music cog
- Great for development and debugging

### ✅ **Easier Maintenance**
- Multiple developers can work on different cogs
- Bugs are isolated to specific modules
- Easier to add new features

### ✅ **Better Error Handling**
- Errors in one cog don't crash the entire bot
- Individual cog loading status is visible

## Cog Management Commands

The bot includes owner-only commands for managing cogs:

- `!load music` - Load the music cog
- `!unload music` - Unload the music cog  
- `!reload music` - Reload the music cog

## Migration Steps

1. **Create the directory structure** as shown above
2. **Copy your methods.py** file to the new structure
3. **Replace your bot.py** with the new main.py
4. **Create each cog file** by copying the relevant commands from your original bot.py
5. **Add the log_command import** to cogs that need command logging
6. **Test each cog** individually to make sure everything works

## Important Notes

### 🔴 **Common Issues to Watch For:**

1. **Import Paths**: Make sure all imports work from the cog files
2. **Bot Reference**: Use `self.bot` instead of `bot` in cog methods
3. **Setup Function**: Each cog MUST have an `async def setup(bot):` function
4. **Voice Client**: Music cog needs to access `bot.lavalink_voice_client`

### 🟡 **Database Access:**
The database file path is defined in main.py. If cogs need direct database access, import the DB_FILE path:
```python
from main import DB_FILE
```

### 🟢 **Adding New Cogs:**
1. Create new .py file in cogs/ directory
2. Add cog name to the `cogs` list in main.py `load_cogs()` function
3. Include the `async def setup(bot):` function

## Testing

After migration, test each command group:
- Music commands: `!play`, `!pause`, `!skip`
- Moderation: `!purge`, `!setlog` 
- Utility: `!ping`, `!userinfo`
- AI Chat: `!chat`, `!speak`
- Events: Join a voice channel, add/remove members

Your bot should now be much more organized and easier to maintain! 🎉