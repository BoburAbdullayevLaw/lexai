# -*- coding: utf-8 -*-
"""Mehnat kodeksi parser LLM — 1M kontekst, qism/band ajratish + ID biriktirish."""
import re, json, os

SYSTEM_PARSER = """Siz Mehnat kodeksi parserisiz. Vazifa: berilgan modda ning ACT_TEXT elementlarini qism/band ga ajratish.

QOIDALAR:
- Har elementda id (masalan -6257580) va matn bor — id ni SAQLAB QOLING, to'liq URL qilib qaytaring: "https://lex.uz/docs/-6257288#-6257580"
- "qism" — moddaning asosiy bo'limi (masalan "Ushbu Kodeksning asosiy vazifalari quyidagilardan iborat:" — bitta qism)
- "band" — qism ichidagi kichik band ("xodimlar mehnat huquqlari...;" kabi ";" bilan tugaganlar — band)
- Faqat JSON qaytaring, id larni to'liq URL: {"n":"2","sarlavha":"2-modda...","sarlavha_id":"https://lex.uz/docs/-6257288#-6257576","qismlar":[{"q":1,"matn":"Ushbu Kodeksning asosiy vazifalari quyidagilardan iborat:","id":"https://lex.uz/docs/-6257288#-6257578","bandlar":[{"b":1,"matn":"xodimlar...","id":"https://lex.uz/docs/-6257288#-6257580"}]}]}
- matn ga id ni qo'shmang, ";" ni saqlang
"""

def build_parser_prompt(modda_n, sarlavha, acts, doc_id="-6257288"):
    acts_text = "\n".join([f"{a['id']}: {a['text']}" for a in acts])
    return f"""MODDA: {modda_n} - {sarlavha}
Sarlavha ID: https://lex.uz/docs/{doc_id}#{acts[0]['id'] if acts else ''}

ACT_TEXT elementlar (id: matn):
{acts_text}

Vazifa: har birini qism/band ga ajratib JSON qaytaring. ID larni to'liq URL qiling.
"""

def parse_modda_llm(modda_n, sarlavha, sarlavha_id, acts, doc_id="-6257288", model="deepseek-v4-flash"):
    import os, json, time
    from dotenv import load_dotenv
    load_dotenv(r'C:\proyekt\huquqiy_agent\.env')
    load_dotenv(r'C:\proyekt\lex_uz_search_agent\.env', override=False)
    from openai import OpenAI
    # deepseek-v4-flash 1M -> DeepSeek API (api.deepseek.com), qwen -> OpenRouter
    if "deepseek" in model:
        client = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url='https://api.deepseek.com')
        extra = {}
    else:
        client = OpenAI(api_key=os.getenv('OPENROUTER_API_KEY'), base_url='https://openrouter.ai/api/v1')
        extra = {"extra_headers":{"HTTP-Referer":"https://lex.uz","X-Title":"huquqiy_agent"}}
    prompt = build_parser_prompt(modda_n, sarlavha, acts, doc_id)
    time.sleep(0.8)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":SYSTEM_PARSER},{"role":"user","content":prompt}],
        temperature=0.0,
        response_format={"type":"json_object"},
        **extra
    )
    content=resp.choices[0].message.content
    if '```' in content:
        content=content.split('```')[1].split('```')[0].strip().lstrip('json')
    data=json.loads(content)
    data['n']=str(modda_n)
    data['sarlavha']=sarlavha
    data['sarlavha_id']=sarlavha_id if sarlavha_id.startswith('http') else f"https://lex.uz/docs/{doc_id}#{sarlavha_id.lstrip('#')}"
    # id larni to'liq URL qilish
    for q in data.get('qismlar',[]):
        if q.get('id','').startswith('-'):
            q['id']=f"https://lex.uz/docs/{doc_id}#{q['id'].lstrip('#')}"
        for b in q.get('bandlar',[]):
            if b.get('id','').startswith('-'):
                b['id']=f"https://lex.uz/docs/{doc_id}#{b['id'].lstrip('#')}"
    return data

def mock_llm_classify(acts):
    """Hozircha LLM siz regex fallback — keyin OpenRouter 1M ga almashtiramiz."""
    qismlar=[]
    cur_q=None
    for a in acts:
        txt=a['text']
        # LLM fikirlashi kerak bo'lgan joy: "1." qismmi bandmi?
        # Regex: agar oldingi matn "quyidagilardan iborat:" bo'lsa keyingi "xodimlar..." band
        if re.match(r'^\d+\.\s+', txt) and len(txt) < 200 and 'modda' not in txt.lower():
            # qisqa raqamli sarlavha — qism bo'lishi mumkin, lekin LLM kontekstga qarab hal qiladi
            pass
        # Hozircha sodda: birinchi element qism sarlavhasi, qolganlari band
        if not qismlar:
            qismlar.append({'q': 1, 'matn': txt, 'id': a['id'], 'bandlar':[]})
            cur_q=qismlar[0]
        else:
            # band deb hisoblaymiz
            b_num=len(cur_q['bandlar'])+1
            cur_q['bandlar'].append({'b': b_num, 'matn': txt, 'id': a['id']})
    return {'qismlar': qismlar}
