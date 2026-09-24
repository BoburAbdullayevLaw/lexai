# Jinoyat Kodeksi (JK) Moddalari va Sharhlar Bazasi

## Maqsad
O'zbekiston Respublikasi Jinoyat kodeksining moddalarini va ularning sharhlarini tizimli shaklda JSON formatida saqlash.

## Direktoriya tuzilishi
```
data/jinoyat/kodekslar/jk/
├── modda_1.json
├── modda_2.json
├── ...
├── modda_103.json
├── modda_103-1.json
└── modda_302.json
```

## JSON strukturasi
Har bir modda fayli quyidagi formatda:
```json
{
  "n": 1,
  "kod": "JK",
  "sarlavha_id": "https://lex.uz/docs/-111453#-5449385",
  "sarlavha": "1-modda. Oʻzbekiston Respublikasining jinoyat toʻgʻrisidagi qonunchiligi",
  "qismlar": [
    {
      "q": 1,
      "id": "https://lex.uz/docs/-111453#-5449389",
      "matn": "Modda matni..."
    }
  ],
  "sharh": [
    "1-sharh matni...",
    "2-sharh matni..."
  ]
}
```

## Maydonlar tavsifi
| Maydon | Tavsif |
|--------|--------|
| `n` | Modda raqami |
| `kod` | Kodeks kodi (JK) |
| `sarlavha_id` | Lex.uz manba URLi |
| `sarlavha` | Modda sarlavhasi |
| `qismlar` | Modda qismlari ro'yxati |
| `q` | Qism raqami |
| `bandlar` | Bandlar (agar bo'lsa) |
| `matn` | Matn |
| `sharh` | Sharhlar ro'yxati (tozalangan) |

## Sharhlarni tozalash qoidalari

### 1. Formatlashni tuzatish
- Buzilgan tirnoq belgilarini tuzatish: `"`, `"`, `'`, `'` → oddiy `"` yoki `'`
- Ketma-ket bo'sh joylarni tozalash
- Ortiqcha qavslarni olib tashlash

### 2. Mazmunni tozalash
- Keraksiz takrorlarni olib tashlash
- Murakkab jumlalarni soddalashtirish
- Jinoyat kodeksiga doir muhim ma'lumotlarni saqlash
- Noto'g'ri yoki eskirgan ma'lumotlarni olib tashlash
- **"Subьekt" so'zini "Subyekt" ga almashtirish** (har bir modda uchun qo'llaniladi)

### 3. Strukturalash
- Har bir sharh mustaqil element sifatida saqlanadi
- Sharhlar raqamlangan ro'yxat shaklida
- Qisqa va tushunarli bo'lishi kerak

## Tozalangan moddalar ro'yxati

### Umumiy qism (1-96 moddalar)
| Bob | Moddalar | Sharh holati |
|-----|----------|--------------|
| I bob | 1-20 | ✓ Tugadi |
| II bob | 21-26 | ✓ Tugadi |
| III bob | 27-35 | ✓ Tugadi |
| IV bob | 36-42 | ✓ Tugadi |
| V bob | 43-48 | ✓ Tugadi |
| VI bob | 49-54 | ✓ Tugadi (modda_53 hisoblanmagan) |
| VII bob | 55-57-2 | ✓ Tugadi |
| VIII bob | 58-63 | ✓ Tugadi |
| IX bob | 64-68 | ✓ Tugadi |
| X bob | 69-76 | ✓ Tugadi |
| XI bob | 77-80 | ✓ Tugadi |
| XII bob | 81-86 | ✓ Tugadi |
| XIII bob | 87-90 | ✓ Tugadi |
| XIV bob | 91-96 | ✓ Tugadi |

### Maxsus Qism
| Bob | Moddalar | Sharh holati |
|-----|----------|--------------|
| I bob | 97-103-1 | ✓ Tugadi |
| II bob | 104-111 | ✓ Tugadi |
| III bob | 112-117 | ✓ Tugadi |
| IV bob | 118-121 | ✓ Tugadi |
| V bob | 122-134 | ✓ Tugadi |
| VI bob | 135-140 | ✓ Tugadi |
| VII bob | 141-149 | ✓ Tugadi (141-1, 141-2, 141-3, 148-1, 148-2, 149-1, 149-2, 149-3 — sharh hali yo'q) |
| VIII bob | 150-156 | ✓ Tugadi (154-1, 155-1, 155-2, 155-3 — sharh hali yo'q) |
| IX bob | 157-163 | ✓ Tugadi |
| X bob | 164-169 | ✓ Tugadi |
| XI bob | 170-174 | ✓ Tugadi |
| XII bob | 175-185-2 | ✓ Tugadi |
| XIII bob | 186-192 | ✓ Tugadi (187 chiqarilgan, 186, 186-2, 186-3, 188, 188-1, 189, 190, 191, 192 — yaratildi) |
| XIII-1 bob | 192-1 — 192-12 | ✓ Tugadi |
| XIV bob | 193-204 | ✓ Tugadi (193, 194, 195, 196, 197, 197-1, 198, 199, 200, 201, 202, 202-1, 203, 204) |
| XV bob | 205-229-6 | ✓ Tugadi (205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 214-1, 214-2, 215, 216, 216-1, 216-2, 217, 218, 219, 220, 221, 222, 223, 225, 226, 227, 227-1, 228, 228-1, 228-2, 229, 229-1, 229-2, 229-3, 229-4, 229-5, 229-6) |
| XVI bob | 230-241-1 | ✓ Tugadi (230, 230-1, 230-2, 231, 232, 232-1, 233, 234, 235, 236, 237, 238, 239, 240, 241, 241-1) |
| XVII bob | 242-259-1 | ✓ Tugadi (242, 243, 244, 244-1, 244-2, 244-3, 244-4, 244-5, 244-6, 245, 246, 247, 248, 248-1, 249, 250, 250-1, 251, 251-1, 251-2, 252, 253, 254, 255, 255-1, 255-2, 256, 257, 257-1, 258, 259, 259-1) |
| XVIII bob | 260-269 | ✓ Tugadi (260, 260-1, 261, 262, 263, 263-1, 264, 265, 266, 267, 268, 269) |
| XIX bob | 270-276 | ✓ Tugadi (270, 271, 273, 274, 275, 276. 272 chiqarilgan) |
| XX bob | 277-278 | ✓ Tugadi (277, 278) |
| XX-1 bob | 278-1 — 278-9 | ✓ Tugadi (278-1, 278-2, 278-3, 278-4, 278-5, 278-6, 278-7, 278-8, 278-9) |
| XXI bob | 279-286 | ✓ Tugadi (279, 280, 281, 282, 283, 284, 285, 286) |
| XXII bob | 287-294 | ✓ Tugadi (287, 288, 289, 290, 291, 292, 293, 294) |
| XXIII-XXIV bob | 295-302 | ✓ Tugadi (295, 296, 297, 298, 299, 300, 301, 302) |
| XXV bob | 303 | ✓ Tugadi (303) |

### Sharh tuzilishi
- Oddiy moddalar: `"sharh": ["...", "..."]`
- Bandli moddalar: `"sharh": {"qism_1": [...], "qism_2": [...]}`
- Band sharhlari: `{"band": "a", "sharh": [...]}`

## Keyingi qadamlar
1. Bazani yangilab turish

## Manbalar
- Asosiy manba: https://lex.uz/docs/-111453
- Sharhlar: O'zbekiston Respublikasi Oliy sudi Plenumi qarorlari
