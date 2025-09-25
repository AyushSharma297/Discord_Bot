import discord
import aiohttp
import os
import base64
import yaml
from gtts import gTTS
from io import BytesIO
from discord.ext import commands
from discord import app_commands
from methods import get_latest_user_conversation_history, get_and_summarize_conversation
from utils.utility import log_command, log_chat_to_db
import logging
import time
from datetime import datetime

# Construct path to the YAML file
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # goes up one level from 'cogs'
sys_prompts_path = os.path.join(base_dir, 'utils', 'sys_prompts.yaml')

class AIChat(commands.Cog):
    """AI Chat and TTS commands"""

    def __init__(self, bot):
        self.bot = bot
        self.API_URL = os.getenv("API_URL")
        self.IMG_API_URL = os.getenv("IMG_API_URL")
        

        with open(sys_prompts_path, "r", encoding="utf-8") as f:
            self.prompts_data = yaml.safe_load(f)

    def get_prompt_by_id(self, prompt_id):
        for prompt in self.prompts_data.get("system_prompts", []):
            if prompt.get("id") == prompt_id:
                return prompt.get("content")
        return None

    @commands.hybrid_command(
        name="chat", 
        description="Chat with Rajjo Gujjar 💕"
    )
    # 3. (Optional but recommended) Add a description for the argument
    @app_commands.describe(
        query="The message you want to send to Rajjo."
    )
    async def chat(self, ctx, *, query: str):
        user_name = ctx.author.name

        processing_embed = discord.Embed(
            title="Rajjo is thinking... 💭",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )
        processing_embed.add_field(name="Your Query", value=f"`{query}`", inline=False)
        processing_embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )
        response_message = await ctx.send(embed=processing_embed)

        start_time = time.time()
        history = await get_latest_user_conversation_history(user_name, limit=8)
        if history.empty:
            history_text = "No previous conversation history found."
        else:
            history_lines = []
            for _, row in history.iterrows():
                time_str = row["Time"]
                user_msg = row["User_message"]
                bot_resp = row["Bot_response"]
                history_lines.append(f"[{time_str}] User: {user_msg} | Bot: {bot_resp}")
            history_text = "\n".join(history_lines)

        base_system_prompt = self.get_prompt_by_id("rp_v1")
        if not base_system_prompt:
            base_system_prompt = "You are Rajjo Gujjar, a helpful assistant."

        # Format the prompt with conversation context
        system_prompt = base_system_prompt.format(
            history_text=history_text
        )

        json_data = {"system_prompt": system_prompt, "user_prompt": query, "use_groq": True}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.API_URL, json=json_data) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    response_text = data.get("response", "No response field in API reply.")
                    model_name = data.get("model_used")
        except aiohttp.ClientResponseError as e:
            response_text = f"API returned error status {e.status}"
        except Exception as e:
            logging.error(f"Error calling API: {e}")
            response_text = f"Error calling API: {e}"

        processing_time = round(time.time() - start_time, 2)

        success_embed = discord.Embed(
            title=" ",
            description=response_text,
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        
        success_embed.add_field(name="\u200b", value=" ", inline=False)
        success_embed.add_field(
            name="📝 Your Query",
            value=f"`{query}`",
            inline=False,
        )
        success_embed.add_field(
            name="⏱️ Processing Time",
            value=f"`{processing_time}s`",
            inline=True,
        )
        success_embed.add_field(
            name="🔗 Model",
            value=f"`{model_name}`",
            inline=True,
        )
        success_embed.set_footer(
            text=f"Requested by {ctx.author.display_name} • ID: {ctx.author.id}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )
        success_embed.timestamp = discord.utils.utcnow()
        await response_message.edit(embed=success_embed)
        await log_chat_to_db(ctx, user_message=query, bot_response=response_text)

    @commands.hybrid_command(
        name="speak", 
        description="Wana hear Rajjo Gujjar 💕"
    )

    @app_commands.describe(
        text="The message you want to send to Rajjo."
    )
    @log_command
    async def speak(self, ctx, *, text=None):
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel.")
            return
        channel = ctx.author.voice.channel

        if not ctx.voice_client or ctx.voice_client.channel != channel:
            await channel.connect()
            await ctx.send(f"Joined voice channel: {channel.name}")

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
                time_str = row["Time"]
                user_msg = row["User_message"]
                bot_resp = row["Bot_response"]
                history_lines.append(f"[{time_str}] User: {user_msg} | Bot: {bot_resp}")
            history_text = "\n".join(history_lines)

        base_system_prompt = self.get_prompt_by_id("rp_v1")
        if not base_system_prompt:
            base_system_prompt = "You are Rajjo Gujjar, a helpful assistant."

        system_prompt = base_system_prompt.format(history_text=history_text, summarized_history="")

        json_data = {"system_prompt": system_prompt, "user_prompt": text or ""}

        try:
            async with aiohttp.ClientSession() as session:
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
            await log_chat_to_db(ctx, user_message=text, bot_response=response_text)
        except Exception as e:
            await ctx.send(f"❌ Error generating or playing TTS: {str(e)}")

    @commands.hybrid_command(
        name="chat_img", 
        description="Chat with Rajjo Gujjar 💕 with attached image."
    )
    # 3. (Optional but recommended) Add a description for the argument
    @app_commands.describe(
        prompt="The message you want to send to Rajjo."
    )
    async def ollama_img_command(self, ctx, *, prompt: str):
        if not ctx.message.attachments:
            error_embed = discord.Embed(
                title="❌ No Image Attached",
                description="Please attach an image to your message.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            )
            error_embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )
            await ctx.send(embed=error_embed)
            return

        attachment = ctx.message.attachments[0]
        if not attachment.content_type.startswith("image/"):
            error_embed = discord.Embed(
                title="❌ Invalid File Type",
                description="The attached file is not an image.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            )
            error_embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )
            await ctx.send(embed=error_embed)
            return

        processing_embed = discord.Embed(
            title="🔄 Processing Image...",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )
        processing_embed.add_field(name="Prompt", value=f"`{prompt}`", inline=False)
        processing_embed.add_field(name="Image", value=f"`📎 {attachment.filename}`", inline=True)
        processing_embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )

        response_message = await ctx.send(embed=processing_embed)
        start_time = time.time()

        async with ctx.typing():
            try:
                image_data = await attachment.read()
                base64_image = base64.b64encode(image_data).decode("utf-8")

                base_system_prompt = self.get_prompt_by_id("img_analysis_v1")
                if not base_system_prompt:
                    base_system_prompt = "You are a helpful assistant that analyzes images thoroughly and provides detailed descriptions."

                payload = {
                    "user_prompt": prompt,
                    "image_base64": base64_image,
                    "system_prompt": base_system_prompt,
                }

                api_url = self.IMG_API_URL

                async with aiohttp.ClientSession() as session:
                    async with session.post(api_url, json=payload, timeout=300) as resp:
                        resp.raise_for_status()
                        json_response = await resp.json()

                end_time = time.time()
                local_processing_time = round(end_time - start_time, 2)

                ollama_response = json_response.get("response", "No response received")
                ollama_elapsed_time = json_response.get("elapsed_time_seconds", 0)
                ollama_elapsed_time_formatted = round(ollama_elapsed_time, 2)
                model_name = json_response["full_response_object"]["model"]

                success_embed = discord.Embed(
                    title="✅ Image Processed Successfully",
                    description=ollama_response,
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow(),
                )
                success_embed.add_field(name="\u200b", value="\u200b", inline=False)
                success_embed.add_field(name="📝 User Asked", value=f"`{prompt}`", inline=False)
                success_embed.add_field(name="📎 Image", value=f"`{attachment.filename}`", inline=True)
                success_embed.add_field(
                    name="⏱️ Server Processing Time",
                    value=f"`{ollama_elapsed_time_formatted}s`",
                    inline=True,
                )
                success_embed.add_field(
                    name="🌐 Total Request Time", value=f"`{local_processing_time}s`", inline=True
                )
                success_embed.add_field(name="🔗 Model", value=f"`{model_name}`", inline=True)
                success_embed.set_footer(
                    text=f"Requested by {ctx.author.display_name} • ID: {ctx.author.id}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
                )
                success_embed.timestamp = discord.utils.utcnow()
                success_embed.set_thumbnail(url=attachment.url)

                await response_message.edit(embed=success_embed)
                await log_chat_to_db(ctx, user_message=prompt, bot_response=ollama_response)

            except aiohttp.ClientResponseError as e:
                end_time = time.time()
                local_processing_time = round(end_time - start_time, 2)

                error_embed = discord.Embed(
                    title="❌ Server Error",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow(),
                )
                if e.status == 500:
                    error_embed.description = (
                        "The Ollama model is not available or encountered an error on the server. Please check the server logs."
                    )
                else:
                    error_embed.description = f"Backend server error: {e.status} - {e.message}"
                error_embed.add_field(name="⏱️ Failed After", value=f"{local_processing_time}s", inline=True)
                error_embed.add_field(name="📝 User Asked", value=prompt, inline=False)
                error_embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
                )
                
                await response_message.edit(embed=error_embed)

            except json.JSONDecodeError as e:
                end_time = time.time()
                local_processing_time = round(end_time - start_time, 2)

                logging.error(f"Error parsing JSON response: {e}")

                error_embed = discord.Embed(
                    title="❌ Response Parsing Error",
                    description="Failed to parse the server response. The response may be malformed.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow(),
                )
                error_embed.add_field(name="⏱️ Failed After", value=f"{local_processing_time}s", inline=True)
                error_embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
                )

                await response_message.edit(embed=error_embed)

            except aiohttp.ClientError as e:
                end_time = time.time()
                local_processing_time = round(end_time - start_time, 2)

                logging.error(f"Error connecting to FastAPI server: {e}")

                error_embed = discord.Embed(
                    title="❌ Connection Error",
                    description=f"Failed to connect to the backend server: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow(),
                )
                error_embed.add_field(name="⏱️ Failed After", value=f"{local_processing_time}s", inline=True)
                error_embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
                )

                await response_message.edit(embed=error_embed)

            except Exception as e:
                end_time = time.time()
                local_processing_time = round(end_time - start_time, 2)

                logging.error(f"An unexpected error occurred: {e}")

                error_embed = discord.Embed(
                    title="❌ Unexpected Error",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow(),
                )
                error_embed.add_field(name="⏱️ Failed After", value=f"{local_processing_time}s", inline=True)
                error_embed.set_footer(
                    text=f"Requested by {ctx.author.display_name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
                )

                await response_message.edit(embed=error_embed)


async def setup(bot):
    await bot.add_cog(AIChat(bot))
