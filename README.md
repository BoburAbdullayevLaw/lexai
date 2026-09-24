# Lex AI — O'zbekiston huquqiy AI agent

Jinoyat-protsessual kodeks (JPK), Jinoyat kodeksi (JK) va Oliy Majlis plenum qarorlaridan **kazus-relevant moddalarni** tanlab, **IRAC** (Issue → Rule → Application → Conclusion) tahlilini LLM orqali yaratuvchi agentic pipeline.

## Nima uchun RAG emas?

An'anaviy RAG (chunking + vector search) huquqiy matnlarda ko'p marta mayda-kichik qoidalarni ajratib tashlaydi va modda bandini buzadi. Bu loyiha **"Agentic Filtering"** yondashuvini ishlatadi: to'liq modda JSONlari batch-larda modelga beriladi, model esa faqat kazusga tegishli qismlarni tanlaydi.

## Tuzilma

```
lexai/
  main.py          # kirish nuqtasi
  config.py        # BATCH_SIZE, model nomlari, ROOT path
  clients.py       # OpenRouter client + safe_api_call
  kazus.py         # test kazusi matni
  prompts.py       # JK / JPK / Plenum / IRAC promptlar
  pipeline.py      # parallel skan + backup + IRAC
  irac.py          # IRAC formatlash + generate_irac
  safety_net.py    # safety-net qoidalar
  backup.py        # thread-safe JSON backup
  utils.py         # natural_sort_key, modda_id_key, batch_modda_ids
  scanners/
    jk.py jpk.py plenum.py
data/
  jinoyat/kodekslar/jk|jpk/   # modda_*.json
  jinoyat/plenumlar/          # plenum qarorlari
  qonunlar/                   # qonun moddalari
parser/                       # lex.uz parserlari
main_v7.py                    # legacy monolith (refaktor oldin)
```

## Ishga tushirish

```powershell
# 1) .env fayl tayyorlang (OPENROUTER_API_KEY=...)
# 2) virtual env
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install openai python-dotenv

# 3) agentlarni tanlang (1=JK, 2=JPK, 3=Plenum) va ishga tushiring
python lexai\main.py
```

## Batch size tajribasi

| Batch | Kazus savollari aniqligi (gold standard) |
|-------|------------------------------------------|
| 10    | 11/20 (55%) |
| 5     | **20/20 (100%)** |
| 3     | tekshirilmoqda |

`config.py` → `BATCH_SIZE = 5`.

## Texnik eslatmalar

- **Sort:** `natural_sort_key` raqamli tartib (`1, 2, 10`, `95 → 95-1`), eski alphabetik sort tuzatilgan.
- **Sub-modda:** `n` maydoni ba'zan `str` (`"95-1"`, `"254¹⁰"`) — eski `int()` crash tuzatildi (308/308 test).
- **Kuchini yo'qotgan moddalar:** JK'da 48, 53, 84, 187, 224, 272… — ular chiqarilgan, fayl yo'qligi normal holat.

## License

Private / portfolio — huquqiy matnlar manbasi: [lex.uz](https://lex.uz).
