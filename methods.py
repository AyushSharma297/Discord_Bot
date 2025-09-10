import pandas as pd
import aiohttp
import asyncio
import aiosqlite

DB_FILE = 'data/chat_log.db'



async def get_latest_user_conversation_history(user_name: str, limit=5) -> pd.DataFrame:
    """
    Retrieve the latest conversation history (up to limit) for a user from the SQLite log.

    :param user_name: Discord username#discriminator, e.g. 'regil297#1234'
    :param limit: Number of latest conversation entries to retrieve
    :return: pandas DataFrame containing latest conversation rows for the user
    """
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT time, user, user_message, bot_response FROM chat_log WHERE user = ? ORDER BY time DESC LIMIT ?",
            (user_name, limit)
        )
        rows = await cursor.fetchall()
        if not rows:
            print(f"No conversation history found for user '{user_name}'.")
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=['Time', 'User', 'User_message', 'Bot_response'])
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
        df = df.sort_values(by='Time').reset_index(drop=True)
        return df



async def get_user_conversation_history(user_name: str) -> pd.DataFrame:
    """
    Retrieve full conversation history for a user from the SQLite log.

    :param user_name: Discord username#discriminator, e.g. 'regil297#1234'
    :return: pandas DataFrame containing conversation rows for the user
    """
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT time, user, bot_response FROM chat_log WHERE user = ? ORDER BY time ASC",
            (user_name,)
        )
        rows = await cursor.fetchall()
        if not rows:
            print(f"No conversation history found for user '{user_name}'.")
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=['Time', 'User', 'Bot_response'])
        return df


async def summarize_with_LLM(history_text: str, user_prompt: str, api_url: str):
    """
    Sends conversation history with a detailed system prompt to the API, returns bot's response.

    Args:
        history_text (str): Conversation history text used for context (not shown in response).
        user_prompt (str): User's current query or message.
        api_url (str): API endpoint URL.

    Returns:
        str: API response text or error.
    """
    system_prompt = f""""You are a helpful assistant who summarizes conversation histories.
            Summarize the following conversation into concise key points and notes,
            preserving the context and meaning. Highlight important aspects clearly and succinctly
            *Use the following conversation history for context dont add this to the response ,this is purely for keeping track of conversation*:
            <conversation_history>
                {history_text}
            </conversation_history>

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
        "user_prompt": user_prompt
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(api_url, json=json_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    responce = data.get("response", "No response field in API reply.")
                    print("API Response:", responce)
                    return responce
                else:
                    return f"API returned error status {resp.status}"
        except Exception as e:
            return f"Error calling API: {e}"
