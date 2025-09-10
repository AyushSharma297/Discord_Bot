# utils.py - Shared utilities and decorators
import os
import aiosqlite
from datetime import datetime
from functools import wraps

# Database configuration
DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "chat_log.db")

def log_command(func):
    """Decorator to log command usage to database"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Detect if this is a method (Cog) or a function
        if hasattr(args[0], "bot"):  # likely a Cog instance
            ctx = args[1]
            func_args = args[2:]
        else:
            ctx = args[0]
            func_args = args[1:]

        user_msg = ctx.message.content
        user_name = str(ctx.author)
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response_messages = []

        original_send = ctx.send

        async def fake_send(content=None, *, embed=None, **send_kwargs):
            if content:
                response_messages.append(str(content))
            elif embed:
                texts = []
                if embed.title:
                    texts.append(embed.title)
                if embed.description:
                    texts.append(embed.description)
                for field in embed.fields:
                    texts.append(field.name)
                    texts.append(field.value)
                embed_text = "\n".join(texts)
                response_messages.append(embed_text)
            else:
                response_messages.append("Sent an embed or message without text content.")

            return await original_send(content=content, embed=embed, **send_kwargs)

        ctx.send = fake_send
        await func(*args, **kwargs)

        bot_msg = "\n".join(response_messages) if response_messages else "No response captured."
        location = f"#{ctx.channel.name}" if ctx.guild else "Direct Message"
        channel_id = ctx.channel.id
        server_name = ctx.guild.name if ctx.guild else "Direct Message"

        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute(
                "INSERT INTO chat_log (time, user, user_message, bot_response, location, channel_id, server) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (dt, user_name, user_msg, bot_msg, location, channel_id, server_name)
            )
            await db.commit()

    return wrapper