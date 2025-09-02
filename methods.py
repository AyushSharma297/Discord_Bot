import pandas as pd
import aiohttp
import asyncio

def get_latest_user_conversation_history(user_name: str, source_csv='chat_log.csv', limit=5) -> pd.DataFrame:
    """
    Retrieve the latest conversation history (up to limit) for a user from the main CSV log.

    :param user_name: Discord username#discriminator, e.g. 'regil297#1234'
    :param source_csv: Path to the main conversation CSV file
    :param limit: Number of latest conversation entries to retrieve
    :return: pandas DataFrame containing latest conversation rows for the user
    """
    df = pd.read_csv(source_csv)

    # Filter rows where 'User' exactly matches user_name
    user_history = df[df['User'] == user_name]

    if user_history.empty:
        print(f"No conversation history found for user '{user_name}'.")
        return user_history

    # Convert 'Time' column to datetime for proper sorting
    user_history['Time'] = pd.to_datetime(user_history['Time'], errors='coerce')

    # Sort by Time descending and get the latest `limit` rows
    latest_history = user_history.sort_values(by='Time', ascending=False).head(limit)

    # Optional: Reset index and sort ascending if needed for readability
    latest_history = latest_history.sort_values(by='Time').reset_index(drop=True)

    return latest_history


def get_user_conversation_history(user_name: str, source_csv='chat_log.csv') -> pd.DataFrame:
    """
    Retrieve full conversation history for a user from the main CSV log.

    :param user_name: Discord username#discriminator, e.g. 'regil297#1234'
    :param source_csv: Path to the main conversation CSV file
    :return: pandas DataFrame containing conversation rows for the user
    """
    df = pd.read_csv(source_csv)

    # # Filter rows where 'User' exactly matches user_name
    # user_history = df[df['User'] == user_name]
    
    user_history = df[df['User'] == user_name][['Time', 'User', 'Bot_response']]

    if user_history.empty:
        print(f"No conversation history found for user '{user_name}'.")
    return user_history

def save_user_conversation_history(user_name: str, server_name: str, source_csv='chat_log.csv', output_csv=None):
    """
    Extracts the conversation history of a specific user in a server from the main CSV log,
    and saves it to a new CSV file.

    :param user_name: Discord username#discriminator, e.g. 'regil297#1234'
    :param server_name: The server (guild) name to filter by
    :param source_csv: Path to the main conversation CSV file
    :param output_csv: Optional output CSV filename; if None, defaults to '{user_name}_history.csv'
    """
    df = pd.read_csv(source_csv)

    # Filter rows belonging to the user in the specified server
    user_history = df[(df['User'] == user_name) & (df['Server'] == server_name)]

    if user_history.empty:
        print(f"No conversation history found for user '{user_name}' in server '{server_name}'.")
        return

    if output_csv is None:
        safe_username = user_name.replace("#", "_")  # sanitize filename
        safe_server = server_name.replace(" ", "_")
        output_csv = f"{safe_username}_{safe_server}_history.csv"

    user_history.to_csv(output_csv, index=False)
    print(f"Saved conversation history to {output_csv}")



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

    # print("Summarize Prompt:", system_prompt)  # Debug print

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
                    print("API Response:", responce)  # Debug print
                    return responce
                
                else:
                    return f"API returned error status {resp.status}"
        except Exception as e:
            return f"Error calling API: {e}"
