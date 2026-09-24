import os
import glob
import json
import time
from config import (
    BATCH_SIZE,
    JPK_DIR,
    JPK_BASE_URL,
    SCAN_MODEL,
)
from utils import (
    load_json_file,
    natural_sort_key,
    format_modda_for_prompt,
    extract_element_id,
    clean_to_json,
    modda_id_key,
    modda_match_keys,
    batch_modda_ids,
)
from prompts import build_scan_prompt
from safety_net import apply_safety_net
from backup import backup_jpk
from clients import safe_api_call


def scan_jpk(kazus: str, client) -> list:
    print(f"\n{'=' * 60}")
    print("📚 AGENT: JPK TAHLILI")
    print(f"{'=' * 60}")

    all_files = sorted(glob.glob(os.path.join(JPK_DIR, "modda_*.json")), key=natural_sort_key)
    total_files = len(all_files)
    total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE
    collected = []

    print(f"   Jami: {total_files} modda, {total_batches} batch")
    print(f"   Boshlandi: {time.strftime('%H:%M:%S')}")

    for batch_idx in range(0, total_files, BATCH_SIZE):
        batch_files = all_files[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        batch_moddalar = []
        for fp in batch_files:
            try:
                batch_moddalar.append(load_json_file(fp))
            except Exception as e:
                print(f"  ❌ {os.path.basename(fp)}: {e}")

        if not batch_moddalar:
            continue

        batch_text = "\n".join(format_modda_for_prompt(m) for m in batch_moddalar)
        valid_batch_ids = batch_modda_ids(batch_files, batch_moddalar)
        prompt = build_scan_prompt(kazus, batch_text, batch_num, total_batches, "JPK")

        time.sleep(0.5)
        raw_text = safe_api_call(
            client, prompt, model=SCAN_MODEL, provider_name=f"JPK-{batch_num}"
        )
        if raw_text is None:
            print(f"  ❌ [JPK {batch_num}/{total_batches}] API xato, o'tkazib yuborildi")
            continue

        try:
            res = json.loads(clean_to_json(raw_text))
            items = res.get("relevant_moddalar", [])
            valid_items = _filter_items(items, valid_batch_ids, batch_moddalar, collected)
            if valid_items:
                nums = ", ".join(str(i["modda_raqami"]) for i in valid_items)
                print(f"  ✅ [JPK {batch_num}/{total_batches}] → {len(valid_items)}: [{nums}]")
            else:
                print(f"  ⚪ [JPK {batch_num}/{total_batches}] → Yo'q")
        except Exception as e:
            print(f"  ❌ [JPK {batch_num}/{total_batches}] Xato: {e}")

        if batch_num % 20 == 0:
            backup_jpk(collected)

    apply_safety_net(kazus, collected, JPK_DIR, JPK_BASE_URL, "JPK")
    backup_jpk(collected)
    print(f"\n   📊 JPK: {len(collected)} ta modda topildi")
    print(f"   JPK tugadi: {time.strftime('%H:%M:%S')}")
    return collected


def _filter_items(items, valid_ids, batch_moddalar, collected):
    seen = {modda_id_key(i.get("modda_raqami")) for i in collected}
    result = []
    for item in items:
        mr_raw = item.get("modda_raqami")
        ms = item.get("modda_sarlavhasi")
        if mr_raw is None or ms is None:
            continue
        mr_keys = modda_match_keys(mr_raw)
        if not mr_keys or not (mr_keys & valid_ids):
            continue
        mr = modda_id_key(mr_raw)
        if mr in seen or (mr_keys & seen):
            continue
        seen |= mr_keys
        seen.add(mr)
        element_id = item.get("element_id", "")
        if not element_id:
            for md in batch_moddalar:
                if modda_match_keys(md.get("n")) & mr_keys:
                    element_id = extract_element_id(md.get("sarlavha_id", ""))
                    break
        lex_link = f"{JPK_BASE_URL}#{element_id}" if element_id else JPK_BASE_URL
        collected.append({
            "manba": "JPK",
            "modda_raqami": mr,
            "modda_sarlavhasi": ms,
            "element_id": element_id,
            "lex_url": lex_link,
            "qism_yoki_band": item.get("qism_yoki_band", ""),
            "kazusdagi_holat": item.get("kazusdagi_holat", ""),
            "qonuniy_asos": item.get("qonuniy_asos", ""),
        })
        result.append(item)
    return result
