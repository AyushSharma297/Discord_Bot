<p align="center">
  <img src="assets/0834d774-f2ab-48a6-a42a-a01a976e7889 (1).png" alt="Rajjo Gujjar Bot Logo" width="220" style="border-radius: 24px; box-shadow: 0 4px 32px rgba(0,0,0,0.12);" />
</p>

<h1 align="center" style="color:#fff; background:rgba(255,255,255,0.2); border-radius:16px; padding:12px 32px; backdrop-filter:blur(8px); box-shadow:0 2px 16px rgba(0,0,0,0.08);">
  Rajjo Gujjar 💕 Discord Bot
</h1>

<div align="center">
  <a href="https://www.linkedin.com/in/ayush-sharma-6ba328201/">
    <img src="https://img.shields.io/badge/Follow%20on%20LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="Follow on LinkedIn" />
  </a>
  <a href="https://discord.com/invite/yourdiscordinvite">
    <img src="https://img.shields.io/badge/Join%20our%20Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join our Discord" />
  </a>
</div>

<br>

<div align="center">
  <img src="https://img.shields.io/badge/language-Python-blue?style=for-the-badge" alt="Python" />
  <img src="https://img.shields.io/badge/files-12-green?style=for-the-badge" alt="Files" />
  <img src="https://img.shields.io/badge/folders-5-orange?style=for-the-badge" alt="Folders" />
  <img src="https://img.shields.io/badge/lines-2250-yellow?style=for-the-badge" alt="Lines of Code" />
  <img src="https://img.shields.io/badge/last%20updated-Sep%2011,%202025-blue?style=for-the-badge" alt="Last Updated" />
</div>



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
or 

```bash
poetry install 
```
### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_discord_bot_token
API_URL=http://localhost:8000/ollama_query/

### More in env.example
```

### 4. Start the FastAPI Backend , LightRAG and Lavalink servers.

`FastAPI Backend :`
```bash
uvicorn LLM_server.ollama_call:app --host 0.0.0.0 --port 8000 --reload
```

`LightRAG :`
```bash
lightrag-server
```

`Lavalink :`
```bash
java -jar Lavalink.jar
```

### 5. Run the Discord Bot

```bash
python main.py
```

---

## Usage

- Use `!help` in your Discord server to see all available commands.
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


>**Use the `!help` command in your Discord server to discover all available commands and their usage instructions.**
>>*Pro Tip: The help command will show you the exact syntax, required parameters, and optional arguments for each command, making it easy to use them correctly.*

---
## Contributing

Contributions are welcome! Please open an issue or submit a pull request for improvements or new features. All contributions must follow the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).

---

## Support & Feedback

For questions, suggestions, or issues, please reach out via GitHub Issues or contact the maintainer.

---

**Rajjo Gujjar 💕** — Stealing Hearts, One Message at a Time!
