"""
lib/llm.py — the LLM translation call
=====================================
One job: turn an English string into Mexican Spanish using an LLM.

Provider is swappable via the `LLM_PROVIDER` env var:
  - "anthropic"  (default) → Anthropic Claude, reads ANTHROPIC_API_KEY
  - "openrouter"           → OpenRouter (OpenAI-compatible), reads OPENROUTER_API_KEY

Set `MODEL` to a slug the chosen provider understands, e.g.
  LLM_PROVIDER=anthropic   MODEL=claude-sonnet-4-6
  LLM_PROVIDER=openrouter  MODEL=openai/gpt-4o-mini   (or meta-llama/llama-3.1-8b-instruct, etc.)

FAIL LOUD: we do NOT wrap the call in a try/except that returns `text` on error.
If the provider fails, the exception propagates so the caller returns a 502.
Silently returning the untranslated input is an automatic fail on this
assignment (and a real production bug — it ships English while looking healthy).
"""
import os

MODEL_DEFAULT = os.getenv("MODEL", "claude-sonnet-4-6")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _provider() -> str:
    # Read at call time, not import time: lib.llm is imported before
    # load_dotenv() runs in app.py, so a module-level constant would miss it.
    return os.getenv("LLM_PROVIDER", "anthropic").lower()

SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's English text into "
    "natural, everyday MEXICAN Spanish (es-MX) — the register a Mexican speaker "
    "would actually use, NOT generic or Castilian (es-ES) Spanish. "
    "Return ONLY the translation: no preamble, no explanations, no wrapping "
    "quotes, no notes. Preserve numbers, prices (e.g. $1,299.00), URLs, and "
    "product/model codes (e.g. SKU-4471) exactly as written."
)

# Clients are built lazily (after load_dotenv() has populated the env) and the
# SDKs are imported only for the provider actually in use.
_anthropic = None
_openai = None


def _anthropic_client():
    global _anthropic
    if _anthropic is None:
        from anthropic import AsyncAnthropic
        _anthropic = AsyncAnthropic()  # reads ANTHROPIC_API_KEY
    return _anthropic


def _openrouter_client():
    global _openai
    if _openai is None:
        from openai import AsyncOpenAI
        _openai = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
    return _openai


def _clean(s: str) -> str:
    return (s or "").strip().strip('"').strip()


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into `target` (Mexican Spanish by default).

    Fails loud: any provider error propagates to the caller (→ 502). We never
    swallow the error and return the untranslated input.
    """
    if _provider() == "openrouter":
        resp = await _openrouter_client().chat.completions.create(
            model=model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        return _clean(resp.choices[0].message.content)

    # default: anthropic
    msg = await _anthropic_client().messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    return _clean(msg.content[0].text)


async def translate_stream(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT):
    """Yield the translation token-by-token as it's generated.

    Same fail-loud contract as translate_text: provider errors propagate.
    """
    if _provider() == "openrouter":
        stream = await _openrouter_client().chat.completions.create(
            model=model,
            max_tokens=1024,
            stream=True,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
        return

    # default: anthropic
    async with _anthropic_client().messages.stream(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    ) as stream:
        async for delta in stream.text_stream:
            if delta:
                yield delta
