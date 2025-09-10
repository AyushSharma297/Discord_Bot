# Rajjo Gujjar 💕 Discord Bot

## Overview

Rajjo Gujjar 💕 is a feature-rich, modular Discord bot designed for fun, engagement, and server management. Built with Python and leveraging LLM-powered conversational AI, it offers playful chat, music playback, moderation, giveaways, logging, and more. The bot is organized using Discord.py cogs for maintainability and scalability.

---

## Features

- **Conversational AI**: Chat with Rajjo Gujjar using context-aware LLM responses.
- **Music Playback**: Play, queue, skip, and manage music with Lavalink integration.
- **Moderation Tools**: Purge messages, log edits/deletes, set/unset log channels, and run giveaways.
- **Fun & Games**: Russian Roulette, memes, and interactive features.
- **Utilities**: User info, server info, markdown posting, latency checks.
- **Logging**: All interactions are logged to a SQLite database for analytics and history.
- **Voice TTS**: Make the bot speak in voice channels using Google TTS.
- **Cog-Based Architecture**: Easy to extend and maintain.

---

## Technologies Used

- **Python 3.10+**
- **discord.py** – Discord API wrapper
- **aiohttp** – Async HTTP client
- **FastAPI** – LLM API backend
- **pandas** – Data manipulation and logging
- **dotenv** – Environment variable management
- **Lavalink** – Music playback
- **Google TTS** – Text-to-speech
- **Logging** – Built-in Python logging

---

## Directory Structure

```
Discord Bot/
│
├── main.py                # Main bot file (startup, cog loading, Lavalink setup)
├── methods.py             # Utility functions (conversation history, LLM calls)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (BOT_TOKEN, API_URL, etc.)
├── data/                  # Database and data files
│   └── chat_log.db        # SQLite database (auto-created)
├── cogs/                  # Cog modules directory
│   ├── __init__.py
│   ├── music.py           # Music commands
│   ├── moderation.py      # Moderation commands
│   ├── utility.py         # Utility commands
│   ├── ai_chat.py         # AI chat and TTS commands
│   ├── fun.py             # Fun commands and games
│   ├── events.py          # Event handlers
│   └── roast.py           # Roasting commands
├── LLM_server/
│   └── ollama_call.py     # FastAPI backend for LLM inference via Ollama
└── README.md              # Project documentation
```

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/discord-bot.git
cd discord-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_discord_bot_token
API_URL=http://localhost:8000/ollama_query/
```

### 4. Start the FastAPI Backend

```bash
uvicorn LLM_server.ollama_call:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run the Discord Bot

```bash
python main.py
```

---

## Usage

- Use `!helpme` in your Discord server to see all available commands.
- Chat with Rajjo using `!chat <your message>`.
- Moderate and manage your server with built-in utilities.
- Play music, run giveaways, and enjoy fun games.

---

## Example Commands

| Command                                 | Description                                                      |
|------------------------------------------|------------------------------------------------------------------|
| `!chat <message>`                        | Chat with Rajjo Gujjar 💕                                         |
| `!play <song>`                           | Play a song or add it to the queue                               |
| `!queue`                                 | Show the current music queue                                     |
| `!skip`                                  | Skip the current track                                           |
| `!purge <count>`                         | Delete a specified number of previous messages                   |
| `!setlog <channel_name>`                 | Set the log channel by name                                      |
| `!unsetlog`                              | Unset the log channel for this server                            |
| `!giveaway <time_in_seconds> <prize>`    | Start a giveaway                                                 |
| `!userinfo [member]`                     | Show information about a user                                    |
| `!serverinfo`                            | Show detailed information about the server                       |
| `!markdown <channel> [embed=True] <text>`| Send a markdown message to a specified channel                   |
| `!roulette [mode] [ante]`                | Play Russian Roulette game                                       |
| `!meme [sort_type] [time_filter]`        | Get a random meme from Reddit                                    |

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for improvements or new features. All contributions must follow the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).

---

## License

This project is licensed under the MIT License.

---

## Support & Feedback

For questions, suggestions, or issues, please reach out via GitHub Issues or contact the maintainer.

---

**Rajjo Gujjar 💕** — Stealing Hearts, One Message at a Time!