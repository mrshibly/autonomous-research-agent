"""
LLM client factory — supports Groq, OpenAI, and Ollama.
Returns a unified interface regardless of provider.
"""

from openai import AsyncOpenAI
from groq import AsyncGroq
from loguru import logger

from app.config import get_settings


def get_llm_client() -> tuple:
    """
    Create and return an LLM client + model name based on settings.

    Returns:
        Tuple of (client, model_name).
        The client follows the OpenAI-compatible API interface.
    """
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "groq":
        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is required when using the Groq provider. "
                "Get a free key at https://console.groq.com"
            )
        client = AsyncGroq(api_key=settings.groq_api_key)
        model = settings.groq_model
        logger.info(f"Using Groq LLM provider with model: {model}")

    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when using the OpenAI provider."
            )
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        model = settings.openai_model
        logger.info(f"Using OpenAI LLM provider with model: {model}")

    elif provider == "ollama":
        client = AsyncOpenAI(
            base_url=f"{settings.ollama_base_url}/v1",
            api_key="ollama",  # Ollama doesn't need a real key
        )
        model = settings.ollama_model
        logger.info(f"Using Ollama LLM provider with model: {model}")

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    return client, model


async def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful research assistant.",
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """
    Make an LLM call with the configured provider.

    Args:
        prompt: The user prompt.
        system_prompt: System-level instruction.
        temperature: Sampling temperature (lower = more focused).
        max_tokens: Maximum response tokens.

    Returns:
        The LLM's text response.
    """
    client, model = get_llm_client()

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:
        logger.error(f"LLM call failed: {exc}")
        raise RuntimeError(f"LLM call failed: {exc}") from exc
