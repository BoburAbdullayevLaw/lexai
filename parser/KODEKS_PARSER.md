# Kodeks Parser — lex.uz HTML → JSON

**Manba:** `https://lex.uz/docs/-111453` (JK), `-111460` (JPK), `-6257288` (Mehnat)
**HTML sinflar:**
- `TEXT_HEADER_DEFAULT lx_elem` — 95 ta, bo'lim/bob sarlavhasi (UMUMIY QISM, I BO'LIM)
- `CLAUSE_DEFAULT lx_elem` — 581 ta, modda sarlavhasi (`1-modda. ...` name/id="-252771")
- `ACT_TEXT lx_elem` — 2956 ta, qism/band matni

**Pattern:**
```regex
<div class="CLAUSE_DEFAULT lx_elem".*?<div name="(-?\d+)" id="(-?\d+)">(.*?)</div>\s*</div>
<div class="ACT_TEXT lx_elem".*?<div name="(-?\d+)" id="(-?\d+)">(.*?)</div>\s*</div>
```

**Ierarxiya:**
1. Barcha 3 sinfni `pos` (html dagi tartib) bo'yicha sort
2. Har `CLAUSE_DEFAULT` = yangi modda `{n, sarlavha, sarlavha_id: "https://lex.uz/docs/-111453#-252771", header: TEXT_HEADER, qismlar: []}`
3. Keyingi `CLAUSE` gacha bo'lgan `ACT_TEXT` larni shu moddaga yig'ish (5-10 ta)

**Qism/Band ajratish (Muse bepul, $0):**
- `:` bilan tugagan `Ushbu Kodeksning ... iborat:` → `qism` (`q:1`)
- `;` bilan tugagan `xodimlar ...;` → `band` (`b:1` qism ichida)
- Har birida `id` to'liq URL: `https://lex.uz/docs/-111453#-252771`

**QOIDA — Har modda alohida JSON (bitta qilinsa xatolik bo'ladi):**
- `modda_1.json`, `modda_2.json` ... har biri alohida fayl, bitta `jk.json` da 581 modda emas
- Har birida `kodeks_nomi` to'liq: `"O'zbekiston Respublikasi Jinoyat kodeksi"`

**Chiqish JSON (alohida fayl):**
```json
{
  "kodeks_nomi": "O'zbekiston Respublikasi Jinoyat kodeksi",
  "n": "2",
  "sarlavha": "2-modda. Asosiy vazifalari",
  "sarlavha_id": "https://lex.uz/docs/-111453#-252771",
  "qismlar": [{"q":1,"matn":"...","id":"https://lex.uz/docs/-111453#-252772","bandlar":[{"b":1,"matn":"...","id":"https://..."}]}]
}
```
**Saqlash:** `data/jinoyat/kodekslar/jk/modda_2.json` (581 ta alohida), `data/fuqorolik/kodekslar/...`
**Model:** `deepseek-v4-flash $0.14/1M` per CLAUSE chunk (1k token) yoki Muse bepul regex
