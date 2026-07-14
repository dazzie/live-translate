"""
lib/llm.py — the LLM translation call  (TODO: you implement)
============================================================
One job: turn an English string into Mexican Spanish using an LLM.

Provider is your choice. The default example below is Anthropic Claude
(`pip install anthropic`, set ANTHROPIC_API_KEY). Hamza's launched version
used Google Gemini — either is fine. Whatever you pick:

  - Write a PROMPT that pins the register to Mexican Spanish (es-MX), not
    generic/Castilian Spanish. Ask for ONLY the translation, no preamble.
  - Keep numbers, prices ($), and product/model codes unchanged.
  - Return a clean string (strip quotes/whitespace the model may add).

FAIL LOUD: do NOT wrap the call in a try/except that returns `text` on error.
If the provider fails, let the exception propagate so the caller returns a 502.
Silently returning the untranslated input is an automatic fail on this
assignment (and a real production bug — it ships English while looking healthy).
"""
import os

from anthropic import AsyncAnthropic

MODEL_DEFAULT = os.getenv("MODEL", "claude-sonnet-4-6")

SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's English text into "
    "natural, everyday MEXICAN Spanish (es-MX) — the register a Mexican speaker "
    "would actually use, NOT generic or Castilian (es-ES) Spanish. "
    "Return ONLY the translation: no preamble, no explanations, no wrapping "
    "quotes, no notes. Preserve numbers, prices (e.g. $1,299.00), URLs, and "
    "product/model codes (e.g. SKU-4471) exactly as written."
)

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    # Lazily construct the client so it's built AFTER load_dotenv() has run
    # (module-level construction would miss ANTHROPIC_API_KEY from .env).
    global _client
    if _client is None:
        _client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from the environment
    return _client


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into `target` (Mexican Spanish by default).

    Fails loud: any provider error propagates to the caller (→ 502). We never
    swallow the error and return the untranslated input.
    """
    msg = await _get_client().messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    return msg.content[0].text.strip().strip('"').strip()
