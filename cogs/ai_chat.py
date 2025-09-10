import discord
import aiohttp
import os
from gtts import gTTS
from io import BytesIO
from discord.ext import commands
from methods import get_latest_user_conversation_history, summarize_with_LLM, get_user_conversation_history
from utils import log_command

class AIChat(commands.Cog):
    """AI Chat and TTS commands"""

    def __init__(self, bot):
        self.bot = bot
        self.API_URL = os.getenv("API_URL")

    @commands.command(help="Chat with Rajjo Gujjar 💕")
    @log_command
    async def chat(self, ctx, *, query: str):
        user_name = ctx.author.name

        # Get conversation history for context
        history_for_summarize = await get_user_conversation_history(user_name)
        history_for_summarize_text = history_for_summarize.to_string() if not history_for_summarize.empty else "No previous conversation history found."
        summarized_history = await summarize_with_LLM(
            history_for_summarize_text,
            "Summarize the above conversation in key points and notes",
            self.API_URL
        )

        # Get recent conversation history
        history = await get_latest_user_conversation_history(user_name, limit=5)
        if history.empty:
            history_text = "No previous conversation history found."
        else:
            history_lines = []
            for _, row in history.iterrows():
                time_str = row['Time']
                user_msg = row['User_message']
                bot_resp = row['Bot_response']
                history_lines.append(f"[{time_str}] User: {user_msg} | Bot: {bot_resp}")
            history_text = "\n".join(history_lines)

        # Build system prompt with conversation context and guardrails
        system_prompt = f"""Act as Rajjo Gujjar 💕, a playful, confident, and witty female assistant who always responds with sass, humor, and charm, adding flirtation where appropriate. Stay helpful but entertaining—never break character.

*Use the following conversation history for context dont add this to the response ,this is purely for keeping track of conversation*:

**Summarized Past Conversation :\n{summarized_history}\n**

**Recent Conversation :\n{history_text}\n**

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
                async with session.post(self.API_URL, json=json_data) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("response", "No response field in API reply.")
                    else:
                        response_text = f"API returned error status {resp.status}"
            except Exception as e:
                response_text = f"Error calling API: {e}"

        await ctx.send(response_text)

    @commands.command(help="Make the bot speak using TTS in a voice channel")
    @log_command
    async def speak(self, ctx, *, text=None):
        if ctx.author.voice:
            channel = ctx.author.voice.channel

            if not ctx.voice_client or ctx.voice_client.channel != channel:
                await channel.connect()
                await ctx.send(f"Joined voice channel: {channel.name}")
        else:
            await ctx.send("You are not in a voice channel.")
            return

        if not ctx.voice_client:
            await ctx.send("Bot is not in a voice channel.")
            return

        user_name = ctx.author.name

        history = await get_latest_user_conversation_history(user_name, limit=5)
        if history.empty:
            history_text = "No previous conversation history found."
        else:
            history_lines = []
            for _, row in history.iterrows():
                time_str = row['Time']
                user_msg = row['User_message']
                bot_resp = row['Bot_response']
                history_lines.append(f"[{time_str}] User: {user_msg} | Bot: {bot_resp}")
            history_text = "\n".join(history_lines)

        system_prompt = f"""Act as Rajjo Gujjar, a playful, confident, and witty female assistant who always responds with sass, humor, and charm, adding flirtation where appropriate. Stay helpful but entertaining—never break character.

*Use the following conversation history for context dont add this to the response ,this is purely for keeping track of conversation*:

**Recent Conversation :\n{history_text}\n**

Guardrails:
1. Avoid offensive, harmful, or inappropriate content.
2. Keep flirtation fun and respectful; never make users uncomfortable.
3. Do not give professional advice (medical, legal, financial).
4. Respect privacy; do not ask for personal info.
5. Stay positive and kind, even when declining requests.
6. Use emojis to enhance responses but not excessively.
7. Always be playful and engaging, never dull.
8. Provide accurate info when needed.
9. If you don't know something, admit it rather than making it up.
10. Keep responses concise and to the point.
11. Use proper grammar and never use emojis."""

        json_data = {
            "system_prompt": system_prompt,
            "user_prompt": text or ""
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.API_URL, json=json_data) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("response", "No response field in API reply.")
                    else:
                        response_text = f"API returned error status {resp.status}"
            except Exception as e:
                response_text = f"Error calling API: {e}"

        try:
            buf = BytesIO()
            tts = gTTS(text=response_text, lang="en")
            tts.write_to_fp(buf)
            buf.seek(0)

            ctx.voice_client.play(discord.FFmpegPCMAudio(buf, pipe=True))

            await ctx.send(f"🔊 Speaking: {response_text}")

        except Exception as e:
            await ctx.send(f"❌ Error generating or playing TTS: {str(e)}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
