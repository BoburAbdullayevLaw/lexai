import os
import json
import glob
import time
from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
# 1. MUHITNI YUKLASH VA KONFIGURATSIYA
# ============================================================
load_dotenv()
API_KEY = os.environ.get('DEEPSEEK_API_KEY')

if not API_KEY:
    raise ValueError("DEEPSEEK_API_KEY topilmadi")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"
)

extra_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ============================================================
# 2. MODELLAR VA SOZLAMALAR
# ============================================================
MODEL_FLASH = "deepseek-v4-flash"
MODEL_PRO = "deepseek-v4-pro"

JPK_DOC_ID = "-111460"
BASE_LEX_URL = f"https://lex.uz/docs/{JPK_DOC_ID}"

PLENUM_BASE_URL = "https://lex.uz/docs/-3895986"  # Dalillar maqbulligi haqidagi Plenum qarori

JPK_DATA_DIR = "data/jpk_boblar"
PLENUM_DATA_DIR = "data/plenum"

COLLECTED_ARTICLES = []  # JPK moddalari
COLLECTED_PLENUM_BANDS = []  # Plenum bandlari

# ============================================================
# 3. KAZUS MATNI
# ============================================================
KAZUS_MATNI = """Voyaga yetmagan shaxslar oʻrtasida kelib chiqqan oʻzaro janjal natijasida 2025-yil 10-yanvar kuni taxminan soat 12:30 larda voyaga yetmagan 16 yoshli Anvar ismli shaxs janjal davomida yonida boʻlgan pichoq bilan Bobur ismli shaxsning chap qorin qismiga bir marotaba urib, tan jarohati yetkazgan.

Voqea joyi koʻzdan kechirilganda voqea joyidan qonga oʻxshash qizgʻish dogʻlari boʻlgan pichoq, oq rangdagi mato parchalari, bir dona charm oyoq kiyim topildi hamda ashyoviy dalil sifatida ish materiallariga qoʻshib qoʻyildi. Ushbu narsalar voqea joyini koʻzdan kechirish bayonnomasiga kiritilmadi.

Sudga oid tibbiy ekspertizaning xulosasiga koʻra Bobur ismli shaxsga ogʻir shikast yetkazilgani aniqlangan. Biroq, tergovchi ekspert xulosasiga qoʻshilmagan.

Dastlabki tergov jarayonida Anvar oʻz aybini toʻliq tan olib, aniq koʻrsatma beradi. Sud muhokamasida Anvar koʻrsatuvlarini oʻzgartirib, aybni tan olmagan va tergovchi ishni tugatishga vaʼda berib, uni majburlaganini bildirgan.

Sud jarayonida jabrlanuvchi guvohlik berishdan bosh tortgan. Ikki nafar guvohlarning koʻrsatuvlari esa qarama-qarshi boʻlgan."""


# ============================================================
# 4. YORDAMCHI FUNKSIYALAR
# ============================================================
def clean_to_json(text_content: str) -> str:
    text_content = text_content.strip()
    if "```json" in text_content:
        text_content = text_content.split("```json")[1].split("```")[0].strip()
    elif "```" in text_content:
        text_content = text_content.split("```")[1].split("```")[0].strip()
    return text_content


def natural_sort_key(path: str):
    import re
    name = os.path.basename(path).replace("-bob.json", "").replace(".json", "")
    parts = re.split(r"[-.]", name)
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            pass
    return nums if nums else [0]


def format_bob_for_prompt(bob_data: dict) -> str:
    lines = []
    bob_nomi = bob_data.get("bob_nomi", "Nomsiz bob")
    lines.append(f"BOB: {bob_nomi}\n{'=' * 60}")

    for modda in bob_data.get("moddalar", []):
        sarlavha = modda.get("sarlavha", f"{modda.get('n')}-modda")
        sarlavha_id = modda.get("sarlavha_id", "")
        id_qismi = f" (ID: {sarlavha_id})" if sarlavha_id else ""
        lines.append(f"\n{sarlavha}{id_qismi}")

        for qism in modda.get("qismlar", []):
            q_id = qism.get("id", "")
            q_text = qism.get("matn", "")
            id_tag = f" [ID:{q_id}]" if q_id else ""
            lines.append(f"  Qism {qism.get('q')}{id_tag}: {q_text}")

            for band in qism.get("bandlar", []):
                b_id = band.get("id", "")
                b_text = band.get("matn", "")
                id_tag = f" [ID:{b_id}]" if b_id else ""
                lines.append(f"    Band {band.get('b')}{id_tag}: {b_text}")

    return "\n".join(lines)


def save_backup_results():
    if COLLECTED_ARTICLES or COLLECTED_PLENUM_BANDS:
        backup = {
            "jpk_moddalar": COLLECTED_ARTICLES,
            "plenum_bandlari": COLLECTED_PLENUM_BANDS
        }
        with open("lexai_v4_backup.json", "w", encoding="utf-8") as f:
            json.dump(backup, f, ensure_ascii=False, indent=2)
        print("📦 Oraliq natijalar 'lexai_v4_backup.json' fayliga saqlandi.")


# ============================================================
# 5. JPK BOBLARINI SKANERLASH
# ============================================================
def scan_jpk_boblar():
    global COLLECTED_ARTICLES

    all_files = glob.glob(os.path.join(JPK_DATA_DIR, "*.json"))
    all_files.sort(key=natural_sort_key)

    print(f"📚 JPK tahlili: {len(all_files)} ta bob skanerlanmoqda...")

    for idx, file_path in enumerate(all_files):
        filename = os.path.basename(file_path)

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                bob_data = json.load(f)
        except Exception as e:
            print(f"  [{idx + 1}/{len(all_files)}] 📁 {filename}: {e}")
            continue

        bob_nomi = bob_data.get("bob_nomi", filename)
        bob_raqami = bob_data.get("bob_raqami", "?")

        if not bob_data.get("moddalar"):
            continue

        formatted_bob = format_bob_for_prompt(bob_data)

        prompt = f"""KAZUS:
{KAZUS_MATNI}

JPK BOB:
{formatted_bob}

Ushbu bobdagi qaysi moddalar kazusga bevosita aloqador?
Faqat JSON formatida javob bering.

{{
  "relevant_moddalar": [
    {{
      "modda_raqami": <int>,
      "modda_sarlavhasi": "<sarlavha>",
      "element_id": "<ID>",
      "kazusdagi_holat": "<1 jumla>",
      "qonuniy_asos": "<1 jumla>"
    }}
  ]
}}"""

        time.sleep(0.15)

        try:
            response = client.chat.completions.create(
                model=MODEL_FLASH,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                extra_headers=extra_headers,
                extra_body={"thinking": {"type": "disabled"}},
                response_format={"type": "json_object"}
            )

            raw_text = response.choices[0].message.content.strip()
            clean_content = clean_to_json(raw_text)
            res_json = json.loads(clean_content)
            relevant_list = res_json.get("relevant_moddalar", [])

            for item in relevant_list:
                element_id = item.get("element_id", "")
                lex_link = f"{BASE_LEX_URL}#{element_id}" if element_id else BASE_LEX_URL

                COLLECTED_ARTICLES.append({
                    "manba": "JPK",
                    "bob_raqami": bob_raqami,
                    "bob_nomi": bob_nomi,
                    "modda_raqami": item.get("modda_raqami"),
                    "modda_sarlavhasi": item.get("modda_sarlavhasi"),
                    "element_id": element_id,
                    "lex_url": lex_link,
                    "kazusdagi_holat": item.get("kazusdagi_holat", ""),
                    "qonuniy_asos": item.get("qonuniy_asos", "")
                })

            if relevant_list:
                moddalar_str = ", ".join(str(m.get("modda_raqami")) for m in relevant_list)
                print(f"  ✅ [{idx + 1}/{len(all_files)}] {bob_nomi[:35]} → JPK {moddalar_str}")

        except Exception as e:
            print(f"  ❌ [{idx + 1}/{len(all_files)}] {filename}: {e}")

        if (idx + 1) % 10 == 0:
            save_backup_results()

    print(f"  📊 JPK dan {len(COLLECTED_ARTICLES)} ta aloqador modda topildi.")


# ============================================================
# 6. PLENUM QARORLARINI SKANERLASH
# ============================================================
def scan_plenum_qarorlari():
    global COLLECTED_PLENUM_BANDS

    all_files = glob.glob(os.path.join(PLENUM_DATA_DIR, "*.json"))

    if not all_files:
        print("⚠️ Plenum qarorlari topilmadi, o'tkazib yuboriladi.")
        return

    print(f"\n📚 Plenum tahlili: {len(all_files)} ta qaror skanerlanmoqda...")

    for idx, file_path in enumerate(all_files):
        filename = os.path.basename(file_path)

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                qaror_data = json.load(f)
        except Exception as e:
            print(f"  [{idx + 1}/{len(all_files)}] 📁 {filename}: {e}")
            continue

        qaror_nomi = qaror_data.get("qaror_nomi", filename)
        bandlar = qaror_data.get("bandlar", [])

        for band in bandlar:
            if not band.get("matn"):
                continue

            band_id = band.get("id", "")
            band_raqami = band.get("band_raqami", "")
            xatboshi = band.get("xatboshi", "")

            prompt = f"""KAZUS:
{KAZUS_MATNI}

PLENUM BANDI:
{band.get('matn', '')}

Bu band kazusga tegishlimi? Faqat "HA" yoki "YO'Q" deb javob bering."""

            time.sleep(0.1)

            try:
                response = client.chat.completions.create(
                    model=MODEL_FLASH,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    extra_headers=extra_headers,
                    extra_body={"thinking": {"type": "disabled"}}
                )

                if "HA" in response.choices[0].message.content.upper():
                    band_url = f"{PLENUM_BASE_URL}#{band_id}" if band_id else PLENUM_BASE_URL

                    COLLECTED_PLENUM_BANDS.append({
                        "manba": "Plenum",
                        "qaror_nomi": qaror_nomi,
                        "band_raqami": band_raqami,
                        "xatboshi": xatboshi,
                        "band_id": band_id,
                        "band_url": band_url,
                        "mazmuni": band.get("mazmuni", ""),
                        "matn": band.get("matn", ""),
                        "bogliq_jpk_moddalari": band.get("bogliq_jpk_moddalari", [])
                    })
                    print(f"  ✅ Plenum: {qaror_nomi[:30]} → band {band_raqami}.{xatboshi}")

            except Exception as e:
                print(f"  ❌ Xato: {e}")

            time.sleep(0.1)

    print(f"  📊 Plenumdan {len(COLLECTED_PLENUM_BANDS)} ta tegishli band topildi.")


# ============================================================
# 7. YAKUNIY XULOSA (JPK + PLENUM)
# ============================================================
def generate_final_conclusion():
    print(f"\n🧠 Yakuniy xulosa shakllantirilmoqda (JPK + Plenum)...")

    # JPK moddalarini formatlash
    jpk_text = ""
    for item in COLLECTED_ARTICLES:
        jpk_text += f"""
### JPK {item.get('modda_raqami')}-modda
- Sarlavha: {item.get('modda_sarlavhasi')}
- Kazusdagi holat: {item.get('kazusdagi_holat')}
- Qonuniy asos: {item.get('qonuniy_asos')}
- Havola: {item.get('lex_url')}
"""

    # Plenum bandlarini formatlash
    plenum_text = ""
    for band in COLLECTED_PLENUM_BANDS:
        plenum_text += f"""
### Plenum bandi {band.get('band_raqami')}.{band.get('xatboshi')}
- Mazmuni: {band.get('mazmuni')}
- Matn: {band.get('matn')[:200]}...
- Havola: {band.get('band_url')}
- Bog'liq JPK moddalari: {band.get('bogliq_jpk_moddalari')}
"""

    final_prompt = f"""Siz O'zbekiston Respublikasi Jinoyat-protsessual kodeksi va Oliy sud Plenum qarorlari bo'yicha professional huquqshunossiz.

KAZUS:
{KAZUS_MATNI}

============================================================
JPK DAN TOPILGAN ALOQADOR MODDALAR:
{jpk_text}

PLENUM QARORLARIDAN TOPILGAN TEGISHLI BANDLAR:
{plenum_text}
============================================================

VAZIFA:
Yuqoridagi JPK moddalari va Plenum qarorlari bandlariga asoslanib, kazus bo'yicha professional huquqiy xulosa tayyorlang.

TALAB QILINADIGAN JAVOB FORMATI (IRAC usuli):

I — ISSUE (Muammo):
Kazusdagi asosiy huquqiy masalalarni 4-6 gapda yozing.

R — RULE (Qonun qoidasi va Plenum izohlari):
JPK moddalarini va Plenum qarorlarining tegishli bandlarini keltiring. Har bir qonun qoidasiga havola qo'shing.

A — APPLICATION (Qonunni kazusga qo'llash):
Har bir masala bo'yicha kazusdagi faktlarni qonun va Plenum tushuntirishlari bilan solishtiring.

C — CONCLUSION (Xulosa):
5-7 gapda yakuniy xulosani yozing. "Yakuniy javob: ..." deb aniq xulosa bering.

MUHIM QOIDALAR:
1. Hech qanday jadval ishlatmang
2. Har bir JPK moddasi va Plenum bandi uchun havolani qavs ichida ko'rsating
3. Javob kamida 600 so'zdan iborat bo'lsin
4. Oddiy, tushunarli tilda yozing, lekin professional atamalardan qochmang
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_PRO,
            messages=[
                {"role": "system",
                 "content": "Siz O'zbekiston Jinoyat-protsessual kodeksi va Oliy sud Plenum qarorlari bo'yicha professional huquqshunossiz. Sizning javoblaringiz IRAC usulida, jadvalsiz, havolalar bilan va kamida 600 so'zdan iborat bo'ladi."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.7,
            extra_headers=extra_headers,
            extra_body={
                "thinking": {"type": "enabled"},
                "reasoning_effort": "high"
            }
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Xulosa shakllantirishda xato: {e}"


# ============================================================
# 8. ASOSIY FUNKSIYA
# ============================================================
def run_pipeline():
    print("=" * 70)
    print("🚀 LexAI v4 — JPK + Plenum qarorlari integratsiyalashgan tahlil tizimi")
    print("=" * 70)

    # 1. JPK boblarini skanerlash
    scan_jpk_boblar()

    # 2. Plenum qarorlarini skanerlash
    scan_plenum_qarorlari()

    # 3. Natijalar statistikasi
    print("\n" + "-" * 50)
    print("📊 TOPILGAN NATIJALAR:")
    print(f"   JPK moddalari: {len(COLLECTED_ARTICLES)} ta")
    print(f"   Plenum bandlari: {len(COLLECTED_PLENUM_BANDS)} ta")
    print("-" * 50)

    if not COLLECTED_ARTICLES and not COLLECTED_PLENUM_BANDS:
        print("\n⚠️ Hech qanday aloqador ma'lumot topilmadi.")
        return

    # 4. Yakuniy xulosa
    conclusion = generate_final_conclusion()

    print("\n" + "=" * 80)
    print("🏆 YAKUNIY XULOSA (JPK + Plenum qarorlari asosida)")
    print("=" * 80)
    print(conclusion)
    print("=" * 80)

    # 5. Saqlash
    with open("lexai_v4_xulosa.txt", "w", encoding="utf-8") as f:
        f.write(conclusion)

    # 6. Qo'shimcha ma'lumotlarni saqlash
    full_data = {
        "kazus": KAZUS_MATNI,
        "jpk_moddalar": COLLECTED_ARTICLES,
        "plenum_bandlari": COLLECTED_PLENUM_BANDS,
        "xulosa": conclusion
    }
    with open("lexai_v4_full_data.json", "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)

    print("\n💾 Natijalar saqlandi:")
    print("   • lexai_v4_xulosa.txt — yozma xulosa")
    print("   • lexai_v4_full_data.json — to'liq ma'lumotlar")

    # 7. Havolalar ro'yxati
    print("\n📋 ISHLATILGAN HAVOLALAR:")
    for item in COLLECTED_ARTICLES:
        print(f"   • JPK {item.get('modda_raqami')}: {item.get('lex_url')}")
    for band in COLLECTED_PLENUM_BANDS:
        print(f"   • Plenum band {band.get('band_raqami')}.{band.get('xatboshi')}: {band.get('band_url')}")


if __name__ == "__main__":
    run_pipeline()