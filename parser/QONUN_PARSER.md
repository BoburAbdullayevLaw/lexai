# Qonun Parser — lex.uz Qonunlar

**Manba:** `https://lex.uz/docs/-111189` (Fuqarolik), `Konstitutsiya`, `Sudlar to'g'risida`
**HTML sinflar:** Kodeks kabi `TEXT_HEADER`, `CLAUSE`, `ACT` — lekin Qonunda modda kam (50-100), band ko'p

**Pattern:** Kodeks bilan bir xil, faqat `CLAUSE_DEFAULT` kam:
```regex
<div class="CLAUSE_DEFAULT lx_elem".*?<div name="(-?\d+)" id="(-?\d+)">(.*?)</div>\s*</div>
```

**Farqi:**
- Qonunda `TEXT_HEADER` = "I. Umumiy qoidalar" kabi bo'lim
- `CLAUSE` = modda, lekin "1-modda. Qonunning maqsadi" qisqa
- `ACT_TEXT` = modda matni, ko'pincha 1-2 qism, band yo'q

**Chiqish JSON:** Kodeks bilan bir xil schema:
```json
{
  "n": "1",
  "sarlavha": "1-modda. Qonunning maqsadi",
  "sarlavha_id": "https://lex.uz/docs/-111189#-111190",
  "qismlar": [{"q":1,"matn":"Ushbu Qonun ...","id":"https://lex.uz/docs/-111189#-111191","bandlar":[]}]
}
```

**Saqlash:** `data/jinoyat/qonunlar/`, `data/fuqorolik/qonunlar/`, `data/iqtisodiy/qonunlar/`
