import httpx, re, json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
Plenum parser — ketma-ket raqamlar asosida bandlarni ajratadi.
31. kabi raqamlar xatboshi deb hisoblaydi (3-band ichida).
Ishlatish: python parse_plenum.py <qaror_id> <sana> <raqami> <qaror_nomi>
Misol: python parse_plenum.py -1595235 2007-11-14 16-son "Oliy sud Plumentining 16-sonli qarori"
"""

def parse_plenum(qaror_id, sana, raqami, qaror_nomi):
    url = f'https://lex.uz/docs/{qaror_id}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = httpx.get(url, headers=headers, timeout=30, follow_redirects=True)
    html = r.text

    pat = re.compile(r'<div class="ACT_TEXT lx_elem".*?<div name="(-?\d+)" id="(-?\d+)">(.*?)</div>\s*</div>', re.DOTALL)
    acts = []
    for m in pat.finditer(html):
        body = re.sub(r'<[^>]+>', '', m.group(3))
        body = re.sub(r'\s+', ' ', body).strip()
        if body:
            acts.append({'id': m.group(2), 'text': body})

    # Find all number-dot starts
    all_num_starts = []
    for i, a in enumerate(acts):
        m = re.match(r'^(\d+)\.\s+', a['text'])
        if m:
            all_num_starts.append((i, int(m.group(1)), a))

    # Determine top-level: sequential from 1
    top_level = []
    for idx, num, a in all_num_starts:
        if len(top_level) == 0 and num == 1:
            top_level.append((idx, num, a))
        elif len(top_level) > 0:
            if num == top_level[-1][1] + 1:
                top_level.append((idx, num, a))

    print(f"Total ACT: {len(acts)}, Top-level bands: {len(top_level)}")

    # Group into bands
    bands = []
    for j, (idx, num, a) in enumerate(top_level):
        next_idx = top_level[j + 1][0] if j + 1 < len(top_level) else len(acts)
        xatboshilar = []
        for k in range(idx + 1, next_idx):
            xatboshilar.append({
                'id': f"https://lex.uz/docs/{qaror_id}#{acts[k]['id']}",
                'matn': acts[k]['text']
            })
        band = {
            'band_raqami': str(num),
            'id': f"https://lex.uz/docs/{qaror_id}#{a['id']}",
            'matn': a['text'],
            'xatboshilar': xatboshilar
        }
        bands.append(band)

    # Save
    out_dir = os.path.join('data', 'jinoyat', 'plenumlar', raqami)
    os.makedirs(out_dir, exist_ok=True)

    meta = {
        "qaror_nomi": qaror_nomi,
        "qaror_id": qaror_id,
        "manba": url,
        "bandlar_soni": len(bands),
        "sana": sana,
        "raqami": raqami
    }
    with open(os.path.join(out_dir, '_plenum.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    for b in bands:
        fname = f"band_{b['band_raqami']}.json"
        out = {"band_raqami": b['band_raqami'], "id": b['id'], "matn": b['matn'], "xatboshilar": b['xatboshilar']}
        with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Created {len(bands)} band files in {out_dir}")
    return bands

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python parse_plenum.py <qaror_id> <sana> <raqami> <qaror_nomi>")
        print("Misol: python parse_plenum.py -1595235 2007-11-14 16-son 'Oliy sud Plumentining 16-sonli qarori'")
        sys.exit(1)
    parse_plenum(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
