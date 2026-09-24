import os
import json
import time
from config import PLENUM_DIR, SCAN_MODEL
from utils import format_plenum_for_prompt, clean_to_json
from prompts import build_plenum_prompt
from backup import backup_plenums
from clients import safe_api_call


def scan_plenums(kazus: str, client) -> list:
    print(f"\n{'=' * 60}")
    print("📚 AGENT: PLENUMLAR — HAR BIR MAVZU TO'LIQ")
    print(f"{'=' * 60}")

    plenum_dirs = sorted([
        d for d in os.listdir(PLENUM_DIR)
        if os.path.isdir(os.path.join(PLENUM_DIR, d))
    ])
    total = len(plenum_dirs)
    collected = []
    print(f"   Jami: {total} ta plenum mavzusi")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}")

    for idx, plenum_dir in enumerate(plenum_dirs, 1):
        meta, plenum_text = format_plenum_for_prompt(plenum_dir, PLENUM_DIR)
        if not meta or not plenum_text:
            print(f"  ⚪ [{idx}/{total}] {plenum_dir} — o'qib bo'lmadi")
            continue

        bandlar_soni = meta.get("bandlar_soni", "?")
        print(f"\n  📖 [{idx}/{total}] {meta.get('raqami', plenum_dir)} — {bandlar_soni} band")

        prompt = build_plenum_prompt(kazus, plenum_text)
        time.sleep(0.5)
        raw_text = safe_api_call(
            client, prompt, model=SCAN_MODEL, provider_name=f"PLENUM-{idx}"
        )
        if raw_text is None:
            print(f"  ❌ [{idx}/{total}] API xato, o'tkazib yuborildi")
            continue

        try:
            res_json = json.loads(clean_to_json(raw_text))
            aloqadorlik = res_json.get("kazusga_aloqadorlik", "")
            tegishli_bandlar = res_json.get("tegishli_bandlar", [])

            plenum_record = {
                "mavzu_dir": plenum_dir,
                "qaror_nomi": meta.get("qaror_nomi", ""),
                "raqami": meta.get("raqami", ""),
                "sana": meta.get("sana", ""),
                "manba": meta.get("manba", ""),
                "kazusga_aloqadorlik": aloqadorlik,
                "tegishli_bandlar": tegishli_bandlar,
                "bogliq_jk_moddalar": res_json.get("bogliq_jk_moddalar", res_json.get("bog'liq_jk_moddalar", [])),
                "bogliq_jpk_moddalar": res_json.get("bogliq_jpk_moddalar", res_json.get("bog'liq_jpk_moddalar", [])),
                "tahlil": res_json.get("tahlil", ""),
            }
            collected.append(plenum_record)

            if tegishli_bandlar:
                band_raqamlar = [b.get("band_raqami", "?") for b in tegishli_bandlar]
                print(f"  ✅ [{idx}/{total}] {len(tegishli_bandlar)} band: [{', '.join(band_raqamlar)}]")
            else:
                print(f"  ⚪ [{idx}/{total}] Kazusga aloqador band topilmadi")
        except Exception as e:
            print(f"  ❌ [{idx}/{total}] Xato: {e}")

        if idx % 5 == 0:
            backup_plenums(collected)

    backup_plenums(collected)
    aloqador = [p for p in collected if p.get("tegishli_bandlar")]
    print(f"\n   📊 PLENUMLAR: {len(collected)} ta o'qildi, {len(aloqador)} ta kazusga aloqador")
    print(f"   Plenumlar tugadi: {time.strftime('%H:%M:%S')}")
    return collected
