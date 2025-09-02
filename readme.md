# Rajjo Gujjar 💕 Discord Bot

## Introduction

Rajjo Gujjar 💕 is a playful, witty, and charming Discord bot designed to bring fun, engagement, and helpfulness to your server. She responds with sass, humor, and a touch of flirtation, while maintaining respectful and positive interactions. The bot features chat capabilities powered by LLMs, server utilities, logging, giveaways, and more.

## Features

- **Conversational AI**: Chat with Rajjo Gujjar using LLM-powered responses with context-aware history.
- **Command Logging**: All bot interactions are logged to a CSV file for analytics and history.
- **Server Utilities**: User info, server info, message purge, markdown posting, and more.
- **Moderation Tools**: Message edit/delete logging, configurable log channels.
- **Giveaways**: Interactive giveaways with button-based entry.
- **Conversation History**: Export and retrieve user/server conversation logs.
- **Customizable Presence**: Fun status and welcome messages.

## Technologies Used

- **Python 3.10+**
- **discord.py** (Discord API wrapper)
- **aiohttp** (Async HTTP client)
- **FastAPI** (For LLM API backend)
- **pandas** (CSV logging and data manipulation)
- **dotenv** (Environment variable management)
- **Ollama** (Local LLM inference via subprocess)
- **Logging** (Built-in Python logging)

## Project Structure

```
Discord Bot/
│
├── bot.py                # Main Discord bot logic and commands
├── methods.py            # Utility functions
├── ollama_call.py        # FastAPI backend for LLM inference via Ollama
├── chat_log.csv          # CSV log of all bot conversations
├── .env                  # Environment variables (BOT_TOKEN, API_URL, etc.)
└── README.md             # Project documentation
```

## Setup & Installation

1. **Clone the repository**
    ```
    git clone https://github.com/yourusername/discord-bot.git
    ```

2. **Install dependencies**
    ```
    pip install -r requirements.txt
    ```

3. **Configure environment variables**
    - Create a `.env` file with:
        ```
        BOT_TOKEN=your_discord_bot_token
        API_URL=http://localhost:8000/ollama_query/
        ```

4. **Start the FastAPI backend**
    ```
    uvicorn ollama_call:app --host 0.0.0.0 --port 8000 --reload
    ```

5. **Run the Discord bot**
    ```
    python bot.py
    ```

## Usage

- Use `!helpme` in your Discord server to see all available commands.
- Chat with Rajjo using `!chat <your message>`.
- Export conversation history with custom commands.
- Moderate and manage your server with built-in utilities.

## Example Commands

- `!chat Hello Rajjo!`
- `!userinfo @username`
- `!serverinfo`
- `!purge 10`
- `!giveaway 60 Free Nitro`
- `!setlog general`
- `!unsetlog`
- `!markdown general True **Hello, Markdown!**`

## Contributing

Pull requests and suggestions are welcome! Please open an issue for major changes.

## License

This project is licensed under the MIT License.

---

**Rajjo Gujjar 💕** — Stealing Hearts, One Message at a Time!