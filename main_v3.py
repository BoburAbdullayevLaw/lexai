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
    raise ValueError("DEEPSEEK_API_KEY topilmadi. .env faylini tekshiring.")

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
MODEL_PRO   = "deepseek-v4-pro"

JPK_DOC_ID   = "-111460"
BASE_LEX_URL = f"https://lex.uz/docs/{JPK_DOC_ID}"

DATA_DIR            = "data/jpk_boblar"
COLLECTED_ARTICLES  = []

# ============================================================
# 3. KAZUS MATNI
# ============================================================
KAZUS_MATNI = """KAZUS Jinoyat protsesida dalillar va isbotlash modulidan.
Voyaga yetmagan shaxslar oʻrtasida kelib chiqqan oʻzaro janjal natijasida 2025-yil 10-yanvar kuni taxminan soat 12:30 larda voyaga yetmagan 16 yoshli Anvar ismli shaxs janjal davomida yonida boʻlgan pichoq bilan Bobur ismli shaxsning chap qorin qismiga bir marotaba urib, tan jarohati yetkazgan.

Voqea joyi koʻzdan kechirilganda voqea joyidan qonga oʻxshash qizgʻish dogʻlari boʻlgan pichoq, oq rangdagi mato parchalari, bir dona charm oyoq kiyim topildi hamda ashyoviy dalil sifatida ish materiallariga qoʻshib qoʻyildi. Ushbu narsalar voqea joyini koʻzdan kechirish bayonnomasiga kiritilmadi.

Sudga oid tibbiy ekspertizaning xulosasiga koʻra Bobur ismli shaxsga qorin devori chap yon sohasidan qorin boʻshligʻiga teshib oʻtuvchi, sanchib kesilgan jarohat, qorin boʻshligʻiga ichki qon kelishi” kabi sogʻligʻini buzilishiga olib kelgan ogʻir shikast yetkazilgani aniqlangan. Biroq, tergovchi ekspert xulosasiga qoʻshilmagan.

Tergov materiallariga koʻra, Anvar ismli shaxs Bobur ismli shaxsga nisbatan shaxsiy adovati boʻlgan. Anvar ismli shaxs bu mojaroni oʻzaro janjal bilan hal qilinishi mumkinligiga qaror qilgan. Dastlabki tergov jarayonida Anvar ismli shaxs oʻz aybini toʻliq tan olib, oʻzining harakatlari va ish holatlari haqida aniq koʻrsatma beradi.

Sud muhokamasida Anvar ismli shaxs oʻzining koʻrsatuvlarini oʻzgartirib, aybni tan olmagan, yaʼni u oʻzining aybdor emasligini, dastlabki tergov jarayonida tergovchi ishni tugatishga vaʼda berib, unga aybni tan olishga va chin koʻngildan pushaymon boʻlishga majburlab, qanday koʻrsatma berish kerakligini oʻrgatganini bildiradi.

Sud jarayonida jabrlanuvchi ham guvohlik berishdan bosh tortgan. Ikki nafar guvohlarning koʻrsatuvlari esa qarama-qarshi boʻlib, tortishuvlarga sabab boʻlgan.

"""


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
    if COLLECTED_ARTICLES:
        with open("lexai_v3_backup.json", "w", encoding="utf-8") as f:
            json.dump(COLLECTED_ARTICLES, f, ensure_ascii=False, indent=2)
        print("📦 Oraliq natijalar 'lexai_v3_backup.json' fayliga saqlandi.")


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


# ============================================================
# 5. ASOSIY PIPELINE
# ============================================================
def run_pipeline():
    global COLLECTED_ARTICLES

    all_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    all_files.sort(key=natural_sort_key)

    print(f"🚀 LexAI v3 — IRAC usulida professional tahlil")
    print(f"   Model: {MODEL_FLASH}  |  Jami boblar: {len(all_files)}\n")

    for idx, file_path in enumerate(all_files):
        filename = os.path.basename(file_path)

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                bob_data = json.load(f)
        except Exception as e:
            print(f"[{idx+1}/{len(all_files)}] 📁 Nuqsonli JSON [{filename}]: {e}")
            continue

        bob_nomi = bob_data.get("bob_nomi", filename)
        bob_raqami = bob_data.get("bob_raqami", "?")
        moddalar = bob_data.get("moddalar", [])

        if not moddalar:
            print(f"[{idx+1}/{len(all_files)}] ⚪ {bob_nomi} — modda yo'q, o'tkazildi.")
            continue

        formatted_bob = format_bob_for_prompt(bob_data)

        prompt = f"""KAZUS MATNI:
{KAZUS_MATNI}

JPK BOB STRUKTURASI:
{formatted_bob}

VAZIFA:
Ushbu bobdagi qaysi MODDALAR (yoki ularning qismlari/bandlari) kazusga bevosita ALOQADOR?

QOIDALAR:
1. Faqat haqiqatan aloqador bo'lgan moddalarni ko'rsating.
2. Agar aloqador modda bo'lmasa — bo'sh massiv qaytaring.
3. Faqat quyidagi JSON formatida javob bering.

ELEMENT_ID: FAQAT [ID:...] dan raqamni oling. Masalan: [ID:-2460781] → "-2460781"

{{
  "relevant_moddalar": [
    {{
      "modda_raqami": <int>,
      "modda_sarlavhasi": "<sarlavha>",
      "element_id": "<raqamli ID>",
      "qism_yoki_band": "<masalan: 2-qism>",
      "kazusdagi_holat": "<kazusdagi aniq vaziyat, 1 jumla>",
      "qonuniy_asos": "<modda nimani talab qiladi/taqiqlaydi, 1 jumla>",
      "buzilganmi": true/false
    }}
  ]
}}"""

        time.sleep(0.15)

        try:
            response = client.chat.completions.create(
                model=MODEL_FLASH,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                temperature=0.0,
                extra_headers=extra_headers,
                extra_body={"thinking": {"type": "disabled"}},
                response_format={"type": "json_object"}
            )

            raw_text = response.choices[0].message.content.strip()

            if "<!DOCTYPE" in raw_text or "403 Forbidden" in raw_text:
                print(f"[{idx+1}/{len(all_files)}] ⚠️ {bob_nomi} — tarmoq cheklovi, 5s...")
                time.sleep(5)
                continue

            clean_content = clean_to_json(raw_text)
            res_json = json.loads(clean_content)
            relevant_list = res_json.get("relevant_moddalar", [])

            if relevant_list:
                for item in relevant_list:
                    element_id = item.get("element_id", "")
                    lex_link = f"{BASE_LEX_URL}#{element_id}" if element_id else BASE_LEX_URL

                    COLLECTED_ARTICLES.append({
                        "bob_raqami": bob_raqami,
                        "bob_nomi": bob_nomi,
                        "modda_raqami": item.get("modda_raqami"),
                        "modda_sarlavhasi": item.get("modda_sarlavhasi"),
                        "element_id": element_id,
                        "qism_yoki_band": item.get("qism_yoki_band", ""),
                        "lex_url": lex_link,
                        "kazusdagi_holat": item.get("kazusdagi_holat", ""),
                        "qonuniy_asos": item.get("qonuniy_asos", ""),
                        "buzilganmi": item.get("buzilganmi", True),
                    })

                moddalar_str = ", ".join(str(m.get("modda_raqami")) for m in relevant_list)
                print(f"[{idx+1}/{len(all_files)}] ✅ {bob_nomi} → {len(relevant_list)} ta modda: [{moddalar_str}]")
            else:
                print(f"[{idx+1}/{len(all_files)}] ⚪ {bob_nomi} → Tegishli modda yo'q.")

        except Exception as e:
            print(f"[{idx+1}/{len(all_files)}] ❌ {filename}: {e}")

        if (idx + 1) % 10 == 0:
            save_backup_results()

    # ============================================================
    # 6. YAKUNIY SINTEZ — IRAC USULIDA
    # ============================================================
    print(f"\n📊 Skanerlash yakunlandi. Jami {len(COLLECTED_ARTICLES)} ta aloqador element topildi.")

    if not COLLECTED_ARTICLES:
        print("⚠️ Hech qanday aloqador modda topilmadi.")
        return

    print(f"\n🧠 Yakuniy xulosa shakllantirilmoqda ({MODEL_PRO})...")
    print("   IRAC usulida, jadvalsiz, professional formatda...\n")
    time.sleep(2)

    # ============================================================
    # MUHIM: IRAC USULIDA YOZILGAN NAMUNA JAVOB
    # ============================================================
    IRAC_MISOL_JAVOB = """
I — ISSUE (Muammo)

Ushbu kazusda quyidagi huquqiy masalalar mavjud. Birinchidan, voqea joyidan topilgan ashyoviy dalillar (pichoq, mato parchalari, oyoq kiyim) tegishli bayonnoma bilan rasmiylashtirilmagan. Bu dalillar qonuniy kuchga egami yoki ular nomaqbul dalil hisoblanadimi? Ikkinchidan, tergovchi sud-tibbiy ekspertizasining og'ir shikast yetkazilganligi haqidagi xulosasiga qo'shilmagan, ammo qayta ekspertiza tayinlamagan va rad etish sabablarini asoslamagan. Uchinchidan, 16 yoshli voyaga yetmagan Anvar himoyachisiz so'roq qilingan va tergovchi tomonidan "ishni tugatish" va'dasi bilan aldash hamda majburlash yo'li bilan ko'rsatuv olingan. To'rtinchidan, jabrlanuvchi guvohlik berishdan bosh tortgan va ikki guvohning ko'rsatuvlari qarama-qarshi bo'lgan.

R — RULE (Qonun qoidasi)

JPKning 90-moddasiga ko'ra, dalillar qonunda belgilangan tartibda olingan bo'lishi shart. JPKning 163-moddasiga binoan, olib qo'yish natijalari bo'yicha albatta bayonnoma tuzilishi kerak. JPKning 95-moddasiga muvofiq, qonunga xilof usulda olingan dalillar nomaqbul hisoblanadi va isbot vositasi sifatida foydalanilishi mumkin emas.

JPKning 176-moddasiga ko'ra, tergovchi ekspert xulosasiga qo'shilmasa, qayta ekspertiza tayinlashi shart. JPKning 187-moddasiga binoan, ekspert xulosasiga qo'shilmaslik qarorda asoslanishi kerak.

JPKning 51-moddasiga binoan, voyaga yetmaganlarning ishida himoyachi ishtiroki majburiydir. JPKning 52-moddasining ikkinchi qismiga ko'ra, voyaga yetmagan himoyachidan voz kecha olmaydi. JPKning 22-moddasiga ko'ra, gumon qilinuvchidan zo'rlash, qo'rqitish, aldash yoki boshqa qonunga xilof choralar bilan ko'rsatuvlar olish qat'iyan man etiladi. JPKning 88-moddasining ikkinchi qismi ikkinchi bandida ham aldash va qonunga xilof usullar bilan ko'rsatuv olish taqiqlangan.

JPKning 66-moddasiga ko'ra, guvoh va jabrlanuvchi ish bo'yicha o'ziga ma'lum bo'lgan barcha ma'lumotlarni so'zlab berishi shart. JPKning 122-moddasiga binoan, qarama-qarshi ko'rsatuvlar bo'lganda yuzlashtirish o'tkazilishi kerak.

A — APPLICATION (Qonunni kazusga qo'llash)

Birinchi masala bo'yicha, kazusda voqea joyidan pichoq, mato parchalari va oyoq kiyim topilgan. Ushbu narsalar ashyoviy dalil sifatida ish materiallariga qo'shilgan, biroq voqea joyini ko'zdan kechirish bayonnomasiga kiritilmagan. JPK 163-modda talabiga ko'ra, bayonnoma tuzilmagan taqdirda, bu narsalar qonunda belgilangan tartibda olingan deb hisoblanmaydi. Shuning uchun JPK 90 va 95-moddalariga asosan ular nomaqbul dalil hisoblanadi va ishdan chiqarilishi kerak.

Ikkinchi masala bo'yicha, sud-tibbiy ekspertizasi Boburga og'ir shikast yetkazilganligini aniqlagan. Tergovchi bu xulosaga qo'shilmagan, ammo JPK 176-moddasiga ko'ra qayta ekspertiza tayinlamagan va JPK 187-moddasiga ko'ra rad etish sabablarini asoslamagan. Tergovchi maxsus tibbiy bilimga ega emas. Shuning uchun uning ekspert xulosasini asossiz rad etishi qonunga ziddir.

Uchinchi masala bo'yicha, Anvar 16 yoshli voyaga yetmagan shaxs. JPK 51-moddasiga ko'ra, unga himoyachi tayinlanishi majburiy edi. Kazusda himoyachisiz so'roq qilingan. Tergovchi unga "ishni tugatish" haqida va'da berib aldagan va qanday ko'rsatma berishni o'rgatgan. Bu JPK 22 va 88-moddalarining buzilishidir. Anvar sudda aybni tan olmagan va majburlanganini aytgan.

To'rtinchi masala bo'yicha, jabrlanuvchi Bobur guvohlik berishdan bosh tortgan, ammo JPK 66-moddasiga ko'ra u javobgarlikka tortilmagan. Ikki guvohning qarama-qarshi ko'rsatuvlari bo'yicha esa JPK 122-moddasiga ko'ra yuzlashtirish o'tkazilmagan.

C — CONCLUSION (Xulosa)

Yuqoridagi tahlillardan kelib chiqib, quyidagi xulosalarga kelaman. Birinchidan, ashyoviy dalillar (pichoq, mato, oyoq kiyim) nomaqbul hisoblanadi va ishdan chiqarilishi kerak. Ularga asoslanib ayblov hukmi chiqarish mumkin emas. Ikkinchidan, ekspert xulosasi asossiz rad etilgan, qayta ekspertiza o'tkazilishi kerak. Uchinchidan, voyaga yetmagan Anvarning himoyalanish huquqi qo'pol ravishda buzilgan. Uning dastlabki ko'rsatuvlari majburlash yo'li bilan olinganligi sababli nomaqbul dalil hisoblanadi. To'rtinchidan, jabrlanuvchining ko'rsatuv bermasligi va guvohliklarning qarama-qarshiligi ishning to'liq tekshirilmaganligini ko'rsatadi. Yakuniy javob: Anvar oqlanishi kerak. Ayblov hukmi chiqarish mumkin emas. Ish yangi tergovga yuborilishi yoki Anvarga nisbatan ish tugatilishi kerak.
"""

    final_prompt = f"""Siz O'zbekiston Respublikasi Jinoyat-protsessual kodeksi bo'yicha professional huquqshunos va imtihon komissiyasi a'zosisiz.

KAZUS:
{KAZUS_MATNI}

SARALAB OLINGAN ALOQADOR JPK MODDALARI:
{json.dumps(COLLECTED_ARTICLES, ensure_ascii=False, indent=2)}

============================================================
QUYIDA IRAC USULIDA YOZILGAN TO'G'RI JAVOB NAMUNASI KELTIRILGAN.
AYNAN SHU USLUBDA JAVOB YOZING. JADVAL ISHLATMANG. ODDIY MATN YOZING.
============================================================

NAMUNA JAVOB:
{IRAC_MISOL_JAVOB}

============================================================
ENDI O'ZINGIZ YUQORIDAGI KAZUS VA TOPILGAN MODDALAR ASOSIDA JAVOB YOZING.
============================================================

TALAB QILINADIGAN JAVOB FORMATI (IRAC):

I — ISSUE (Muammo):
Kazusdagi asosiy huquqiy masalalarni 3-5 gapda yozing. "Ushbu kazusda quyidagi huquqiy masalalar mavjud: Birinchidan... Ikkinchidan... Uchinchidan..." deb boshlang.

R — RULE (Qonun qoidasi):
Har bir masala uchun tegishli JPK moddalarini keltiring. "JPKning X-moddasiga ko'ra..." deb boshlang.

A — APPLICATION (Qonunni kazusga qo'llash):
Har bir masala bo'yicha kazusdagi faktlarni qonun bilan solishtiring. "Birinchi masala bo'yicha, kazusda..." deb boshlang.

C — CONCLUSION (Xulosa):
5-7 gapda yakuniy xulosani yozing. Eng oxirgi gapda "Yakuniy javob: ..." deb aniq xulosani yozing.

HAVOLA FORMATI (qat'iy):
Har bir moddaga havolani ro'yxatdagi "lex_url" dan oling. Format: (Havola: https://lex.uz/docs/-111460#-XXXXX)

MUHIM QOIDALAR:
1. Hech qanday jadval ishlatmang
2. Hech qanday belgi (*, -, #, |) ishlatmang
3. Har bir gap nuqta bilan tugasin
4. Abzaslar orasida bir qator bo'sh joy qoldiring
5. Javob kamida 500 so'zdan iborat bo'lsin
6. NAMUNADAGI USLUB VA SIFATDA JAVOB YOZING
"""

    try:
        final_res = client.chat.completions.create(
            model=MODEL_PRO,
            messages=[
                {"role": "system", "content": "Siz O'zbekiston Jinoyat-protsessual kodeksi bo'yicha professional huquqshunossiz. Sizning vazifangiz — kazuslarni IRAC usulida tahlil qilish va aniq, tushunarli xulosalar chiqarish. Hech qachon jadval ishlatmaysiz. Hech qachon qisqa javob yozmaysiz. Har bir javobingiz kamida 500 so'zdan iborat bo'ladi."},
                {"role": "user", "content": final_prompt}
            ],
            stream=False,
            temperature=0.7,  # 0.0 emas! Batafsil javob uchun
            extra_headers=extra_headers,
            extra_body={
                "thinking": {"type": "enabled"},
                "reasoning_effort": "high"
            }
        )

        final_text = final_res.choices[0].message.content

        print("\n" + "=" * 80)
        print("🏆 LEX.UZ HAVOLALARI BILAN YAKUNIY XULOSA (v3 — IRAC usuli)")
        print("=" * 80)
        print(final_text)
        print("=" * 80)

        with open("lexai_v3_xulosa.txt", "w", encoding="utf-8") as f:
            f.write(final_text)
        print("\n💾 'lexai_v3_xulosa.txt' fayliga saqlandi.")

        print("\n" + "-" * 50)
        print("📊 SAMARADORLIK HISOBOTI:")
        print(f"   Skanerlangan boblar   : {len(all_files)} ta")
        print(f"   Topilgan aloqador el. : {len(COLLECTED_ARTICLES)} ta")
        print(f"   API chaqiruvlar (v3)  : {len(all_files)} ta")
        print(f"   ✅ V1 ga nisbatan tejaldi: ~{764 - len(all_files)} ta chaqiruv")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Yakuniy tahlilda xato: {e}")
        save_backup_results()


if __name__ == "__main__":
    run_pipeline()