# Nizom Parser — lex.uz Nizomlar

**Manba:** Vazirlar Mahkamasi qarorlari, nizomlar (masalan `-2493774`, `-3020217`)
**HTML:** `ACT_TEXT` ko'p, `CLAUSE` kam, ko'pincha `1.`, `2.` bandlar

**Pattern:** Plenum kabi, lekin Nizomda `1. Umumiy qoidalar` bandlari:
```regex
<div class="ACT_TEXT lx_elem".*?<div name="(-?\d+)" id="(-?\d+)">(.*?)</div>\s*</div>
```

**Band ajratish:** `^(\d+)\.` → band raqami

**Chiqish JSON:**
```json
{
  "nizom_nomi": "Vazirlar Mahkamasi 305-son qarori",
  "nizom_id": "-2493774",
  "bandlar": [{"band_raqami":"1","id":"https://lex.uz/docs/-2493774#-2493775","matn":"1. Ushbu Nizom ..."}]
}
```

**Saqlash:** `data/jinoyat/nizomlar/`, `data/fuqorolik/nizomlar/` ...
