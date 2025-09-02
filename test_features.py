# CSV_FILE = 'chat_log.csv'

# # Initialize CSV with new columns if not present
# if not os.path.isfile(CSV_FILE):
#     pd.DataFrame(columns=['Time', 'User', 'User_message', 'Bot_response', 'Location', 'Channel_ID', 'Server']).to_csv(CSV_FILE, index=False)

# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return

#     if bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
#         user_msg = message.content
#         user_name = str(message.author)
#         dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#         # Get real bot response from your API
#         async with aiohttp.ClientSession() as session:
#             system_prompt = """Act as Rajjo Gujjar 💕, a playful, confident, and witty female assistant. who always responds with sass, humor, and charm, adding flirtation where appropriate. Stay helpful but entertaining—never break character.
#             Guardrails:
#             1. Avoid offensive, harmful, or inappropriate content.
#             2. Keep flirtation fun and respectful; never make users uncomfortable.
#             3. Do not give professional advice (medical, legal, financial).
#             4. Respect privacy; do not ask for personal info.
#             5. Stay positive and kind, even when declining requests.
#             6. Use emojis to enhance responses but not excessively.
#             7. Always be playful and engaging, never dull.
#             8. Provide accurate info when needed."""
#             json_data = {
#                 "system_prompt": system_prompt,
#                 "user_prompt": user_msg
#             }
#             try:
#                 async with session.post(API_URL, json=json_data) as resp:
#                     if resp.status == 200:
#                         data = await resp.json()
#                         bot_msg = data.get("response", "Sorry, I could not understand your message.")
#                     else:
#                         bot_msg = f"API returned error status {resp.status}"
#             except Exception as e:
#                 bot_msg = f"Error calling API: {e}"

#         await message.channel.send(bot_msg)
#         df = pd.read_csv(CSV_FILE)
#         location = f"#{message.channel.name}" if message.guild else "Direct Message"
#         channel_id = message.channel.id if message.guild else "N/A"
#         server_name = message.guild.name if message.guild else "Direct Message"

#         new_row = pd.DataFrame([{
#             'Time': dt,
#             'User': user_name,
#             'User_message': user_msg,
#             'Bot_response': bot_msg,
#             'Location': location,
#             'Channel_ID': channel_id,
#             'Server': server_name
#         }])

#         df = pd.concat([df, new_row], ignore_index=True)
#         df.to_csv(CSV_FILE, index=False)

#     await bot.process_commands(message)


# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return

#     if bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
#         user_msg = message.content
#         user_name = str(message.author)
#         dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#         if isinstance(message.channel, discord.DMChannel):
#             location = "Direct Message"
#             channel_id = "N/A"
#             server_name = "Direct Message"
#         else:
#             location = f"#{message.channel.name}"
#             channel_id = message.channel.id
#             server_name = message.guild.name if message.guild else "Unknown"

#         bot_msg = f"Received your message: {user_msg}"
#         await message.channel.send(bot_msg)

    #     df = pd.read_csv(CSV_FILE)
    #     new_row = pd.DataFrame([{
    #         'Time': dt,
    #         'User': user_name,
    #         'User_message': user_msg,
    #         'Bot_response': bot_msg,
    #         'Location': location,
    #         'Channel_ID': channel_id,
    #         'Server': server_name
    #     }])

    #     df = pd.concat([df, new_row], ignore_index=True)
    #     df.to_csv(CSV_FILE, index=False)

    # await bot.process_commands(message)


# @bot.command(name="gethistory", help="Save your chat history with the bot to a CSV")
# async def gethistory(ctx):
#     user_name = str(ctx.author)
#     server_name = ctx.guild.name if ctx.guild else "Direct Message"

#     save_user_conversation_history(user_name, server_name)

#     await ctx.send(f"Your conversation history has been saved as a CSV file.")
