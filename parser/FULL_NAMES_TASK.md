# Vazifa: Har bir hujjat nomini to'liq yozish

**Talab:** `lex.uz` dan olinadigan har bir Kodeks, Qonun, Plenum, Nizom JSON da `id` dan tashqari **to'liq rasmiy nomi** yozilishi shart. Qisqa `-1595235 16-son Qamoq` kabi emas.

**Qoidalar:**
1. **Plenum:** `qaror_nomi` = `O'zbekiston Respublikasi Oliy sudi Plenumining 2007-yil 14-noyabrdagi “Sudga qadar ish yuritish bosqichida qamoqqa olish tarzidagi ehtiyot chorasining sudlar tomonidan qo'llanilishi to'g'risida”gi 16-sonli qarori` + `qaror_id: -1595235`, `manba: https://lex.uz/docs/-1595235`
   - Fayl nomi ham to'liq: `Oliy_sud_Plenumi_2007-11-14_16-son_qamoqqa_olish.json` (ixtiyoriy, lekin `qaror_nomi` ichida to'liq bo'lishi shart)

2. **Kodeks:** Har bir `modda_*.json` da:
   ```json
   {
     "kodeks_nomi": "O'zbekiston Respublikasi Jinoyat kodeksi",
     "n": "1",
     "sarlavha": "1-modda. ...",
     "sarlavha_id": "https://lex.uz/docs/-111453#-5449385"
   }
   ```
   JK = `O'zbekiston Respublikasi Jinoyat kodeksi (-111453)`, JPK = `O'zbekiston Respublikasi Jinoyat-protsessual kodeksi (-111460)`, Mehnat = `O'zbekiston Respublikasi Mehnat kodeksi (-6257288)`

3. **Qonun:** `qonun_nomi` = `O'zbekiston Respublikasining “Sudlar to'g'risida”gi Qonuni` kabi to'liq

4. **Nizom:** `nizom_nomi` to'liq

**Tekshiruv:** `id` har doim to'liq URL `https://lex.uz/docs/-111460#-252771`, `sarlavha_id` ham to'liq.

**Holat:** `plenum_16_qamoq.json` to'liq nomga o'tkazildi, `jinoyat/kodekslar/jpk|jk` da `kodeks_nomi` qo'shilmoqda.
