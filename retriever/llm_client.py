import os
import logging
from typing import List, Dict, Any, Optional
from retriever.prompt_templates import QA_TEMPLATE, SQL_QA_TEMPLATE, ROLE_SYSTEM
from openai import OpenAI

MODEL_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

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
            {"role": "system", "content": ROLE_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
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
        temperature=temperature,
    )
    return message.content[0].text.strip()

def build_sql_prompt(query, articles, model):
    """
    Articles is a list of dicts, each containing the full metadata and content.
    """
    # For context, join all articles in a readable format
    context = "\n---\n".join(
        f"ID: {a.get('id')}\nTitle: {a.get('title')}\nWebsite: {a.get('website_url')}\nURL: {a.get('news_url')}\nPublished at: {a.get('published_at')}\nMeta: {a.get('meta','')}\nContent: {a.get('content')}" for a in articles
    )
    return SQL_QA_TEMPLATE.format(context=context, query=query)

def generate_sql_answer(
    query: str,
    articles: List[Dict[str, Any]],
    provider: Optional[str] = None
) -> Dict[str, Any]:
    provider = provider or MODEL_PROVIDER
    if provider == "openai":
        model = OPENAI_MODEL
    elif provider == "anthropic":
        model = ANTHROPIC_MODEL
    else:
        raise ValueError("Unsupported LLM provider.")
    prompt = build_sql_prompt(query, articles, model)
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
        "used_articles": articles
    }