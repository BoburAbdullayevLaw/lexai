import os
import json
import glob
import time
import threading
from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
# 1. MUHITNI YUKLASH VA KONFIGURATSIYA
# ============================================================
load_dotenv()

OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')
TOKENHARBOR_KEY = os.environ.get('TOKENHARBOR_API_KEY')
TOKENHARBOR_BASE = os.environ.get('TOKENHARBOR_BASE_URL', 'https://tokenharbor.ai/v1')
BYNARA_KEY = os.environ.get('BYNARA_API_KEY')
BYNARA_BASE = os.environ.get('BYNARA_BASE_URL', 'https://router.bynara.id/v1')

if not OPENROUTER_KEY:
    raise ValueError("OPENROUTER_API_KEY topilmadi.")
if not TOKENHARBOR_KEY:
    raise ValueError("TOKENHARBOR_API_KEY topilmadi.")

# Client 1: OpenRouter (JK qismi 1 + JPK qism 1-2 + Pro javob)
client_openrouter = OpenAI(
    api_key=OPENROUTER_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Client 2: TokenHarbor (JK qismi 2 — RPM cheklov yo'q)
client_tokenharbor = OpenAI(
    api_key=TOKENHARBOR_KEY,
    base_url=TOKENHARBOR_BASE
)

# Client 3: Bynara (JK qismi 3 + JPK qismi 3)
client_bynara = None
if BYNARA_KEY:
    client_bynara = OpenAI(
        api_key=BYNARA_KEY,
        base_url=BYNARA_BASE
    )

extra_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "HTTP-Referer": "https://lexai.uz",
    "X-Title": "LexAI Legal Analysis"
}

# ============================================================
# 2. MODELLAR VA SOZLAMALAR
# ============================================================
JK_MODEL_1 = "deepseek/deepseek-v4-flash"                          # JK qism 1 — OpenRouter
JK_MODEL_2 = os.environ.get('TOKENHARBOR_MODEL', 'deepseek-v4-flash:free')  # JK qism 2 — TokenHarbor
JK_MODEL_3 = os.environ.get('BYNARA_MODEL', 'nemotron-3-ultra-free')        # JK qism 3 — Bynara

JPK_MODEL_1 = "deepseek/deepseek-v4-flash-0731"         # JPK qism 1 — OpenRouter
JPK_MODEL_2 = "deepseek/deepseek-v4-flash-vision-exp"   # JPK qism 2 — OpenRouter
JPK_MODEL_3 = os.environ.get('BYNARA_MODEL', 'nemotron-3-ultra-free')  # JPK qism 3 — Bynara

MAIN_MODEL = "deepseek/deepseek-v4-pro"  # Yakuniy IRAC javob

BATCH_SIZE = 5

JK_DOC_ID = "-111453"
JPK_DOC_ID = "-111460"

JK_BASE_URL = f"https://lex.uz/docs/{JK_DOC_ID}"
JPK_BASE_URL = f"https://lex.uz/docs/{JPK_DOC_ID}"

JK_DIR = "data/jinoyat/kodekslar/jk"
JPK_DIR = "data/jinoyat/kodekslar/jpk"

COLLECTED_JK = []
COLLECTED_JPK = []
JK_LOCK = threading.Lock()
JPK_LOCK = threading.Lock()


# ============================================================
# 3. KAZUS MATNI
# ============================================================
KAZUS_MATNI = """KAZUS:
Voyaga yetmagan shaxslar oʻrtasida kelib chiqqan oʻzaro janjal natijasida 2025-yil 10-yanvar kuni taxminan soat 12:30 larda voyaga yetmagan 16 yoshli Anvar ismli shaxs janjal davomida yonida boʻlgan pichoq bilan Bobur ismli shaxsning chap qorin qismiga bir marotaba urib, tan jarohati yetkazgan.

Voqea joyi koʻzdan kechirilganda voqea joyidan qonga oʻxshash qizgʻish dogʻlari boʻlgan pichoq, oq rangdagi mato parchalari, bir dona charm oyoq kiyim topildi hamda ashyoviy dalil sifatida ish materiallariga qoʻshib qoʻyildi. Ushbu narsalar voqea joyini koʻzdan kechirish bayonnomasiga kiritilmadi.

Sudga oid tibbiy ekspertizaning xulosasiga koʻra Bobur ismli shaxsga ogʻir shikast yetkazilgani aniqlangan. Biroq, tergovchi ekspert xulosasiga qoʻshilmagan.

Dastlabki tergov jarayonida Anvar oʻz aybini toʻliq tan olib, aniq koʻrsatma beradi. Sud muhokamasida Anvar koʻrsatuvlarini oʻzgartirib, aybni tan olmagan va tergovchi ishni tugatishga vaʼda berib, uni majburlaganini bildirgan.

Sud jarayonida jabrlanuvchi guvohlik berishdan bosh tortgan. Ikki nafar guvohlarning koʻrsatuvlari esa qarama-qarshi boʻlgan."""


def get_kazus() -> str:
    return KAZUS_MATNI


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


def format_jk_modda_for_prompt(modda_data: dict) -> str:
    lines = []
    sarlavha = modda_data.get("sarlavha", f"{modda_data.get('n')}-modda")
    sarlavha_id = modda_data.get("sarlavha_id", "")
    id_qismi = f" (ID: {sarlavha_id})" if sarlavha_id else ""
    lines.append(f"\n{sarlavha}{id_qismi}")

    for qism in modda_data.get("qismlar", []):
        q_id = qism.get("id", "")
        q_text = qism.get("matn", "")
        id_tag = f" [ID:{q_id}]" if q_id else ""
        lines.append(f"  Qism {qism.get('q')}{id_tag}: {q_text}")

        for band in qism.get("bandlar", []):
            b_id = band.get("id", "")
            b_text = band.get("matn", "")
            id_tag = f" [ID:{b_id}]" if b_id else ""
            lines.append(f"    Band {band.get('b')}{id_tag}: {b_text}")

    if "umumiy_sharh" in modda_data:
        sharh = modda_data["umumiy_sharh"]
        if isinstance(sharh, list) and sharh:
            lines.append("  UMUMIY SHARH:")
            for item in sharh[:3]:
                lines.append(f"    {item}")

    if "sharh" in modda_data:
        sharh = modda_data["sharh"]
        lines.append("  SHARH:")
        if isinstance(sharh, list):
            for item in sharh[:5]:
                lines.append(f"    {item}")

    for qism in modda_data.get("qismlar", []):
        if "sharh" in qism:
            q_sharh = qism["sharh"]
            if isinstance(q_sharh, list):
                for item in q_sharh[:3]:
                    lines.append(f"    {item}")
        for band in qism.get("bandlar", []):
            if "sharh" in band:
                b_sharh = band["sharh"]
                if isinstance(b_sharh, list):
                    for item in b_sharh[:2]:
                        lines.append(f"    {item}")

    return "\n".join(lines)


def format_jpk_modda_for_prompt(modda_data: dict) -> str:
    lines = []
    sarlavha = modda_data.get("sarlavha", f"{modda_data.get('n')}-modda")
    sarlavha_id = modda_data.get("sarlavha_id", "")
    id_qismi = f" (ID: {sarlavha_id})" if sarlavha_id else ""
    lines.append(f"\n{sarlavha}{id_qismi}")

    for qism in modda_data.get("qismlar", []):
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


def load_json_file(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


def save_backup():
    backup = {
        "jk_moddalar": COLLECTED_JK,
        "jpk_moddalar": COLLECTED_JPK,
    }
    with open("lexai_v6_backup.json", "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)
    print("📦 Backup saqlandi: lexai_v6_backup.json")


def extract_element_id(sarlavha_id: str) -> str:
    if "#" in sarlavha_id:
        return sarlavha_id.split("#")[-1]
    return ""


def safe_api_call(client_instance, model_name, prompt, max_retries=5, provider_name=""):
    """API chaqiruvini rate-limit himoyasi bilan amalga oshiradi."""
    kwargs = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "extra_headers": extra_headers,
        "extra_body": {"thinking": {"type": "disabled"}},
        "response_format": {"type": "json_object"}
    }

    for attempt in range(max_retries):
        try:
            response = client_instance.chat.completions.create(**kwargs)
            raw_text = response.choices[0].message.content.strip()

            if "<!DOCTYPE" in raw_text or "403" in raw_text:
                wait = 5
                print(f"  ⚠️ [{provider_name}] Cheklov (403), {wait}s kutish...")
                time.sleep(wait)
                continue

            return raw_text

        except Exception as e:
            err_str = str(e).lower()

            # 429 — Rate limit
            if "429" in err_str or "rate" in err_str or "too many" in err_str:
                # Retry-After ni topishga harakat qilish
                wait = 30  # default
                try:
                    if hasattr(e, 'response') and e.response is not None:
                        retry_after = e.response.headers.get('retry-after')
                        if retry_after:
                            wait = int(retry_after) + 2
                except:
                    pass

                print(f"  ⏳ [{provider_name}] Rate limit! {wait}s kutish (qayta: {attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue

            # Boshqa xatolar
            print(f"  ❌ [{provider_name}] Xato: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return None

    print(f"  ❌ [{provider_name}] {max_retries} ta urinishdan keyin xato")
    return None


# ============================================================
# 5. JK SKANERLASH — UMUMIY FUNKSIYA
# ============================================================
def _scan_jk_part(files: list, model_name: str, client_instance, part_label: str, kazus: str):
    """JK ning bir qismini skanerlaydi."""
    total_files = len(files)
    total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE
    local_collected = []

    print(f"\n   [{part_label}] Model: {model_name}")
    print(f"   [{part_label}] Moddalar: {total_files}, Batch: {total_batches}")
    print(f"   [{part_label}] Boshlandi: {time.strftime('%H:%M:%S')}")

    for batch_idx in range(0, total_files, BATCH_SIZE):
        batch_files = files[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        batch_moddalar = []
        for file_path in batch_files:
            try:
                modda_data = load_json_file(file_path)
                batch_moddalar.append(modda_data)
            except Exception as e:
                print(f"  ❌ [{part_label}] {os.path.basename(file_path)}: {e}")

        if not batch_moddalar:
            continue

        batch_text = ""
        for modda in batch_moddalar:
            batch_text += format_jk_modda_for_prompt(modda) + "\n"

        prompt = f"""Siz O'zbekiston Jinoyat kodeksi bo'yicha professional huquqshunossiz.

KAZUS:
{kazus}

JK MODDALARI (Batch {batch_num}/{total_batches}):
{batch_text}

VAZIFA: Qaysi moddalar kazusga aloqador?

MUHIM: Har bir modda uchun "n" maydonidagi raqamni "modda_raqami" sifatida, "sarlavha_id" dan oxirgi qismni "element_id" sifatida oling.

JAVOBNI JSON FORMATIDA BERING:
{{
  "relevant_moddalar": [
    {{
      "modda_raqami": <n maydonidan raqam>,
      "modda_sarlavhasi": "<sarlavha matni>",
      "element_id": "<sarlavha_id dan oxirgi qism>",
      "qism_yoki_band": "<qism/band>",
      "kazusdagi_holat": "<1-2 jumla>",
      "qonuniy_asos": "<1-2 jumla>",
      "buzilganmi": true
    }}
  ]
}}

Agar aloqador yo'q bo'lsa: {{"relevant_moddalar": []}}"""

        time.sleep(0.3)

        raw_text = safe_api_call(client_instance, model_name, prompt, max_retries=5, provider_name=f"JK-{part_label}")

        if raw_text is None:
            print(f"  ❌ [{part_label} {batch_num}/{total_batches}] API xato, o'tkazib yuborildi")
            continue

        try:
            clean_content = clean_to_json(raw_text)
            res_json = json.loads(clean_content)
            relevant_list = res_json.get("relevant_moddalar", [])

            if relevant_list:
                valid_items = []
                for item in relevant_list:
                    modda_raqami = item.get("modda_raqami")
                    modda_sarlavhasi = item.get("modda_sarlavhasi")

                    if modda_raqami is None or modda_sarlavhasi is None:
                        continue

                    element_id = item.get("element_id", "")
                    if not element_id:
                        for md in batch_moddalar:
                            if md.get("n") == modda_raqami:
                                element_id = extract_element_id(md.get("sarlavha_id", ""))
                                break

                    lex_link = f"{JK_BASE_URL}#{element_id}" if element_id else JK_BASE_URL

                    local_collected.append({
                        "manba": "JK",
                        "modda_raqami": modda_raqami,
                        "modda_sarlavhasi": modda_sarlavhasi,
                        "element_id": element_id,
                        "lex_url": lex_link,
                        "qism_yoki_band": item.get("qism_yoki_band", ""),
                        "kazusdagi_holat": item.get("kazusdagi_holat", ""),
                        "qonuniy_asos": item.get("qonuniy_asos", ""),
                        "buzilganmi": item.get("buzilganmi", True)
                    })
                    valid_items.append(item)

                moddalar_str = ", ".join(str(m.get("modda_raqami")) for m in valid_items)
                print(f"  ✅ [{part_label} {batch_num}/{total_batches}] → {len(valid_items)} modda: [{moddalar_str}]")
            else:
                print(f"  ⚪ [{part_label} {batch_num}/{total_batches}] → Yo'q")

        except Exception as e:
            print(f"  ❌ [{part_label} {batch_num}/{total_batches}] Xato: {e}")

    print(f"\n   📊 [{part_label}] Natija: {len(local_collected)} ta modda topildi")
    return local_collected


# ============================================================
# 6. AGENT 1: JK TAHLCILI (3 MODEL PARALLEL)
# ============================================================
def scan_jk(kazus: str):
    print(f"\n{'='*60}")
    print("📚 AGENT 1: JK TAHLCILI — 3 MODEL PARALLEL")
    print(f"{'='*60}")

    all_files = glob.glob(os.path.join(JK_DIR, "modda_*.json"))
    all_files.sort(key=natural_sort_key)

    total = len(all_files)
    third = total // 3
    part_1 = all_files[:third]
    part_2 = all_files[third:2*third]
    part_3 = all_files[2*third:]

    print(f"   Jami: {total} modda")
    print(f"   Qism 1: {len(part_1)} modda → {JK_MODEL_1} (OpenRouter)")
    print(f"   Qism 2: {len(part_2)} modda → {JK_MODEL_2} (TokenHarbor)")
    print(f"   Qism 3: {len(part_3)} modda → {JK_MODEL_3} (Bynara)")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}")

    results = [None, None, None]

    def worker1():
        results[0] = _scan_jk_part(part_1, JK_MODEL_1, client_openrouter, "QISM-1", kazus)

    def worker2():
        results[1] = _scan_jk_part(part_2, JK_MODEL_2, client_tokenharbor, "QISM-2", kazus)

    def worker3():
        results[2] = _scan_jk_part(part_3, JK_MODEL_3, client_tokenharbor, "QISM-3", kazus)

    t1 = threading.Thread(target=worker1)
    t2 = threading.Thread(target=worker2)
    t3 = threading.Thread(target=worker3)

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

    with JK_LOCK:
        for r in results:
            if r:
                COLLECTED_JK.extend(r)

    print(f"\n   📊 JAMI JK: {len(COLLECTED_JK)} ta modda topildi")
    print(f"   Tayyor: {time.strftime('%H:%M:%S')}")


# ============================================================
# 7. AGENT 2: JPK TAHLCILI — UMUMIY FUNKSIYA
# ============================================================
def _scan_jpk(all_files: list, model_name: str, client_instance, part_label: str, kazus: str):
    """JPK ning bir qismini skanerlaydi."""
    total_files = len(all_files)
    total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE
    local_collected = []

    print(f"\n   [{part_label}] Model: {model_name}")
    print(f"   [{part_label}] Moddalar: {total_files}, Batch: {total_batches}")
    print(f"   [{part_label}] Boshlandi: {time.strftime('%H:%M:%S')}")

    for batch_idx in range(0, total_files, BATCH_SIZE):
        batch_files = all_files[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        batch_moddalar = []
        for file_path in batch_files:
            try:
                modda_data = load_json_file(file_path)
                batch_moddalar.append(modda_data)
            except Exception as e:
                print(f"  ❌ [{part_label}] {os.path.basename(file_path)}: {e}")

        if not batch_moddalar:
            continue

        batch_text = ""
        for modda in batch_moddalar:
            batch_text += format_jpk_modda_for_prompt(modda) + "\n"

        prompt = f"""Siz O'zbekiston Jinoyat-protsessual kodeksi bo'yicha professional huquqshunossiz.

KAZUS:
{kazus}

JPK MODDALARI (Batch {batch_num}/{total_batches}):
{batch_text}

VAZIFA: Qaysi moddalar kazusga aloqador?

MUHIM: Har bir modda uchun "n" maydonidagi raqamni "modda_raqami" sifatida, "sarlavha_id" dan oxirgi qismni "element_id" sifatida oling.

JAVOBNI JSON FORMATIDA BERING:
{{
  "relevant_moddalar": [
    {{
      "modda_raqami": <n maydonidan raqam>,
      "modda_sarlavhasi": "<sarlavha matni>",
      "element_id": "<sarlavha_id dan oxirgi qism>",
      "qism_yoki_band": "<qism/band>",
      "kazusdagi_holat": "<1-2 jumla>",
      "qonuniy_asos": "<1-2 jumla>"
    }}
  ]
}}

Agar aloqador yo'q bo'lsa: {{"relevant_moddalar": []}}"""

        time.sleep(0.3)

        raw_text = safe_api_call(client_instance, model_name, prompt, max_retries=5, provider_name=f"JPK-{part_label}")

        if raw_text is None:
            print(f"  ❌ [{part_label} {batch_num}/{total_batches}] API xato, o'tkazib yuborildi")
            continue

        try:
            clean_content = clean_to_json(raw_text)
            res_json = json.loads(clean_content)
            relevant_list = res_json.get("relevant_moddalar", [])

            if relevant_list:
                valid_items = []
                for item in relevant_list:
                    modda_raqami = item.get("modda_raqami")
                    modda_sarlavhasi = item.get("modda_sarlavhasi")

                    if modda_raqami is None or modda_sarlavhasi is None:
                        continue

                    element_id = item.get("element_id", "")
                    if not element_id:
                        for md in batch_moddalar:
                            if md.get("n") == modda_raqami:
                                element_id = extract_element_id(md.get("sarlavha_id", ""))
                                break

                    lex_link = f"{JPK_BASE_URL}#{element_id}" if element_id else JPK_BASE_URL

                    local_collected.append({
                        "manba": "JPK",
                        "modda_raqami": modda_raqami,
                        "modda_sarlavhasi": modda_sarlavhasi,
                        "element_id": element_id,
                        "lex_url": lex_link,
                        "qism_yoki_band": item.get("qism_yoki_band", ""),
                        "kazusdagi_holat": item.get("kazusdagi_holat", ""),
                        "qonuniy_asos": item.get("qonuniy_asos", "")
                    })
                    valid_items.append(item)

                moddalar_str = ", ".join(str(m.get("modda_raqami")) for m in valid_items)
                print(f"  ✅ [{part_label} {batch_num}/{total_batches}] → {len(valid_items)} modda: [{moddalar_str}]")
            else:
                print(f"  ⚪ [{part_label} {batch_num}/{total_batches}] → Yo'q")

        except Exception as e:
            print(f"  ❌ [{part_label} {batch_num}/{total_batches}] Xato: {e}")

    print(f"\n   📊 [{part_label}] Natija: {len(local_collected)} ta modda topildi")
    print(f"   [{part_label}] Tayyor: {time.strftime('%H:%M:%S')}")
    return local_collected


# ============================================================
# 8. YAKUNIY XULOSA — IRAC USULIDA
# ============================================================
def generate_irac(kazus: str):
    print(f"\n{'='*60}")
    print("🧠 YAKUNIY XULOSA — IRAC USULIDA")
    print(f"{'='*60}")

    jk_text = ""
    for item in COLLECTED_JK:
        jk_text += f"""
### JK {item.get('modda_raqami')}-modda
- Sarlavha: {item.get('modda_sarlavhasi')}
- Qism/Band: {item.get('qism_yoki_band')}
- Kazusdagi holat: {item.get('kazusdagi_holat')}
- Qonuniy asos: {item.get('qonuniy_asos')}
- Buzilganmi: {item.get('buzilganmi')}
- Havola: {item.get('lex_url')}
"""

    jpk_text = ""
    for item in COLLECTED_JPK:
        jpk_text += f"""
### JPK {item.get('modda_raqami')}-modda
- Sarlavha: {item.get('modda_sarlavhasi')}
- Qism/Band: {item.get('qism_yoki_band')}
- Kazusdagi holat: {item.get('kazusdagi_holat')}
- Qonuniy asos: {item.get('qonuniy_asos')}
- Havola: {item.get('lex_url')}
"""

    final_prompt = f"""Siz O'zbekiston Jinoyat kodeksi va Jinoyat-protsessual kodeksi bo'yicha professional huquqshunossiz.

KAZUS:
{kazus}

============================================================
JK TOPILGANLARI:
{jk_text if jk_text else "Topilmadi"}

JPK TOPILGANLARI:
{jpk_text if jpk_text else "Topilmadi"}
============================================================

IRAC USULIDA JAVOB YOZING:

I — ISSUE (Muammo):
4-6 gapda. "Ushbu kazusda quyidagi huquqiy masalalar mavjud..."

R — RULE (Qonun):
JK va JPK moddalarini keltiring. Har bir modda uchun lex.uz havolasini ko'rsating.

A — APPLICATION (Qo'llash):
Kazus faktlarini qonun bilan solishtiring.

C — CONCLUSION (Xulosa):
5-7 gapda. "Yakuniy javob: ..." deb aniq xulosa.

QOIDALAR:
1. Jadval ishlatmang
2. Kamida 600 so'z
3. Barcha havolalarni ko'rsating: https://lex.uz/docs/<doc_id>#<element_id>
4. Professional tilda yozing
5. Disclamer qo'shing"""

    try:
        for attempt in range(5):
            try:
                response = client_openrouter.chat.completions.create(
                    model=MAIN_MODEL,
                    messages=[
                        {"role": "system", "content": "Siz professional huquqshunossiz. IRAC usulida, jadvalsiz, havolalar bilan javob bering."},
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
                err_str = str(e).lower()
                if "429" in err_str or "rate" in err_str:
                    wait = 30
                    try:
                        if hasattr(e, 'response') and e.response is not None:
                            retry_after = e.response.headers.get('retry-after')
                            if retry_after:
                                wait = int(retry_after) + 2
                    except:
                        pass
                    print(f"  ⏳ [IRAC] Rate limit! {wait}s kutish ({attempt+1}/5)...")
                    time.sleep(wait)
                else:
                    raise

        return "❌ IRAC: 5 ta urinishdan keyin javob olinmadi"

    except Exception as e:
        return f"❌ Xato: {e}"


# ============================================================
# 9. ASOSIY PIPELINE — 6 THREAD PARALLEL
# ============================================================
def run_pipeline():
    print("=" * 60)
    print("🚀 LexAI v6 — 5 THREAD PARALLEL")
    print("=" * 60)
    print(f"   JK Qism 1:  {JK_MODEL_1} (OpenRouter)")
    print(f"   JK Qism 2:  {JK_MODEL_2} (TokenHarbor)")
    print(f"   JK Qism 3:  {JK_MODEL_3} (Bynara)")
    print(f"   JPK Qism 1: {JPK_MODEL_1} (OpenRouter)")
    print(f"   JPK Qism 2: {JPK_MODEL_2} (OpenRouter)")
    print(f"   JPK Qism 3: {JPK_MODEL_3} (Bynara)")
    print(f"   Pro model:  {MAIN_MODEL}")
    print(f"   Batch: {BATCH_SIZE} ta modda")
    print("=" * 60)

    kazus = get_kazus()
    start_time = time.time()

    # JK fayllarini 3 ga bo'lish
    jk_files = glob.glob(os.path.join(JK_DIR, "modda_*.json"))
    jk_files.sort(key=natural_sort_key)
    jk_total = len(jk_files)
    jk_third = jk_total // 3
    jk_part_1 = jk_files[:jk_third]
    jk_part_2 = jk_files[jk_third:2*jk_third]
    jk_part_3 = jk_files[2*jk_third:]

    # JPK fayllarini 3 ga bo'lish
    jpk_files = glob.glob(os.path.join(JPK_DIR, "modda_*.json"))
    jpk_files.sort(key=natural_sort_key)
    jpk_total = len(jpk_files)
    jpk_third = jpk_total // 3
    jpk_part_1 = jpk_files[:jpk_third]
    jpk_part_2 = jpk_files[jpk_third:2*jpk_third]
    jpk_part_3 = jpk_files[2*jpk_third:]

    print(f"\n   JK: {jk_total} modda → 3 qism ({len(jk_part_1)}/{len(jk_part_2)}/{len(jk_part_3)})")
    print(f"   JPK: {jpk_total} modda → 3 qism ({len(jpk_part_1)}/{len(jpk_part_2)}/{len(jpk_part_3)})")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}")

    results_jk = [None, None, None]
    results_jpk = [None, None, None]

    # JK workerlari
    def worker_jk1():
        results_jk[0] = _scan_jk_part(jk_part_1, JK_MODEL_1, client_openrouter, "JK-1", kazus)
    def worker_jk2():
        results_jk[1] = _scan_jk_part(jk_part_2, JK_MODEL_2, client_tokenharbor, "JK-2", kazus)
    def worker_jk3():
        results_jk[2] = _scan_jk_part(jk_part_3, JK_MODEL_3, client_bynara, "JK-3", kazus)

    # JPK workerlari
    def worker_jpk1():
        results_jpk[0] = _scan_jpk(jpk_part_1, JPK_MODEL_1, client_openrouter, "JPK-1", kazus)
    def worker_jpk2():
        results_jpk[1] = _scan_jpk(jpk_part_2, JPK_MODEL_2, client_openrouter, "JPK-2", kazus)
    def worker_jpk3():
        results_jpk[2] = _scan_jpk(jpk_part_3, JPK_MODEL_3, client_bynara, "JPK-3", kazus)

    # 6 ta thread bir vaqtda ishga tushadi
    threads = [
        threading.Thread(target=worker_jk1),
        threading.Thread(target=worker_jk2),
        threading.Thread(target=worker_jk3),
        threading.Thread(target=worker_jpk1),
        threading.Thread(target=worker_jpk2),
        threading.Thread(target=worker_jpk3),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Natijalarni yig'ish
    with JK_LOCK:
        for r in results_jk:
            if r:
                COLLECTED_JK.extend(r)
    with JPK_LOCK:
        for r in results_jpk:
            if r:
                COLLECTED_JPK.extend(r)

    print(f"\n{'='*60}")
    print("📊 NATIJALAR:")
    print(f"{'='*60}")
    print(f"   JK: {len(COLLECTED_JK)} modda")
    print(f"   JPK: {len(COLLECTED_JPK)} modda")

    if not COLLECTED_JK and not COLLECTED_JPK:
        print("\n⚠️ Aloqador ma'lumot topilmadi.")
        return

    conclusion = generate_irac(kazus)

    print(f"\n{'='*60}")
    print("🏆 YAKUNIY XULOSA")
    print(f"{'='*60}")
    print(conclusion)

    with open("lexai_v6_xulosa.txt", "w", encoding="utf-8") as f:
        f.write(conclusion)

    full_data = {
        "kazus": kazus,
        "jk_moddalar": COLLECTED_JK,
        "jpk_moddalar": COLLECTED_JPK,
        "xulosa": conclusion
    }
    with open("lexai_v6_full_data.json", "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    jk_count = len(glob.glob(os.path.join(JK_DIR, "modda_*.json")))
    jpk_count = len(glob.glob(os.path.join(JPK_DIR, "modda_*.json")))
    jk_batches = (jk_count + BATCH_SIZE - 1) // BATCH_SIZE
    jpk_batches = (jpk_count + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"\n{'='*60}")
    print("📊 HISOBOT:")
    print(f"{'='*60}")
    print(f"   JK: {jk_count} modda → {jk_batches} batch (3 ga bo'lindi)")
    print(f"   JPK: {jpk_count} modda → {jpk_batches} batch (3 ga bo'lindi)")
    print(f"   Vaqt: {mins} daqiqa {secs} soniya")
    print(f"{'='*60}")

    print(f"\n💾 Saqlandi:")
    print(f"   • lexai_v6_xulosa.txt")
    print(f"   • lexai_v6_full_data.json")

    print(f"\n📋 HAVOLALAR:")
    for item in COLLECTED_JK:
        print(f"   • JK {item.get('modda_raqami')}: {item.get('lex_url')}")
    for item in COLLECTED_JPK:
        print(f"   • JPK {item.get('modda_raqami')}: {item.get('lex_url')}")

    print(f"\n{'='*60}")
    print("✅ TUGADI")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_pipeline()
