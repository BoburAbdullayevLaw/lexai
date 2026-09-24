from config import IRAC_MODEL
from prompts import build_irac_prompt
from clients import safe_api_call


def _format_jk(items: list) -> str:
    text = ""
    for item in items:
        text += f"""
JK {item.get('modda_raqami')}-modda
Sarlavha: {item.get('modda_sarlavhasi')}
Qism/Band: {item.get('qism_yoki_band')}
Kazusdagi holat: {item.get('kazusdagi_holat')}
Qonuniy asos: {item.get('qonuniy_asos')}
Buzilganmi: {item.get('buzilganmi')}
Havola: {item.get('lex_url')}
"""
    return text


def _format_jpk(items: list) -> str:
    text = ""
    for item in items:
        text += f"""
JPK {item.get('modda_raqami')}-modda
Sarlavha: {item.get('modda_sarlavhasi')}
Qism/Band: {item.get('qism_yoki_band')}
Kazusdagi holat: {item.get('kazusdagi_holat')}
Qonuniy asos: {item.get('qonuniy_asos')}
Havola: {item.get('lex_url')}
"""
    return text


def _format_plenums(items: list) -> str:
    text = ""
    for p in items:
        if not p.get("tegishli_bandlar"):
            continue
        bandlar_str = ", ".join(
            b.get("band_raqami", "?") for b in p.get("tegishli_bandlar", [])
        )
        text += f"""
PLENUM: {p.get('raqami')} — {str(p.get('qaror_nomi', ''))[:80]}
Manba: {p.get('manba')}
Tegishli bandlar: {bandlar_str}
Kazusga aloqadorlik: {p.get('kazusga_aloqadorlik')}
Tahlil: {p.get('tahlil')}
"""
    return text


def generate_irac(kazus: str, collected_jk: list, collected_jpk: list,
                  collected_plenums: list, client) -> str:
    print(f"\n{'=' * 60}")
    print("🧠 YAKUNIY XULOSA — IRAC USULIDA")
    print(f"   Model: {IRAC_MODEL}")
    print(f"{'=' * 60}")
    print("   IRAC javobi yozilmoqda...")

    final_prompt = build_irac_prompt(
        kazus,
        _format_jk(collected_jk),
        _format_jpk(collected_jpk),
        _format_plenums(collected_plenums),
    )

    raw_text = safe_api_call(
        client,
        final_prompt,
        model=IRAC_MODEL,
        max_retries=5,
        provider_name="IRAC",
        temperature=0.7,
        response_format_json=False,
        system_prompt=(
            "Siz professional huquqshunossiz. IRAC usulida, jadvalsiz, "
            "havolalar bilan javob bering."
        ),
    )
    if raw_text is None:
        return "❌ IRAC: 5 ta urinishdan keyin javob olinmadi"
    return raw_text
