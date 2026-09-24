def build_scan_prompt(kazus, batch_text, batch_num, total_batches, manba="JPK"):
    kodeks_nomi = (
        "O'zbekiston Jinoyat kodeksi" if manba == "JK"
        else "O'zbekiston Jinoyat-protsessual kodeksi"
    )

    oqibat_qoidasi = ""
    if manba == "JPK":
        oqibat_qoidasi = """
MUHIM — OQIBAT QOIDASI:
Agar kazusda qonun buzilishi bo'lsa (qo'rqitish, himoyachini kiritmaslik,
advokatni so'roq qilish, qiynoq), faqat BUZILGAN moddani emas, balki uning
OQIBATI bo'lgan moddalarni ham top:
- JPK 95 (Dalillar maqbulligi)
- JPK 11 (Qonuniylik)
- JPK 88 (Isbotlash)
"""

    if manba == "JK":
        javob_namuna = """{
  "relevant_moddalar": [
    {
      "modda_raqami": <n>,
      "modda_sarlavhasi": "<sarlavha>",
      "element_id": "<id>",
      "qism_yoki_band": "<qism>",
      "kazusdagi_holat": "<1-2 jumla>",
      "qonuniy_asos": "<1-2 jumla>",
      "buzilganmi": true
    }
  ]
}"""
    else:
        javob_namuna = """{
  "relevant_moddalar": [
    {
      "modda_raqami": <n>,
      "modda_sarlavhasi": "<sarlavha>",
      "element_id": "<id>",
      "qism_yoki_band": "<qism>",
      "kazusdagi_holat": "<1-2 jumla>",
      "qonuniy_asos": "<1-2 jumla>"
    }
  ]
}"""

    return f"""Siz {kodeks_nomi} bo'yicha professional huquqshunossiz.

KAZUS:
{kazus}

{manba} MODDALARI (Batch {batch_num}/{total_batches}):
{batch_text}

VAZIFA: Qaysi moddalar kazusga aloqador?
{oqibat_qoidasi}
⚠️ MUHIM: Faqat yuqorida berilgan moddalardan tanlang. Boshqa moddalarni qo'shmang.
Har bir modda uchun "n" maydonidagi raqamni "modda_raqami" sifatida, "sarlavha_id" dan oxirgi qismni "element_id" sifatida oling.

JAVOBNI JSON FORMATIDA BERING:
{javob_namuna}
Agar aloqador yo'q bo'lsa: {{"relevant_moddalar": []}}"""


def build_plenum_prompt(kazus, plenum_text):
    return f"""Siz O'zbekiston Huquq tizimi bo'yicha professional huquqshunossiz.

KAZUS:
{kazus}

PLENUM MA'LUMOTLARI:
{plenum_text}

VAZIFA:
1. Ushbu plenum kazusga qanday aloqadorligini aniqlang
2. Plenumning qaysi bandlari kazusga to'g'ri kelishini ko'rsating
3. Kazus faktlari plenum talablari bilan qanday mos kelishini tahlil qiling
4. Qaysi JK/JPK moddalari ushbu plenum orqali izohlanishini ko'rsating

JAVOBNI JSON FORMATIDA BERING:
{{
  "plenum_mavzu": "<plenum nomi>",
  "kazusga_aloqadorlik": "<1-3 jumla>",
  "tegishli_bandlar": [
    {{
      "band_raqami": "<band raqami>",
      "kazusga_moslik": "<1-2 jumla>",
      "izoh": "<1 jumla>"
    }}
  ],
  "bogliq_jk_moddalar": [],
  "bogliq_jpk_moddalar": [],
  "tahlil": "<3-5 gap>"
}}
Agar yo'q bo'lsa: {{"plenum_mavzu": "...", "kazusga_aloqadorlik": "yo'q", "tegishli_bandlar": [], "bogliq_jk_moddalar": [], "bogliq_jpk_moddalar": [], "tahlil": "..."}}"""


def build_irac_prompt(kazus, jk_text, jpk_text, plenum_text):
    return f"""Siz O'zbekiston Jinoyat kodeksi, Jinoyat-protsessual kodeksi va Oliy Sud Plenumlari bo'yicha professional huquqshunossiz.

KAZUS:
{kazus}

JK TOPILGANLARI:
{jk_text or "Topilmadi"}

JPK TOPILGANLARI:
{jpk_text or "Topilmadi"}

PLENUMLAR:
{plenum_text or "Topilmadi"}

IRAC USULIDA JAVOB YOZING:
I — ISSUE: 4-6 gapda. "Ushbu kazusda quyidagi huquqiy masalalar mavjud..."
R — RULE: Moddalarni havolalar bilan keltiring. Har bir modda uchun lex.uz havolasini ko'rsating.
A — APPLICATION: Faktlarni qonun bilan solishtiring. Plenum talablari asosida tahlil qiling.
C — CONCLUSION: 5-7 gapda. "Yakuniy javob: ..." deb aniq xulosa.

QOIDALAR: Jadval yo'q. Kamida 800 so'z. Havolalar bilan. Professional til. Disclaimer qo'shing."""
