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

OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')

if not OPENROUTER_KEY:
    raise ValueError("OPENROUTER_API_KEY topilmadi. .env faylini tekshiring.")

# OpenRouter client
client = OpenAI(
    api_key=OPENROUTER_KEY,
    base_url="https://openrouter.ai/api/v1"
)

extra_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "HTTP-Referer": "https://lexai.uz",
    "X-Title": "LexAI Legal Analysis"
}

# ============================================================
# 2. MODELLAR VA SOZLAMALAR (OpenRouter — DeepSeek pullik)
# ============================================================
# Har bir agent uchun alohida model
JK_READER_MODEL = "deepseek/deepseek-v4-flash"              # JK (Jinoyat Kodeksi)
JPK_READER_MODEL = "deepseek/deepseek-v4-flash-0731"        # JPK (Jinoyat-Protsessual Kodeksi)
PLENUM_READER_MODEL = "deepseek/deepseek-v4-flash-vision-exp" # Plenum qarorlari

# Asosiy model — yakuniy javob berish uchun
MAIN_MODEL = "deepseek/deepseek-v4-pro"

# JSON response format qo'llab-quvvatlaydigan modellar
MODELS_WITH_JSON = {
    JK_READER_MODEL: True,
    JPK_READER_MODEL: True,
    PLENUM_READER_MODEL: True
}

BATCH_SIZE = 2  # Har bir batchda 2 ta modda (model uchun osonroq)

JK_DOC_ID = "-111453"
JPK_DOC_ID = "-111460"
PLENUM_DOC_ID = "-6523582"

JK_BASE_URL = f"https://lex.uz/docs/{JK_DOC_ID}"
JPK_BASE_URL = f"https://lex.uz/docs/{JPK_DOC_ID}"
PLENUM_BASE_URL = f"https://lex.uz/docs/{PLENUM_DOC_ID}"

JK_DIR = "data/jinoyat/kodekslar/jk"
JPK_DIR = "data/jinoyat/kodekslar/jpk"
PLENUM_DIR = "data/jinoyat/plenumlar"

COLLECTED_JK = []
COLLECTED_JPK = []
COLLECTED_PLENUM = []

def get_model_config(model_id: str) -> tuple:
    """Model konfiguratsiyasini qaytaradi (model_id, supports_json)"""
    supports_json = MODELS_WITH_JSON.get(model_id, False)
    return model_id, supports_json

# ============================================================
# 3. KAZUS MATNI (Foydalanuvchi o'zgartiradi)
# ============================================================
KAZUS_MATNI = """KAZUS:
Voyaga yetmagan shaxslar oʻrtasida kelib chiqqan oʻzaro janjal natijasida 2025-yil 10-yanvar kuni taxminan soat 12:30 larda voyaga yetmagan 16 yoshli Anvar ismli shaxs janjal davomida yonida boʻlgan pichoq bilan Bobur ismli shaxsning chap qorin qismiga bir marotaba urib, tan jarohati yetkazgan.

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

    if "sharh" in modda_data:
        sharh = modda_data["sharh"]
        lines.append("  SHARH:")
        if isinstance(sharh, dict):
            for key, value in sharh.items():
                if isinstance(value, list):
                    for item in value:
                        lines.append(f"    {key}: {item}")
                else:
                    lines.append(f"    {key}: {value}")
        elif isinstance(sharh, list):
            for item in sharh:
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
    """UTF-8 BOM ni hisobga olib JSON faylni o'qish"""
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
        "plenum_bandlari": COLLECTED_PLENUM
    }
    with open("lexai_v5_backup.json", "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)
    print("📦 Backup saqlandi: lexai_v5_backup.json")


# ============================================================
# 5. AGENT 1: JK TAHLCILI (Batch Processing)
# ============================================================
def scan_jk():
    print(f"\n{'='*60}")
    print("📚 AGENT 1: JK TAHLCILI (Jinoyat Kodeksi)")
    print(f"{'='*60}")

    all_files = glob.glob(os.path.join(JK_DIR, "modda_*.json"))
    all_files.sort(key=natural_sort_key)

    total_files = len(all_files)
    total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"   Jami: {total_files} modda, {total_batches} batch")
    print(f"   JK model: {JK_READER_MODEL}")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}\n")

    print(f"   DEBUG: Starting loop over {total_files} files, {total_batches} batches")
    for batch_idx in range(0, total_files, BATCH_SIZE):
        batch_files = all_files[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        
        print(f"   DEBUG: Batch {batch_num}/{total_batches} - files: {[os.path.basename(f) for f in batch_files]}")

        batch_moddalar = []
        for file_path in batch_files:
            try:
                modda_data = load_json_file(file_path)
                batch_moddalar.append(modda_data)
            except Exception as e:
                print(f"  ❌ {os.path.basename(file_path)}: {e}")

        if not batch_moddalar:
            continue

        batch_text = ""
        for modda in batch_moddalar:
            batch_text += format_jk_modda_for_prompt(modda) + "\n"

        prompt = f"""Siz O'zbekiston Jinoyat kodeksi bo'yicha professional huquqshunossiz.

KAZUS:
{KAZUS_MATNI}

JK MODDALARI (Batch {batch_num}/{total_batches}):
{batch_text}

VAZIFA: Qaysi moddalar kazusga aloqador?

MUHIM: Har bir modda uchun "n" maydonidagi raqamni "modda_raqami" sifatida, "sarlavha_id" ni "element_id" sifatida oling.

JAVOBNI JSON FORMATIDA BERING:
{{
  "relevant_moddalar": [
    {{
      "modda_raqami": <n maydonidan raqam>,
      "modda_sarlavhasi": "<sarlavha matni>",
      "element_id": "<sarlavha_id dan anchor qismi (masalan: -5449385)>",
      "qism_yoki_band": "<qism/band>",
      "kazusdagi_holat": "<1-2 jumla>",
      "qonuniy_asos": "<1-2 jumla>",
      "buzilganmi": true
    }}
  ]
}}

Agar aloqador yo'q bo'lsa: {{"relevant_moddalar": []}}"""

        # JK uchun alohida model
        reader_model, supports_json = get_model_config(JK_READER_MODEL)
        time.sleep(0.2)

        try:
            kwargs = {
                "model": reader_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "extra_headers": extra_headers,
                "extra_body": {"thinking": {"type": "disabled"}}
            }
            if supports_json:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**kwargs)

            raw_text = response.choices[0].message.content.strip()

            if "<!DOCTYPE" in raw_text or "403" in raw_text:
                print(f"  ⚠️ [{batch_num}/{total_batches}] Cheklov, 5s kutish...")
                time.sleep(5)
                continue

            clean_content = clean_to_json(raw_text)
            res_json = json.loads(clean_content)
            relevant_list = res_json.get("relevant_moddalar", [])

            if relevant_list:
                valid_items = []
                for item in relevant_list:
                    modda_raqami = item.get("modda_raqami")
                    modda_sarlavhasi = item.get("modda_sarlavhasi")
                    
                    # Skip invalid entries
                    if modda_raqami is None or modda_sarlavhasi is None:
                        continue
                    
                    element_id = item.get("element_id", "")
                    lex_link = f"{JK_BASE_URL}#{element_id}" if element_id else JK_BASE_URL

                    COLLECTED_JK.append({
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
                print(f"  ✅ [{batch_num}/{total_batches}] → {len(valid_items)} modda: [{moddalar_str}]")
            else:
                print(f"  ⚪ [{batch_num}/{total_batches}] → Yo'q")

        except Exception as e:
            print(f"  ❌ [{batch_num}/{total_batches}] Xato: {e}")

        if batch_num % 5 == 0:
            save_backup()

    print(f"\n   📊 Natija: {len(COLLECTED_JK)} ta modda topildi")
    print(f"   Tayyor: {time.strftime('%H:%M:%S')}")


# ============================================================
# 6. AGENT 2: JPK TAHLCILI (Batch Processing)
# ============================================================
def scan_jpk():
    print(f"\n{'='*60}")
    print("📚 AGENT 2: JPK TAHLCILI (Jinoyat-protsessual Kodeksi)")
    print(f"{'='*60}")

    all_files = glob.glob(os.path.join(JPK_DIR, "modda_*.json"))
    all_files.sort(key=natural_sort_key)

    total_files = len(all_files)
    total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"   Jami: {total_files} modda, {total_batches} batch")
    print(f"   JPK model: {JPK_READER_MODEL}")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}\n")

    for batch_idx in range(0, total_files, BATCH_SIZE):
        batch_files = all_files[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        batch_moddalar = []
        for file_path in batch_files:
            try:
                modda_data = load_json_file(file_path)
                batch_moddalar.append(modda_data)
            except Exception as e:
                print(f"  ❌ {os.path.basename(file_path)}: {e}")

        if not batch_moddalar:
            continue

        batch_text = ""
        for modda in batch_moddalar:
            batch_text += format_jpk_modda_for_prompt(modda) + "\n"

        prompt = f"""Siz O'zbekiston Jinoyat-protsessual kodeksi bo'yicha professional huquqshunossiz.

KAZUS:
{KAZUS_MATNI}

JPK MODDALARI (Batch {batch_num}/{total_batches}):
{batch_text}

VAZIFA: Qaysi moddalar kazusga aloqador?

MUHIM: Har bir modda uchun "n" maydonidagi raqamni "modda_raqami" sifatida, "sarlavha_id" ni "element_id" sifatida oling.

JAVOBNI JSON FORMATIDA BERING:
{{
  "relevant_moddalar": [
    {{
      "modda_raqami": <n maydonidan raqam>,
      "modda_sarlavhasi": "<sarlavha matni>",
      "element_id": "<sarlavha_id dan anchor qismi (masalan: -252766)>",
      "qism_yoki_band": "<qism/band>",
      "kazusdagi_holat": "<1-2 jumla>",
      "qonuniy_asos": "<1-2 jumla>"
    }}
  ]
}}

Agar aloqador yo'q bo'lsa: {{"relevant_moddalar": []}}"""

        # JPK uchun alohida model
        reader_model, supports_json = get_model_config(JPK_READER_MODEL)
        time.sleep(0.2)

        try:
            kwargs = {
                "model": reader_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "extra_headers": extra_headers,
                "extra_body": {"thinking": {"type": "disabled"}}
            }
            if supports_json:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**kwargs)

            raw_text = response.choices[0].message.content.strip()

            if "<!DOCTYPE" in raw_text or "403" in raw_text:
                print(f"  ⚠️ [{batch_num}/{total_batches}] Cheklov, 5s kutish...")
                time.sleep(5)
                continue

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
                    lex_link = f"{JPK_BASE_URL}#{element_id}" if element_id else JPK_BASE_URL

                    COLLECTED_JPK.append({
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
                print(f"  ✅ [{batch_num}/{total_batches}] → {len(valid_items)} modda: [{moddalar_str}]")
            else:
                print(f"  ⚪ [{batch_num}/{total_batches}] → Yo'q")

        except Exception as e:
            print(f"  ❌ [{batch_num}/{total_batches}] Xato: {e}")

        if batch_num % 5 == 0:
            save_backup()

    print(f"\n   📊 Natija: {len(COLLECTED_JPK)} ta modda topildi")
    print(f"   Tayyor: {time.strftime('%H:%M:%S')}")


# ============================================================
# 7. AGENT 3: PLENUM TAHLCILI
# ============================================================
def scan_plenum():
    print(f"\n{'='*60}")
    print("📚 AGENT 3: PLENUM TAHLCILI (Oliy Sud Qarorlari)")
    print(f"{'='*60}")

    all_topics = [d for d in os.listdir(PLENUM_DIR) if os.path.isdir(os.path.join(PLENUM_DIR, d))]

    print(f"   Jami: {len(all_topics)} mavzu")
    print(f"   Plenum model: {PLENUM_READER_MODEL}")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}\n")

    for idx, topic in enumerate(all_topics):
        topic_dir = os.path.join(PLENUM_DIR, topic)

        plenum_file = os.path.join(topic_dir, "_plenum.json")
        qaror_nomi = topic
        if os.path.exists(plenum_file):
            try:
                plenum_data = load_json_file(plenum_file)
                qaror_nomi = plenum_data.get("qaror_nomi", topic)
            except:
                pass

        band_files = glob.glob(os.path.join(topic_dir, "band_*.json"))
        band_files.sort(key=lambda x: int(os.path.basename(x).replace("band_", "").replace(".json", "")))

        if not band_files:
            continue

        all_bands_text = ""
        for band_file in band_files:
            try:
                band_data = load_json_file(band_file)
                band_raqami = band_data.get("band_raqami", "?")
                band_matn = band_data.get("matn", "")
                all_bands_text += f"\nBand {band_raqami}: {band_matn}\n"
            except:
                continue

        if not all_bands_text.strip():
            continue

        prompt = f"""Siz O'zbekiston Oliy Sudining Plenum qarorlari bo'yicha professional huquqshunossiz.

KAZUS:
{KAZUS_MATNI}

PLENUM: {qaror_nomi}

MATN:
{all_bands_text}

VAZIFA: Qaysi bandlar kazusga aloqador?

JAVOBNI JSON FORMATIDA BERING:
{{
  "relevant_bandlar": [
    {{
      "band_raqami": "<raqam>",
      "xatboshi": "<sarlavha>",
      "kazusdagi_holat": "<1 jumla>",
      "qonuniy_asos": "<1 jumla>"
    }}
  ]
}}

Agar aloqador yo'q bo'lsa: {{"relevant_bandlar": []}}"""

        # Plenum uchun alohida model
        reader_model, supports_json = get_model_config(PLENUM_READER_MODEL)
        time.sleep(0.2)

        try:
            kwargs = {
                "model": reader_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "extra_headers": extra_headers,
                "extra_body": {"thinking": {"type": "disabled"}}
            }
            if supports_json:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**kwargs)

            raw_text = response.choices[0].message.content.strip()

            if "<!DOCTYPE" in raw_text or "403" in raw_text:
                print(f"  ⚠️ [{idx+1}/{len(all_topics)}] Cheklov, 5s kutish...")
                time.sleep(5)
                continue

            clean_content = clean_to_json(raw_text)
            res_json = json.loads(clean_content)
            relevant_list = res_json.get("relevant_bandlar", [])

            if relevant_list:
                for item in relevant_list:
                    band_raqami = item.get("band_raqami", "?")
                    band_file = os.path.join(topic_dir, f"band_{band_raqami}.json")
                    band_id = ""
                    if os.path.exists(band_file):
                        try:
                            band_data = load_json_file(band_file)
                            band_id = band_data.get("id", "")
                        except:
                            pass

                    band_url = f"{PLENUM_BASE_URL}#{band_id}" if band_id else PLENUM_BASE_URL

                    COLLECTED_PLENUM.append({
                        "manba": "Plenum",
                        "qaror_nomi": qaror_nomi,
                        "band_raqami": band_raqami,
                        "xatboshi": item.get("xatboshi", ""),
                        "band_url": band_url,
                        "kazusdagi_holat": item.get("kazusdagi_holat", ""),
                        "qonuniy_asos": item.get("qonuniy_asos", "")
                    })

                print(f"  ✅ [{idx+1}/{len(all_topics)}] {topic}: {len(relevant_list)} band")

        except Exception as e:
            print(f"  ❌ [{idx+1}/{len(all_topics)}] {topic}: {e}")

        if (idx + 1) % 5 == 0:
            save_backup()

    print(f"\n   📊 Natija: {len(COLLECTED_PLENUM)} ta band topildi")
    print(f"   Tayyor: {time.strftime('%H:%M:%S')}")


# ============================================================
# 8. YAKUNIY XULOSA — IRAC USULIDA
# ============================================================
def generate_irac():
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

    plenum_text = ""
    for item in COLLECTED_PLENUM:
        plenum_text += f"""
### Plenum: {item.get('qaror_nomi')}
- Band: {item.get('band_raqami')}. {item.get('xatboshi')}
- Kazusdagi holat: {item.get('kazusdagi_holat')}
- Qonuniy asos: {item.get('qonuniy_asos')}
- Havola: {item.get('band_url')}
"""

    final_prompt = f"""Siz O'zbekiston Jinoyat kodeksi, Jinoyat-protsessual kodeksi va Oliy sud Plenum qarorlari bo'yicha professional huquqshunossiz.

KAZUS:
{KAZUS_MATNI}

============================================================
JK TOPILGANLARI:
{jk_text if jk_text else "Topilmadi"}

JPK TOPILGANLARI:
{jpk_text if jpk_text else "Topilmadi"}

PLENUM TOPILGANLARI:
{plenum_text if plenum_text else "Topilmadi"}
============================================================

IRAC USULIDA JAVOB YOZING:

I — ISSUE (Muammo):
4-6 gapda. "Ushbu kazusda quyidagi huquqiy masalalar mavjud..."

R — RULE (Qonun):
JK, JPK moddalarini va Plenum bandlarini keltiring. Havolalar bilan.

A — APPLICATION (Qo'llash):
Kazus faktlarini qonun bilan solishtiring.

C — CONCLUSION (Xulosa):
5-7 gapda. "Yakuniy javob: ..." deb aniq xulosa.

QOIDALAR:
1. Jadval ishlatmang
2. Kamida 600 so'z
3. Barcha havolalarni ko'rsating
4. Professional tilda yozing"""

    try:
        response = client.chat.completions.create(
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
        return f"❌ Xato: {e}"


# ============================================================
# 9. ASOSIY PIPELINE
# ============================================================
def run_pipeline():
    print("=" * 60)
    print("🚀 LexAI v5 — JK + JPK + Plenum (OpenRouter DeepSeek)")
    print("=" * 60)
    print(f"   JK model:      {JK_READER_MODEL}")
    print(f"   JPK model:     {JPK_READER_MODEL}")
    print(f"   Plenum model:  {PLENUM_READER_MODEL}")
    print(f"   Asosiy model:  {MAIN_MODEL}")
    print(f"   Batch: {BATCH_SIZE} ta modda")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}")
    print("=" * 60)

    start_time = time.time()

    scan_jk()
    scan_jpk()
    scan_plenum()

    print(f"\n{'='*60}")
    print("📊 NATIJALAR:")
    print(f"{'='*60}")
    print(f"   JK: {len(COLLECTED_JK)} modda")
    print(f"   JPK: {len(COLLECTED_JPK)} modda")
    print(f"   Plenum: {len(COLLECTED_PLENUM)} band")

    if not COLLECTED_JK and not COLLECTED_JPK and not COLLECTED_PLENUM:
        print("\n⚠️ Aloqador ma'lumot topilmadi.")
        return

    conclusion = generate_irac()

    print(f"\n{'='*60}")
    print("🏆 YAKUNIY XULOSA")
    print(f"{'='*60}")
    print(conclusion)

    with open("lexai_v5_xulosa.txt", "w", encoding="utf-8") as f:
        f.write(conclusion)

    full_data = {
        "kazus": KAZUS_MATNI,
        "jk_moddalar": COLLECTED_JK,
        "jpk_moddalar": COLLECTED_JPK,
        "plenum_bandlari": COLLECTED_PLENUM,
        "xulosa": conclusion
    }
    with open("lexai_v5_full_data.json", "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    jk_batches = (414 + BATCH_SIZE - 1) // BATCH_SIZE
    jpk_batches = (764 + BATCH_SIZE - 1) // BATCH_SIZE
    total_api = jk_batches + jpk_batches + 43 + 1

    print(f"\n{'='*60}")
    print("📊 HISOBOT:")
    print(f"{'='*60}")
    print(f"   JK: ~411 modda → {jk_batches} batch")
    print(f"   JPK: ~764 modda → {jpk_batches} batch")
    print(f"   Plenum: 43 mavzu")
    print(f"   API chaqiruvlar: ~{total_api}")
    print(f"   Vaqt: {mins} daqiqa {secs} soniya")
    print(f"{'='*60}")

    print(f"\n💾 Saqlandi:")
    print(f"   • lexai_v5_xulosa.txt")
    print(f"   • lexai_v5_full_data.json")

    print(f"\n📋 HAVOLALAR:")
    for item in COLLECTED_JK:
        print(f"   • JK {item.get('modda_raqami')}: {item.get('lex_url')}")
    for item in COLLECTED_JPK:
        print(f"   • JPK {item.get('modda_raqami')}: {item.get('lex_url')}")
    for item in COLLECTED_PLENUM:
        print(f"   • Plenum {item.get('band_raqami')}.{item.get('xatboshi')}: {item.get('band_url')}")

    print(f"\n{'='*60}")
    print("✅ TUGADI")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_pipeline()
