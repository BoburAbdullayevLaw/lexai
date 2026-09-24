import os
import json
import glob
import time
import threading
from config import (
    SCAN_MODEL,
    IRAC_MODEL,
    BATCH_SIZE,
    BATCH_TAG,
    JK_DIR,
    JPK_DIR,
    PLENUM_DIR,
    ROOT,
)
from kazus import get_kazus
from utils import select_agents
from clients import get_openrouter_client
from scanners.jk import scan_jk
from scanners.jpk import scan_jpk
from scanners.plenum import scan_plenums
from irac import generate_irac
from backup import backup_jk, backup_jpk, backup_plenums


def run_pipeline():
    selected = select_agents()
    active = [k for k, v in selected.items() if v]

    print("=" * 60)
    print("🚀 LexAI — MODULAR PIPELINE")
    print("=" * 60)
    print(f"   Scan model:  {SCAN_MODEL}")
    print(f"   IRAC model:  {IRAC_MODEL}")
    print(f"   Batch size:  {BATCH_SIZE}")
    print(f"   Faol:        {', '.join(active)}")
    print(f"   Safety Net:  ✅")
    print("=" * 60)

    kazus = get_kazus()
    client = get_openrouter_client()
    start = time.time()

    collected_jk: list = []
    collected_jpk: list = []
    collected_plenums: list = []
    threads = []

    if selected["JK"]:
        t = threading.Thread(target=lambda: collected_jk.extend(scan_jk(kazus, client)))
        t.start()
        threads.append(t)

    if selected["JPK"]:
        def w_jpk():
            time.sleep(2)
            collected_jpk.extend(scan_jpk(kazus, client))
        t = threading.Thread(target=w_jpk)
        t.start()
        threads.append(t)

    if selected["PLENUM"]:
        def w_pl():
            time.sleep(4)
            collected_plenums.extend(scan_plenums(kazus, client))
        t = threading.Thread(target=w_pl)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    backup_jk(collected_jk)
    backup_jpk(collected_jpk)
    backup_plenums(collected_plenums)

    print(f"\n{'=' * 60}")
    print("📊 NATIJALAR:")
    print(f"   JK: {len(collected_jk)} | JPK: {len(collected_jpk)} | Plenum: {len(collected_plenums)}")

    if not collected_jk and not collected_jpk and not collected_plenums:
        print("⚠️ Hech narsa topilmadi.")
        return

    conclusion = generate_irac(
        kazus, collected_jk, collected_jpk, collected_plenums, client
    )
    print(conclusion)

    with open(ROOT / f"irac_final_{BATCH_TAG}.txt", "w", encoding="utf-8") as f:
        f.write(conclusion)
    with open(ROOT / f"jk_analysis_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
        json.dump(collected_jk, f, ensure_ascii=False, indent=2)
    with open(ROOT / f"jpk_analysis_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
        json.dump(collected_jpk, f, ensure_ascii=False, indent=2)
    with open(ROOT / f"plenums_analysis_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
        json.dump(collected_plenums, f, ensure_ascii=False, indent=2)

    full_data = {
        "batch_size": BATCH_SIZE,
        "selected_agents": selected,
        "kazus": kazus,
        "jk_moddalar": collected_jk,
        "jpk_moddalar": collected_jpk,
        "plenumlar": collected_plenums,
        "xulosa": conclusion,
    }
    with open(ROOT / f"lexai_v7_full_data_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    jk_count = len(glob.glob(os.path.join(JK_DIR, "modda_*.json")))
    jpk_count = len(glob.glob(os.path.join(JPK_DIR, "modda_*.json")))
    plenum_count = len([d for d in os.listdir(PLENUM_DIR) if os.path.isdir(os.path.join(PLENUM_DIR, d))])
    jk_batches = (jk_count + BATCH_SIZE - 1) // BATCH_SIZE
    jpk_batches = (jpk_count + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"\n{'=' * 60}")
    print("📊 HISOBOT:")
    print(f"{'=' * 60}")
    if selected["JK"]:
        print(f"   JK: {jk_count} modda → {jk_batches} batch")
    if selected["JPK"]:
        print(f"   JPK: {jpk_count} modda → {jpk_batches} batch")
    if selected["PLENUM"]:
        print(f"   Plenumlar: {plenum_count} mavzu → {plenum_count} so'rov")
    print(f"   Model: {SCAN_MODEL}")
    print(f"   IRAC: {IRAC_MODEL}")
    print(f"   Vaqt: {mins} daqiqa {secs} soniya")
    print(f"{'=' * 60}")

    print(f"\n💾 Saqlandi:")
    print(f"   • irac_final_{BATCH_TAG}.txt")
    print(f"   • jk_analysis_{BATCH_TAG}.json")
    print(f"   • jpk_analysis_{BATCH_TAG}.json")
    print(f"   • plenums_analysis_{BATCH_TAG}.json")
    print(f"   • lexai_v7_full_data_{BATCH_TAG}.json")
    print(f"\n✅ TUGADI")
