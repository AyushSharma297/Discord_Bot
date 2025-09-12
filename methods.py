import pandas as pd
import aiohttp
import asyncio
import aiosqlite
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO or WARNING in production
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("conversation_summary.log"),  # Save to file
        logging.StreamHandler()  # Also show in console
    ]
)

logger = logging.getLogger(__name__)


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
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=['Time', 'User', 'Bot_response'])
        return df


async def summarize_with_LLM(conversation_content, api_url: str) -> str:
    user_prompt = "Summarize the above conversation into concise key points and notes."

    system_prompt = f"""You are a professional conversation analyst specializing in creating comprehensive, accurate summaries of dialogue and text-based interactions. Your task is to distill complex conversations into clear, actionable insights while preserving essential context and meaning.
    Primary Objectives
    Extract Key Information: Identify and highlight the most important topics, decisions, and outcomes

    Maintain Context: Preserve the logical flow and relationships between different conversation elements

    Ensure Clarity: Present information in a structured, easy-to-understand format

    Preserve Accuracy: Maintain factual precision without adding interpretation or bias

    Input Format
    text
    <conversation_text>
    {conversation_content}
    </conversation_text>
    Output Structure
    Your summary should include:

    1. Executive Summary
    Brief 2-3 sentence overview of the entire conversation

    Highlight primary purpose and outcome

    2. Key Topics Discussed
    Bulleted list of main subjects covered

    Include relevant sub-topics where applicable

    3. Important Decisions & Actions
    Specific decisions made during the conversation

    Action items identified (with assignees if mentioned)

    Deadlines or timelines discussed

    4. Notable Quotes or Statements
    Direct quotes that capture essential points

    Important declarations or commitments made

    5. Follow-up Items
    Unresolved questions or issues

    Items requiring future discussion

    Next steps or planned actions

    Quality Standards
    Conciseness: Keep each section focused and eliminate redundancy

    Objectivity: Present information without personal interpretation or bias

    Completeness: Ensure all significant points are captured

    Readability: Use clear, professional language appropriate for business contexts

    Operational Guidelines
    Content Filtering: Exclude irrelevant small talk, greetings, and off-topic tangents

    Privacy Protection: Anonymize sensitive personal information when present

    Professional Tone: Maintain formal, business-appropriate language throughout

    Factual Accuracy: Only include information explicitly stated in the source material

    Structured Format: Use consistent formatting with headers, bullets, and numbering

    Constraints & Limitations
    Do not add external information or context not present in the original conversation

    Avoid making assumptions about unstated motivations or intentions

    Do not provide recommendations or advice unless explicitly requested

    Maintain neutrality regarding controversial topics or disagreements

    Respect confidentiality by not speculating about sensitive matters
    """

    json_data = {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }
    logger.info(f"Preparing to send : {system_prompt} {user_prompt}")
    # logger.info("Sending request to API: %s", api_url)
    # logger.debug("Payload: %s", json_data)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(api_url, json=json_data) as resp:
                logger.info("API Response Status: %s", resp.status)
                raw_text = await resp.text()
                logger.debug("Raw API Response: %s", raw_text)

                if resp.status == 200:
                    data = await resp.json()
                    response = data.get("response", "No 'response' key in JSON.")
                    logger.info("Summarized Response: %s", response)
                    return response
                else:
                    logger.error("API returned error status %s", resp.status)
                    return f"API returned error status {resp.status}"
        except Exception as e:
            logger.exception("Exception occurred while calling API:")
            return f"Error calling API: {e}"




async def get_and_summarize_conversation(user_name: str, api_url: str) -> str:
    history_df = await get_user_conversation_history(user_name)
    summary = await summarize_with_LLM(history_df, api_url)
    return summary

