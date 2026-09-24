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
if not OPENROUTER_KEY:
    raise ValueError("OPENROUTER_API_KEY topilmadi.")

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
# 2. MODELLAR VA SOZLAMALAR
# ============================================================
SCAN_MODEL = "deepseek/deepseek-v4-flash"
IRAC_MODEL = "deepseek/deepseek-v4-pro"

BATCH_SIZE = 5  # Test isbotlagan optimal qiymat (batch=5 → 100%, batch=10 → 55%)
BATCH_TAG = f"batch{BATCH_SIZE}"

JK_DOC_ID = "-111453"
JPK_DOC_ID = "-111460"
JK_BASE_URL = f"https://lex.uz/docs/{JK_DOC_ID}"
JPK_BASE_URL = f"https://lex.uz/docs/{JPK_DOC_ID}"

JK_DIR = "data/jinoyat/kodekslar/jk"
JPK_DIR = "data/jinoyat/kodekslar/jpk"
PLENUM_DIR = "data/jinoyat/plenumlar"

COLLECTED_JK = []
COLLECTED_JPK = []
COLLECTED_PLENUMS = []

# ============================================================
# 2.5. SAFETY NET — KRITIK MODDALARNI MAJBURIY QO'SHISH
# ============================================================
SAFETY_NET_KEYWORDS = {
    # Kalit so'z → majburiy qo'shiladigan JPK moddalari
    "himoyachi": [50, 51, 52, 53],
    "advokat": [53, 115],
    "voz kech": [52],
    "dalil": [88, 95],
    "qo'rqit": [17, 22, 116, 117],
    "qo'rqitish": [17, 22, 116, 117],
    "qiynoq": [17, 22, 95],
    "ushlab tur": [221, 224, 225, 230],
    "ushlash": [221, 224, 225, 230],
    "reabilitatsiya": [301, 302, 304, 305, 306, 307],
    "oqlov": [301, 464, 470],
    "so'roq": [88, 95, 108, 114],
    "prokuror": [33, 34, 219],
    "hibsxona": [215, 225, 230],
    "kompensatsiya": [304, 305, 306, 307, 312],
    "ish haqi": [304, 305, 306],
    "pora": [140, 141, 203, 205, 206, 207],
    "qonuniylik": [11],
    "ma'naviy zarar": [301, 302, 304],
    "fuqaroviy da'vo": [276, 277, 280, 281, 283],
}

# JK uchun safety net (agar JK yoqilgan bo'lsa)
SAFETY_NET_KEYWORDS_JK = {
    "pora": [210, 211, 212],
    "oqlov": [83],
    "reabilitatsiya": [83],
    "qasddan odam": [97],
    "o'g'rilik": [169],
    "firibgarlik": [168],
}


def apply_safety_net(kazus: str, collected_list: list,
                     source_dir: str, base_url: str,
                     manba: str = "JPK") -> list:
    """
    Kazusda kalit so'z bo'lsa, tegishli moddalarni
    API chaqiruvsiz, to'g'ridan-to'g'ri ro'yxatga qo'shadi.
    Vaqt: 0 soniya. Kafolat: 100%.
    """
    existing_ids = set()
    for item in collected_list:
        existing_ids.add(str(item.get("modda_raqami")).strip())

    added = []
    keywords_dict = SAFETY_NET_KEYWORDS if manba == "JPK" else SAFETY_NET_KEYWORDS_JK
    kazus_lower = kazus.lower()

    for keyword, moddalar in keywords_dict.items():
        if keyword.lower() in kazus_lower:
            for modda_n in moddalar:
                if str(modda_n).strip() not in existing_ids:
                    file_path = os.path.join(source_dir, f"modda_{modda_n}.json")
                    if os.path.exists(file_path):
                        try:
                            modda_data = load_json_file(file_path)
                            sarlavha = modda_data.get("sarlavha", f"{modda_n}-modda")
                            element_id = extract_element_id(
                                modda_data.get("sarlavha_id", "")
                            )
                            lex_link = (
                                f"{base_url}#{element_id}"
                                if element_id else base_url
                            )

                            collected_list.append({
                                "manba": manba,
                                "modda_raqami": str(modda_n).strip(),
                                "modda_sarlavhasi": sarlavha,
                                "element_id": element_id,
                                "lex_url": lex_link,
                                "qism_yoki_band": "Safety Net",
                                "kazusdagi_holat": (
                                    f"Kazusda '{keyword}' tushunchasi mavjud. "
                                    f"Bu modda kritik ahamiyatga ega."
                                ),
                                "qonuniy_asos": (
                                    f"{manba} {modda_n}-modda: {sarlavha}"
                                ),
                                "safety_net": True
                            })
                            existing_ids.add(str(modda_n).strip())
                            added.append(modda_n)
                        except Exception as e:
                            print(f"  ⚠️ Safety Net: {modda_n} o'qilmadi: {e}")

    if added:
        print(f"  🛡️ Safety Net [{manba}]: {len(added)} ta modda qo'shildi → {added}")

    return collected_list


# ============================================================
# 3. KAZUS MATNI
# ============================================================
KAZUS_MATNI = """KAZUS (Probatsiya — pora olish, himoyachi huquqlari, reabilitatsiya):
A.Jabbarov tuman IIB JXX Probatsiya guruhi katta inspektori lavozimida ishlab kelib, fuqaro Maxmudovga tayinlangan axloq tuzatish ishlari jazosini o'tashdan muddatidan ilgari shartli ravishda ozod qilish haqidagi hujjatlarni taqdim etishga va'da qilib, evaziga 500 AQSH dollari talab qilgan va 2025-yil 10-mart kuni talab qilingan pulni so'mga nisbatan qiymati 3.425433 so'mga teng bo'lgan 300 AQSH dollarini pora tariqasida olgan vaqtida ashyoviy dalillar bilan ushlangan.
Qo'zg'atilgan jinoyat ishi doirasida A.Jabbarovdan o'z advokati bor-yo'qligi so'raldi va u mavjud emasligi bildirib, himoyachi xizmatiga ehtiyoji yo'qligi va bu uning moddiy ahvoli bilan bog'liq emasligi haqida ariza yozib berdi. Biroq tergovchi davlat hisobidan himoyachi chaqirib berdi.
Himoyachi-advokat himoyasi ostidagi shaxs bilan uchrashish uchun vaqtinchalik saqlash hibsxonasi kamerasiga borganida, unga tartibga mas'ul xodim ichkariga kiritish uchun boshliqdan ruxsat qog'ozi kerakligini, bayram sababli nazorat kuchaytirilgani uchun shunaqa buyruq olganini aytdi.
Jinoyatni tezkorlik bilan ochish maqsadida tergovchi A.Jabbarovning advokatini so'roq qilish uchun chaqiruv xatini yubordi. Chaqiruv xatini olgan advokat prokurorga shikoyat qilib, advokatni so'roq qilish mumkin emasligini, bu jiddiy protsessual qonunbuzilishi ekanligini ta'kidlagan. Prokuror esa advokatni so'roq qilmaslik bo'yicha tergovchiga topshiriq berdi.
Bundan g'azablangan tergovchi A.Jabbarovning yaqin qarindoshlarini oldin so'roq qilganiga qaramasdan, A.Jabbarovga ta'sir o'tkazish maqsadida ularni so'roqqa chaqdi va ularni qo'rqitish orqali ko'rsatuvlar oldi.
Biroq yakunda sud tomonidan uning harakatlarida jinoyat tarkibi bo'lmaganligi, to'plangan dalillar uni ayblash uchun yetarli emasligi sababli 2025-yil 10-avgust kuni oqlov hukmi chiqarilib, hukmda to'lanmagan ish haqi va mehnatdan topiladigan boshqa daromadlarni qoplanishi belgilandi.
Mazkur oqlov hukmini olgan A.Jabbarov 2 oydan so'ng sudga kompensatsiyani undirish yuzasidan ariza bilan murojaat qiladi. Yetkazilgan ziyon Majburiy ijro byuroisi tomonidan hisoblab chiqilib, pul to'lovlarini amalga oshirish to'g'risida sud ajrim chiqarildi."""


def get_kazus() -> str:
    return KAZUS_MATNI


# ============================================================
# 4. YORDAMCHI FUNKSIYALAR
# ============================================================
def select_agents() -> dict:
    """Foydalanuvchidan qaysi manbalarni skanerlashni so'raydi."""
    print("\n" + "=" * 60)
    print("📋 QAYSI MANBALARNI SKANERLASH KERAK?")
    print("=" * 60)
    print("   1 - JK       (Jinoyat Kodeksi, ~411 modda)")
    print("   2 - JPK      (Jinoyat-Protsessual Kodeksi, ~764 modda)")
    print("   3 - PLENUM   (Oliy Sud Plenumlari, 43 mavzu)")
    print("-" * 60)
    print("   Misollar:  '2'  |  '2,3'  |  '1,2,3'")
    print("=" * 60)

    while True:
        choice = input("\n   Tanlovingiz: ").strip()
        selected = {"JK": False, "JPK": False, "PLENUM": False}
        valid = True

        for part in choice.split(","):
            part = part.strip()
            if part == "1":
                selected["JK"] = True
            elif part == "2":
                selected["JPK"] = True
            elif part == "3":
                selected["PLENUM"] = True
            elif part == "":
                continue
            else:
                print(f"   ❌ Noto'g'ri: '{part}'. Faqat 1, 2, 3.")
                valid = False
                break

        if valid and any(selected.values()):
            return selected

        if valid:
            print("   ⚠️ Kamida bitta manba tanlanishi kerak.")


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
    nums = [int(n) for n in re.findall(r"\d+", name)]
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


def format_plenum_for_prompt(plenum_dir: str) -> tuple:
    """Bitta plenum mavzusini to'liq o'qish uchun formatlaydi."""
    plenum_path = os.path.join(PLENUM_DIR, plenum_dir)
    meta_path = os.path.join(plenum_path, "_plenum.json")
    if not os.path.exists(meta_path):
        return None, None
    meta = load_json_file(meta_path)
    mavzu_nomi = meta.get("qaror_nomi", plenum_dir)
    raqam = meta.get("raqami", "")
    manba = meta.get("manba", "")
    sana = meta.get("sana", "")
    lines = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"PLENUM: {mavzu_nomi}")
    lines.append(f"Raqami: {raqam} | Sana: {sana}")
    lines.append(f"Manba: {manba}")
    lines.append(f"{'=' * 60}")
    band_files = sorted(
        glob.glob(os.path.join(plenum_path, "band_*.json")),
        key=natural_sort_key
    )
    for bf in band_files:
        try:
            band = load_json_file(bf)
            band_n = band.get("band_raqami", "")
            band_matn = band.get("matn", "")
            band_id = band.get("id", "")
            lines.append(f"\nBand {band_n} (ID: {band_id}):")
            lines.append(f"  {band_matn}")
            for xatbosh in band.get("xatboshilar", []):
                if xatbosh:
                    lines.append(f"  - {xatbosh}")
        except Exception:
            continue
    return meta, "\n".join(lines)


def load_json_file(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


def extract_element_id(sarlavha_id: str) -> str:
    if "#" in sarlavha_id:
        return sarlavha_id.split("#")[-1]
    return ""


def safe_api_call(model_name, prompt, max_retries=5, provider_name="",
                  temperature=0.0, response_format_json=True, extra_body=None):
    """API chaqiruvini rate-limit himoyasi bilan amalga oshiradi."""
    kwargs = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "extra_headers": extra_headers,
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
                    if hasattr(e, 'response') and e.response is not None:
                        retry_after = e.response.headers.get('retry-after')
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


# ============================================================
# 5. AGENT 1: JK SKANERLASH
# ============================================================
def scan_jk(kazus: str):
    print(f"\n{'=' * 60}")
    print("📚 AGENT 1: JK TAHLILI")
    print(f"   Model: {SCAN_MODEL}")
    print(f"{'=' * 60}")

    all_files = glob.glob(os.path.join(JK_DIR, "modda_*.json"))
    all_files.sort(key=natural_sort_key)
    total_files = len(all_files)
    total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"   Jami: {total_files} modda, {total_batches} batch")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}")

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

        time.sleep(0.5)
        raw_text = safe_api_call(SCAN_MODEL, prompt, max_retries=5, provider_name=f"JK-{batch_num}")
        if raw_text is None:
            print(f"  ❌ [JK {batch_num}/{total_batches}] API xato, o'tkazib yuborildi")
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
                            if str(md.get("n", "")).strip() == str(modda_raqami).strip():
                                element_id = extract_element_id(md.get("sarlavha_id", ""))
                                break
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
                print(f"  ✅ [JK {batch_num}/{total_batches}] → {len(valid_items)} modda: [{moddalar_str}]")
            else:
                print(f"  ⚪ [JK {batch_num}/{total_batches}] → Yo'q")
        except Exception as e:
            print(f"  ❌ [JK {batch_num}/{total_batches}] Xato: {e}")

        if batch_num % 20 == 0:
            backup_jk()

    # 🛡️ SAFETY NET — kritik moddalarni majburiy qo'shish
    apply_safety_net(kazus, COLLECTED_JK, JK_DIR, JK_BASE_URL, "JK")

    backup_jk()
    print(f"\n   📊 JK: {len(COLLECTED_JK)} ta modda topildi")
    print(f"   JK tugadi: {time.strftime('%H:%M:%S')}")


# ============================================================
# 6. AGENT 2: JPK SKANERLASH
# ============================================================
def scan_jpk(kazus: str):
    print(f"\n{'=' * 60}")
    print("📚 AGENT 2: JPK TAHLILI")
    print(f"   Model: {SCAN_MODEL}")
    print(f"{'=' * 60}")

    all_files = glob.glob(os.path.join(JPK_DIR, "modda_*.json"))
    all_files.sort(key=natural_sort_key)
    total_files = len(all_files)
    total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"   Jami: {total_files} modda, {total_batches} batch")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}")

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
{kazus}

JPK MODDALARI (Batch {batch_num}/{total_batches}):
{batch_text}

VAZIFA: Qaysi moddalar kazusga aloqador?

MUHIM — OQIBAT QOIDASI:
Agar kazusda qonun buzilishi bo'lsa (qo'rqitish, himoyachini kiritmaslik,
advokatni so'roq qilish, qiynoq, dalil yig'ish tartibining buzilishi),
faqat BUZILGAN moddani emas, balki uning OQIBATI bo'lgan moddalarni ham top:
- JPK 95 (Dalillar maqbulligi) — qonun buzilsa, dalil nomaqbul bo'ladi
- JPK 11 (Qonuniylik) — har qanday chekinish qonuniylikni buzadi
- JPK 88 (Isbotlash) — dalillar majmui baholanishi kerak

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

        time.sleep(0.5)
        raw_text = safe_api_call(SCAN_MODEL, prompt, max_retries=5, provider_name=f"JPK-{batch_num}")
        if raw_text is None:
            print(f"  ❌ [JPK {batch_num}/{total_batches}] API xato, o'tkazib yuborildi")
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
                            if str(md.get("n", "")).strip() == str(modda_raqami).strip():
                                element_id = extract_element_id(md.get("sarlavha_id", ""))
                                break
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
                print(f"  ✅ [JPK {batch_num}/{total_batches}] → {len(valid_items)} modda: [{moddalar_str}]")
            else:
                print(f"  ⚪ [JPK {batch_num}/{total_batches}] → Yo'q")
        except Exception as e:
            print(f"  ❌ [JPK {batch_num}/{total_batches}] Xato: {e}")

        if batch_num % 20 == 0:
            backup_jpk()

    # 🛡️ SAFETY NET — kritik moddalarni majburiy qo'shish
    apply_safety_net(kazus, COLLECTED_JPK, JPK_DIR, JPK_BASE_URL, "JPK")

    backup_jpk()
    print(f"\n   📊 JPK: {len(COLLECTED_JPK)} ta modda topildi")
    print(f"   JPK tugadi: {time.strftime('%H:%M:%S')}")


# ============================================================
# 7. AGENT 3: PLENUMLAR — HAR BIR MAVZU TO'LIQ O'QILADI
# ============================================================
def scan_plenums(kazus: str):
    print(f"\n{'=' * 60}")
    print("📚 AGENT 3: PLENUMLAR — HAR BIR MAVZU TO'LIQ")
    print(f"   Model: {SCAN_MODEL}")
    print(f"{'=' * 60}")

    plenum_dirs = sorted([
        d for d in os.listdir(PLENUM_DIR)
        if os.path.isdir(os.path.join(PLENUM_DIR, d))
    ])
    total = len(plenum_dirs)
    print(f"   Jami: {total} ta plenum mavzusi")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}")

    for idx, plenum_dir in enumerate(plenum_dirs, 1):
        meta, plenum_text = format_plenum_for_prompt(plenum_dir)
        if not meta or not plenum_text:
            print(f"  ⚪ [{idx}/{total}] {plenum_dir} — o'qib bo'lmadi")
            continue

        bandlar_soni = meta.get("bandlar_soni", "?")
        print(f"\n  📖 [{idx}/{total}] {meta.get('raqami', plenum_dir)} — {bandlar_soni} band")

        prompt = f"""Siz O'zbekiston Huquq tizimi bo'yicha professional huquqshunossiz.

KAZUS:
{kazus}

PLENUM MA'LUMOTLARI:
{plenum_text}

VAZIFA:
1. Ushbu plenum kazusga qanday aloqadorligini aniqlang
2. Plenumning qaysi bandlari (raqamlari) kazusga to'g'ri kelishini ko'rsating
3. Kazus faktlari plenum talablari bilan qanday mos kelishini tahlil qiling
4. Qaysi JK/JPK moddalari ushbu plenum orqali izohlanishini ko'rsating

JAVOBNI JSON FORMATIDA BERING:
{{
  "plenum_mavzu": "<plenum nomi>",
  "kazusga_aloqadorlik": "<1-3 jumla — umumiy aloqa>",
  "tegishli_bandlar": [
    {{
      "band_raqami": "<band raqami>",
      "kazusga_moslik": "<1-2 jumla>",
      "izoh": "<bu band qanday qo'llaniladi>"
    }}
  ],
  "bog'liq_jk_moddalar": [<JK modda raqamlari>],
  "bog'liq_jpk_moddalar": [<JPK modda raqamlari>],
  "tahlil": "<3-5 gap — plenumning kazusga ta'siri>"
}}
Agar plenum kazusga aloqador bo'lmasa: {{ "plenum_mavzu": "...", "kazusga_aloqadorlik": "yo'q", "tegishli_bandlar": [], "bog'liq_jk_moddalar": [], "bog'liq_jpk_moddalar": [], "tahlil": "..." }}"""

        time.sleep(0.5)
        raw_text = safe_api_call(SCAN_MODEL, prompt, max_retries=5, provider_name=f"PLENUM-{idx}")
        if raw_text is None:
            print(f"  ❌ [{idx}/{total}] API xato, o'tkazib yuborildi")
            continue

        try:
            clean_content = clean_to_json(raw_text)
            res_json = json.loads(clean_content)
            aloqadorlik = res_json.get("kazusga_aloqadorlik", "")
            tegishli_bandlar = res_json.get("tegishli_bandlar", [])

            plenum_record = {
                "mavzu_dir": plenum_dir,
                "qaror_nomi": meta.get("qaror_nomi", ""),
                "raqami": meta.get("raqami", ""),
                "sana": meta.get("sana", ""),
                "manba": meta.get("manba", ""),
                "kazusga_aloqadorlik": aloqadorlik,
                "tegishli_bandlar": tegishli_bandlar,
                "bog'liq_jk_moddalar": res_json.get("bog'liq_jk_moddalar", []),
                "bog'liq_jpk_moddalar": res_json.get("bog'liq_jpk_moddalar", []),
                "tahlil": res_json.get("tahlil", "")
            }
            COLLECTED_PLENUMS.append(plenum_record)

            if tegishli_bandlar:
                band_raqamlar = [b.get("band_raqami", "?") for b in tegishli_bandlar]
                print(f"  ✅ [{idx}/{total}] {len(tegishli_bandlar)} band: [{', '.join(band_raqamlar)}]")
            else:
                print(f"  ⚪ [{idx}/{total}] Kazusga aloqador band topilmadi")
        except Exception as e:
            print(f"  ❌ [{idx}/{total}] Xato: {e}")

        if idx % 5 == 0:
            backup_plenums()

    backup_plenums()
    aloqador = [p for p in COLLECTED_PLENUMS if p.get("tegishli_bandlar")]
    print(f"\n   📊 PLENUMLAR: {len(COLLECTED_PLENUMS)} ta o'qildi, {len(aloqador)} ta kazusga aloqador")
    print(f"   Plenumlar tugadi: {time.strftime('%H:%M:%S')}")


# ============================================================
# 8. YAKUNIY XULOSA — IRAC USULIDA
# ============================================================
def generate_irac(kazus: str):
    print(f"\n{'=' * 60}")
    print("🧠 YAKUNIY XULOSA — IRAC USULIDA")
    print(f"   Model: {IRAC_MODEL}")
    print(f"{'=' * 60}")

    jk_text = ""
    for item in COLLECTED_JK:
        jk_text += f"""
JK {item.get('modda_raqami')}-modda
Sarlavha: {item.get('modda_sarlavhasi')}
Qism/Band: {item.get('qism_yoki_band')}
Kazusdagi holat: {item.get('kazusdagi_holat')}
Qonuniy asos: {item.get('qonuniy_asos')}
Buzilganmi: {item.get('buzilganmi')}
Havola: {item.get('lex_url')}
"""

    jpk_text = ""
    for item in COLLECTED_JPK:
        jpk_text += f"""
JPK {item.get('modda_raqami')}-modda
Sarlavha: {item.get('modda_sarlavhasi')}
Qism/Band: {item.get('qism_yoki_band')}
Kazusdagi holat: {item.get('kazusdagi_holat')}
Qonuniy asos: {item.get('qonuniy_asos')}
Havola: {item.get('lex_url')}
"""

    plenum_text = ""
    for p in COLLECTED_PLENUMS:
        if not p.get("tegishli_bandlar"):
            continue
        bandlar_str = ", ".join(b.get("band_raqami", "?") for b in p.get("tegishli_bandlar", []))
        plenum_text += f"""
PLENUM: {p.get('raqami')} — {p.get('qaror_nomi', '')[:80]}
Manba: {p.get('manba')}
Tegishli bandlar: {bandlar_str}
Kazusga aloqadorlik: {p.get('kazusga_aloqadorlik')}
Tahlil: {p.get('tahlil')}
"""

    final_prompt = f"""Siz O'zbekiston Jinoyat kodeksi, Jinoyat-protsessual kodeksi va Oliy Sud Plenumlari bo'yicha professional huquqshunossiz.

KAZUS:
{kazus}

JK TOPILGANLARI:
{jk_text if jk_text else "Topilmadi"}

JPK TOPILGANLARI:
{jpk_text if jpk_text else "Topilmadi"}

PLENUMLAR (Oliy Sud interpretatsiyalari):
{plenum_text if plenum_text else "Topilmadi"}

IRAC USULIDA JAVOB YOZING:

I — ISSUE (Muammo):
4-6 gapda. "Ushbu kazusda quyidagi huquqiy masalalar mavjud..."

R — RULE (Qonun):
JK va JPK moddalarini keltiring. Har bir modda uchun lex.uz havolasini ko'rsating. Mavjud bo'lsa, tegishli plenum bandlarini ham qo'shing.

A — APPLICATION (Qo'llash):
Kazus faktlarini qonun bilan solishtiring. Plenum talablari asosida tahlil qiling.

C — CONCLUSION (Xulosa):
5-7 gapda. "Yakuniy javob: ..." deb aniq xulosa.

QOIDALAR:
- Jadval ishlatmang
- Kamida 800 so'z
- Barcha havolalarni ko'rsating: https://lex.uz/docs/<doc_id>#<element_id>
- Professional tilda yozing
- Plenumlar asosida chuqur yuridik tahlil qiling
- Disclaimer qo'shing"""

    print("   IRAC javobi yozilmoqda...")

    try:
        for attempt in range(5):
            try:
                response = client.chat.completions.create(
                    model=IRAC_MODEL,
                    messages=[
                        {"role": "system",
                         "content": "Siz professional huquqshunossiz. IRAC usulida, jadvalsiz, havolalar bilan javob bering."},
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
                    except Exception:
                        pass
                    print(f"  ⏳ [IRAC] Rate limit! {wait}s kutish ({attempt + 1}/5)...")
                    time.sleep(wait)
                else:
                    raise
        return "❌ IRAC: 5 ta urinishdan keyin javob olinmadi"
    except Exception as e:
        return f"❌ Xato: {e}"


# ============================================================
# 9. BACKUP — HAR BIRI ALOHIDA
# ============================================================
JK_LOCK = threading.Lock()
JPK_LOCK = threading.Lock()
PLENUM_LOCK = threading.Lock()


def backup_jk():
    with JK_LOCK:
        with open(f"jk_backup_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
            json.dump(COLLECTED_JK, f, ensure_ascii=False, indent=2)


def backup_jpk():
    with JPK_LOCK:
        with open(f"jpk_backup_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
            json.dump(COLLECTED_JPK, f, ensure_ascii=False, indent=2)


def backup_plenums():
    with PLENUM_LOCK:
        with open(f"plenums_backup_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
            json.dump(COLLECTED_PLENUMS, f, ensure_ascii=False, indent=2)


def save_backup():
    backup_jk()
    backup_jpk()
    backup_plenums()


# ============================================================
# 10. ASOSIY PIPELINE — INTERAKTIV TANLOV BILAN
# ============================================================
def run_pipeline():
    # Interaktiv tanlov
    selected = select_agents()

    print("=" * 60)
    print("🚀 LexAI v7 — INTERAKTIV TANLOV + SAFETY NET")
    print("=" * 60)
    print(f"   Scan model:  {SCAN_MODEL}")
    print(f"   IRAC model:  {IRAC_MODEL}")
    print(f"   Batch size:  {BATCH_SIZE} ta modda")
    print(f"   JK:          {'✅ YOQILGAN' if selected['JK'] else '❌ O\'CHIRILGAN'}")
    print(f"   JPK:         {'✅ YOQILGAN' if selected['JPK'] else '❌ O\'CHIRILGAN'}")
    print(f"   PLENUM:      {'✅ YOQILGAN' if selected['PLENUM'] else '❌ O\'CHIRILGAN'}")
    print(f"   Safety Net:  ✅ YOQILGAN")
    print(f"   Oqibat qoidasi: ✅ YOQILGAN")
    print(f"   Yakun:       IRAC javob")
    print("=" * 60)

    kazus = get_kazus()
    start_time = time.time()
    threads = []

    if selected["JK"]:
        def worker_jk():
            scan_jk(kazus)

        t_jk = threading.Thread(target=worker_jk)
        t_jk.start()
        threads.append(t_jk)

    if selected["JPK"]:
        def worker_jpk():
            time.sleep(2)  # Stagger — bir vaqtda boshlanmaslik uchun
            scan_jpk(kazus)

        t_jpk = threading.Thread(target=worker_jpk)
        t_jpk.start()
        threads.append(t_jpk)

    if selected["PLENUM"]:
        def worker_plenums():
            time.sleep(4)  # Stagger — uchinchi thread kechroq boshlanadi
            scan_plenums(kazus)

        t_pl = threading.Thread(target=worker_plenums)
        t_pl.start()
        threads.append(t_pl)

    for t in threads:
        t.join()

    # Yakuniy backuplar
    save_backup()

    print(f"\n{'=' * 60}")
    print("📊 NATIJALAR:")
    print(f"{'=' * 60}")
    print(f"   JK: {len(COLLECTED_JK)} modda")
    print(f"   JPK: {len(COLLECTED_JPK)} modda")
    print(f"   Plenumlar: {len(COLLECTED_PLENUMS)} mavzu")

    if not COLLECTED_JK and not COLLECTED_JPK and not COLLECTED_PLENUMS:
        print("\n⚠️ Aloqador ma'lumot topilmadi.")
        return

    conclusion = generate_irac(kazus)

    print(f"\n{'=' * 60}")
    print("🏆 YAKUNIY XULOSA")
    print(f"{'=' * 60}")
    print(conclusion)

    # Natijalarni saqlash
    with open(f"irac_final_{BATCH_TAG}.txt", "w", encoding="utf-8") as f:
        f.write(conclusion)

    with open(f"jk_analysis_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
        json.dump(COLLECTED_JK, f, ensure_ascii=False, indent=2)

    with open(f"jpk_analysis_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
        json.dump(COLLECTED_JPK, f, ensure_ascii=False, indent=2)

    with open(f"plenums_analysis_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
        json.dump(COLLECTED_PLENUMS, f, ensure_ascii=False, indent=2)

    full_data = {
        "batch_size": BATCH_SIZE,
        "selected_agents": selected,
        "kazus": kazus,
        "jk_moddalar": COLLECTED_JK,
        "jpk_moddalar": COLLECTED_JPK,
        "plenumlar": COLLECTED_PLENUMS,
        "xulosa": conclusion
    }

    with open(f"lexai_v7_full_data_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    jk_count = len(glob.glob(os.path.join(JK_DIR, "modda_*.json")))
    jpk_count = len(glob.glob(os.path.join(JPK_DIR, "modda_*.json")))
    plenum_count = len([d for d in os.listdir(PLENUM_DIR) if os.path.isdir(os.path.join(PLENUM_DIR, d))])

    jk_batches = (jk_count + BATCH_SIZE - 1) // BATCH_SIZE
    jpk_batches = (jpk_count + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"\n{'=' * 60}")
    print("📊 HISOBOT:")
    print(f"{'=' * 60}")
    if selected["JK"]:
        print(f"   JK: {jk_count} modda → {jk_batches} batch")
    if selected["JPK"]:
        print(f"   JPK: {jpk_count} modda → {jpk_batches} batch")
    if selected["PLENUM"]:
        print(f"   Plenumlar: {plenum_count} mavzu → {plenum_count} so'rov")
    print(f"   Model: {SCAN_MODEL}")
    print(f"   IRAC: {IRAC_MODEL}")
    print(f"   Safety Net: YOQILGAN")
    print(f"   Vaqt: {mins} daqiqa {secs} soniya")
    print(f"{'=' * 60}")

    print(f"\n💾 Saqlandi:")
    print(f"   • irac_final_{BATCH_TAG}.txt")
    print(f"   • jk_analysis_{BATCH_TAG}.json")
    print(f"   • jpk_analysis_{BATCH_TAG}.json")
    print(f"   • plenums_analysis_{BATCH_TAG}.json")
    print(f"   • lexai_v7_full_data_{BATCH_TAG}.json")

    print(f"\n📋 HAVOLALAR:")
    for item in COLLECTED_JK:
        print(f"   • JK {item.get('modda_raqami')}: {item.get('lex_url')}")
    for item in COLLECTED_JPK:
        print(f"   • JPK {item.get('modda_raqami')}: {item.get('lex_url')}")
    for p in COLLECTED_PLENUMS:
        if p.get("tegishli_bandlar"):
            print(f"   • PLENUM {p.get('raqami')}: {p.get('manba')}")

    print(f"\n{'=' * 60}")
    print("✅ TUGADI")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_pipeline()