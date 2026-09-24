import time
from openai import OpenAI
from config import (
    OPENROUTER_KEY,
    TOKENHARBOR_KEY,
    TOKENHARBOR_BASE,
    BYNARA_KEY,
    BYNARA_BASE,
    EXTRA_HEADERS,
    SCAN_MODEL,
)


def get_openrouter_client() -> OpenAI:
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_API_KEY topilmadi. .env faylini tekshiring.")
    return OpenAI(
        api_key=OPENROUTER_KEY,
        base_url="https://openrouter.ai/api/v1",
    )


def get_tokenharbor_client() -> OpenAI:
    if not TOKENHARBOR_KEY:
        raise ValueError("TOKENHARBOR_API_KEY topilmadi.")
    return OpenAI(
        api_key=TOKENHARBOR_KEY,
        base_url=TOKENHARBOR_BASE,
    )


def get_bynara_client():
    if not BYNARA_KEY:
        return None
    return OpenAI(
        api_key=BYNARA_KEY,
        base_url=BYNARA_BASE,
    )


def safe_api_call(
    client,
    prompt: str,
    model: str = SCAN_MODEL,
    max_retries: int = 5,
    provider_name: str = "",
    temperature: float = 0.0,
    response_format_json: bool = True,
    extra_body: dict | None = None,
    system_prompt: str | None = None,
):
    messages = [{"role": "user", "content": prompt}]
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "extra_headers": EXTRA_HEADERS,
    }
    if response_format_json:
        kwargs["response_format"] = {"type": "json_object"}
    if extra_body:
        kwargs["extra_body"] = extra_body
    else:
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            raw_text = response.choices[0].message.content.strip()
            if "<!DOCTYPE" in raw_text or "403" in raw_text:
                print(f"  ⚠️ [{provider_name}] Cheklov (403), 5s kutish...")
                time.sleep(5)
                continue
            return raw_text
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "rate" in err_str or "too many" in err_str:
                wait = 30
                try:
                    if hasattr(e, "response") and e.response is not None:
                        retry_after = e.response.headers.get("retry-after")
                        if retry_after:
                            wait = int(retry_after) + 2
                except Exception:
                    pass
                print(f"  ⏳ [{provider_name}] Rate limit! {wait}s kutish ({attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue
            print(f"  ❌ [{provider_name}] Xato: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return None
    print(f"  ❌ [{provider_name}] {max_retries} ta urinishdan keyin xato")
    return None
