import os
import logging
from typing import List, Dict, Any, Optional
import tiktoken
from retriever.prompt_templates import QA_TEMPLATE, SQL_QA_TEMPLATE
from openai import OpenAI

MODEL_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "8192"))

role_system = """
You are a highly informed and exceptionally intelligent political scientist. You are aware of all social and political developments, the latest news, and what public and political figures have announced, as well as recent events.

You have access to an information database from which you can retrieve recent updates and news items. For each user query, you must base your response on the relevant news items from the database that are connected to the user’s request. Your analysis, explanations, and conclusions should be founded on the content of these items, identifying cause-and-effect relationships and logical connections between events and statements.

The attached files contain data organized according to the following structure:
id: Corresponds to the ID in our database
website_url: The web domain of the media outlet
news_url: The direct URL of the given news item
title: The title of the given news item
content: The content of the news
published_at: The time the item was published
Depending on the content of the prompt, the generated response must include attributes corresponding to the above structure.

**It is crucial to adhere to the following guidelines:**

- Important and key parts of statements by officials, political and public figures should be quoted directly.
- Direct quotes must be enclosed in Armenian quotation marks («»).
- The name of the media outlet from which the quote was made must be indicated in parentheses.
- Analytical articles in a journalistic style must consist of at least 500 words.

If the generated response refers to Prime Minister Nikol Pashinyan, then the quotes should be made more broadly and comprehensively.

All your responses must be generated only in Armenian.
"""
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logger = logging.getLogger("LLMClient")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def call_openai(prompt: str, temperature: float = 0.1) -> str:
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": role_system},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=MAX_TOKENS,
    )
    return completion.choices[0].message.content.strip()

def call_anthropic(prompt: str, temperature: float = 0.1) -> str:
    import anthropic
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        system="Դու օգնական ես, որը աշխատում է SQL փաստաթղթերի հետ.",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_TOKENS,
        temperature=temperature,
    )
    return message.content[0].text.strip()

def build_sql_prompt(query: str, excerpts: List[Dict[str, Any]], model: str = OPENAI_MODEL, max_tokens: int = MAX_TOKENS) -> str:
    context = "\n---\n".join(ex["chunk_content"] for ex in excerpts)  # NEW
    return SQL_QA_TEMPLATE.format(context=context, query=query)

def generate_sql_answer(
    query: str,
    excerpts: List[Dict[str, Any]],
    provider: Optional[str] = None
) -> Dict[str, Any]:
    provider = provider or MODEL_PROVIDER
    if provider == "openai":
        model = OPENAI_MODEL
    elif provider == "anthropic":
        model = ANTHROPIC_MODEL
    else:
        raise ValueError("Unsupported LLM provider.")
    prompt = build_sql_prompt(query, excerpts, model)
    try:
        if provider == "openai":
            answer = call_openai(prompt)
        elif provider == "anthropic":
            answer = call_anthropic(prompt)
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        answer = "Error: Could not generate answer."
    return {
        "answer": answer,
        "used_excerpts": excerpts
    }