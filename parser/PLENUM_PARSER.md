# Plenum Parser — lex.uz Plenum qarorlari

**Manba:**
- `https://lex.uz/docs/-1441585` (3-son Qurol, 15 band, 39 ACT)
- `https://lex.uz/docs/-1592419` (6-son Badanga shikast, 26 band, 63 ACT)
- `https://lex.uz/docs/-7469894` (6-son O'g'rilik, 13 band, 41 ACT)
- `https://lex.uz/docs/-1449617` (8-son Valyuta, 5 band, 31 ACT)
- `https://lex.uz/docs/-1443984` (11-son Iqtisodiyot, 8 band, 41 ACT)
- `https://lex.uz/docs/-1600001` (13-son Kvalifikatsiya, 31 band, 67 ACT)
- `https://lex.uz/docs/-1455961` (13-son Qasddan o'ldirish, 27 band, 69 ACT)
- `https://lex.uz/docs/-1595235` (16-son Qamoq, 35 band, 93 ACT)
- `https://lex.uz/docs/-1453755` (17-son Himoya huquqi, 33 band, 119 ACT)
- `https://lex.uz/docs/-6033155` (18-son Birinchi instansiya, 25 band, 60 ACT)
- `https://lex.uz/docs/-1446429` (20-son O'zini o'zi o'ldirish, 9 band, 18 ACT)
- `https://lex.uz/docs/-1449720` (21-son Voyaga yetmaganlar, 15 band, 40 ACT)
- `https://lex.uz/docs/-1601125` (23-son Ruhiy holat, 27 band, 56 ACT)
- `https://lex.uz/docs/-3895986` (24-son Dalillar maqbulligi, 19 band, 72 ACT)
- `https://lex.uz/docs/-6884042` (7-son Apellyatsiya/Kassatsiya, 40 band, 127 ACT)
- `https://lex.uz/docs/-3115385` (26-son Mulkiy ziyon, 22 band, 61 ACT)
- `https://lex.uz/docs/-1591984` (16-son Amnistiya, 9 band, 76 ACT)
- `https://lex.uz/docs/-2212245` (08-son Soliqlar, 21 band, 85 ACT)
- `https://lex.uz/docs/-1442456` (36-son Ekologiya, 17 band, 34 ACT)
- `https://lex.uz/docs/-2710284` (10-son Transport, 29 band, 74 ACT)
- `https://lex.uz/docs/-2414120` (13-son Nomusga tegish, 19 band, 50 ACT)
- `https://lex.uz/docs/-2414513` (17-son Ashyoviy dalillar, 12 band, 34 ACT)
- `https://lex.uz/docs/-1449106` (19-son Poraxorlik, 11 band, 33 ACT)
- `https://lex.uz/docs/-6523582` (17-son Firibgarlik, 34 band, 68 ACT)
- `https://lex.uz/docs/-1616053` (12-son Odam savdosi, 16 band, 45 ACT)
- `https://lex.uz/docs/-1449509` (7-son Ma'naviy zarar, 11 band, 37 ACT)
- `https://lex.uz/docs/-1616840` (13-son Protsessual chiqim, 13 band, 45 ACT)
- `https://lex.uz/docs/1452652` (9-son Bezorilik, 16 band, 39 ACT)
- `https://lex.uz/docs/-1455976` (1-son Jazo tayinlash, 23 band, 242 ACT)
- `https://lex.uz/docs/-1593076` (15-son Umrbod, 16 band, 32 ACT)
- `https://lex.uz/docs/-1442647` (39-son Zaruriy mudofaa, 16 band, 29 ACT)
- `https://lex.uz/docs/-1454894` (4-son Liberallashtirish, 9 band, 45 ACT)
- `https://lex.uz/docs/-4393049` (11-son Nazorat tartibi, 47 band, 137 ACT)
- `https://lex.uz/docs/-2793078` (13-son Sudlanganlik, 14 band, 45 ACT)
- `https://lex.uz/docs/-1453539` (27-son Yarashuv, 9 band, 29 ACT)
- `https://lex.uz/docs/-6685595` (29-son Harbiy xizmat, 63 band, 174 ACT)
- `https://lex.uz/docs/-6404212` (2-son Bojxona, 25 band, 78 ACT)
- `https://lex.uz/docs/-1442544` (37-son Transport vositalarini olib qochish, 8 band, 17 ACT)
- `https://lex.uz/docs/-2307198` (20-son Tadbirkorlik, 9 band, 65 ACT)
- `https://lex.uz/docs/-3203265` (12-son Giyohvandlik, 37 band, 71 ACT)
**HTML:** `CLAUSE_DEFAULT 0`, `ACT_TEXT` — faqat bandlar, modda yo'q

**Pattern:** Faqat `ACT_TEXT lx_elem`:
```regex
<div class="ACT_TEXT lx_elem".*?<div name="(-?\d+)" id="(-?\d+)">(.*?)</div>\s*</div>
```

**QOIDA — Har band alohida JSON (bitta qilinsa xatolik bo'ladi):**
- 16-son: 35 ta top-level band, 93 ACT dan — `band_1.json` ... `band_35.json`
- 17-son: 33 ta top-level band, 119 ACT dan — `band_1.json` ... `band_33.json`
- 24-son: 19 ta top-level band, 72 ACT dan — `band_1.json` ... `band_19.json`
- **XATO:** har bandda `qaror_nomi/qaror_id/manba` ni takrorlash — keraksiz, `_plenum.json` da 1 marta yetarli
- Har bandda faqat: `{band_raqami, id, matn, xatboshilar}`

**Band ajratish (muhim — raqamlar ketma-ket emasligi mumkin!):**
- `^(\d+)\.\s+` barcha raqam-boshlanishlarni topadi
- Faqat **ketma-ket** raqamlar (1, 2, 3, 4...) = top-level band
- `31.` kabi raqamlar xatboshi (masalan: 3-band ichida 31-chi xatboshi)
- Qolgan `;` / `qasddan...;` → `xatboshilar` o'sha band ichida
- Har bir `id` to'liq: `https://lex.uz/docs/{qaror_id}#{act_id}`

**Chiqish JSON (har band alohida fayl) — TO'G'RI (qaror_nomi/qaror_id/manba YO'Q):**
```json
// data/jinoyat/plenumlar/16-son/band_1.json
{
  "band_raqami": "1",
  "id": "https://lex.uz/docs/-1595235#-6689611",
  "matn": "1. Tushuntirilsinki, qamoqqa olishga sanksiya berish huquqining sudlarga o'tkazilishi ...",
  "xatboshilar": []
}
```

**Saqlash:**
- `data/jinoyat/plenumlar/3-son/` — 15 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/6-son/` — 26 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/8-son/` — 5 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/11-son/` — 8 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/13-son/` — 27 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/16-son/` — 35 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/17-son/` — 33 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/18-son/` — 25 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/20-son/` — 9 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/24-son/` — 19 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/3115385/` — 22 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/amnistiya/` — 9 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/apellyatsiya/` — 40 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/ashyoviy-dalillar/` — 12 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/bezorilik/` — 16 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/bojxona/` — 25 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/ekologiya/` — 17 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/iqtisodiyot/` — 8 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/jazo-tayinlash/` — 23 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/kvalifikatsiya/` — 31 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/liberallashtirish/` — 9 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/manaviy-zarar/` — 11 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/nomus/` — 19 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/nazorat-tartibi/` — 47 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/ogrilik-talonchilik/` — 13 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/oldirish/` — 27 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/odam-savdosi/` — 16 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/poraxorlik/` — 11 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/protsessual-chiqim/` — 13 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/ruhiy/` — 27 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/soliq/` — 21 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/sudlanganlik/` — 14 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/tadbirkorlik/` — 9 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/tashabbus-qochish/` — 8 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/transport/` — 29 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/umrbod/` — 16 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/valyuta/` — 5 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/voyaga-yetmagan/` — 15 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/zaruriy-mudofaa/` — 16 ta band + `_plenum.json`
- `data/jinoyat/plenumlar/yarashuv/` — 9 ta band + `_plenum.json`
**Eslatma:** Plenum nomi to'liq yozilsin — `16-son Qamoq` emas, `Oliy sud Plenumi 2007-11-14 16-son ...` deb `_plenum.json` da

**FIVE-SHOT — 5 ta to'g'ri band namunasi:**
```json
// 16-son band_1.json
{"band_raqami":"1","id":"https://lex.uz/docs/-1595235#-6689611","matn":"1. Tushuntirilsinki...","xatboshilar":[]}
// 16-son band_3.json
{"band_raqami":"3","id":"https://lex.uz/docs/-1595235#-7341077","matn":"3. Qonunchilikka muvofiq...","xatboshilar":[{"id":"https://lex.uz/docs/-1595235#-1596169","matn":"Qamoqqa olish tarzidagi..."},{"id":"https://lex.uz/docs/-1595235#-1596171","matn":"qasddan sodir etilgan..."}]}
// 24-son band_3.json (31. raqami xatboshi!)
{"band_raqami":"3","id":"https://lex.uz/docs/-3895986#-3896144","matn":"3. JPK 951-moddasiga ko'ra...","xatboshilar":[{"id":"https://lex.uz/docs/-3895986#-7618078","matn":"31. Qonunga xilof usullar orqali..."}]}
// 24-son band_9.json
{"band_raqami":"9","id":"https://lex.uz/docs/-3895986#-3896229","matn":"9. Dalil u JPK talablari buzilgan...","xatboshilar":[20 ta xatboshi, jumladan a),b),v),g),d),e),j),z),i),k),l),m),n),o)...]}
// 16-son band_35.json
{"band_raqami":"35","id":"https://lex.uz/docs/-1595235#-1596650","matn":"35. ...","xatboshilar":[]}
```
