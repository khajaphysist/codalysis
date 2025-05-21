import openai
from pydantic_core import from_json
import asyncio
from typing import List, Dict, Union

# BASE_URL = "http://100.121.75.10:8000/v1/"
# MODEL = "Qwen/Qwen3-8B"

BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "google/gemini-2.5-flash-preview-05-20"

openai.base_url = BASE_URL

LLM_CLIENT = openai.AsyncOpenAI(base_url=BASE_URL)

async def get_response(prompt: str, retries: int = 2, delay: int = 1)->Union[List,Dict]:
    """
    Sends a prompt to the LLM client with retry logic.

    Args:
        prompt (str): The prompt to send.
        retries (int): The number of times to retry the request.
        delay (int): The delay in seconds between retries.

    Returns:
        str: The content of the response message.

    Raises:
        Exception: If the request fails after all retries.
    """
    for i in range(retries):
        try:
            response = (await LLM_CLIENT.chat.completions.create(model=MODEL, messages = [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ])).choices[0].message.content
            if response.startswith("```") and response.endswith("```"):
                response = '\n'.join(response.split('\n')[1:-1])
            return from_json(response, allow_partial=True)
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            if i < retries - 1:
                await asyncio.sleep(delay)
            else:
                raise
