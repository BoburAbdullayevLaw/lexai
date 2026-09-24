import json
import threading
from config import BATCH_TAG, ROOT

JK_LOCK = threading.Lock()
JPK_LOCK = threading.Lock()
PLENUM_LOCK = threading.Lock()


def backup_jk(collected):
    with JK_LOCK:
        with open(ROOT / f"jk_backup_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
            json.dump(collected, f, ensure_ascii=False, indent=2)


def backup_jpk(collected):
    with JPK_LOCK:
        with open(ROOT / f"jpk_backup_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
            json.dump(collected, f, ensure_ascii=False, indent=2)


def backup_plenums(collected):
    with PLENUM_LOCK:
        with open(ROOT / f"plenums_backup_{BATCH_TAG}.json", "w", encoding="utf-8") as f:
            json.dump(collected, f, ensure_ascii=False, indent=2)
