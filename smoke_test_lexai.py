import sys
import os
import glob

os.chdir(r"C:\proyekt\huquqiy_agent")
sys.path.insert(0, r"C:\proyekt\huquqiy_agent\lexai")

from main import run_pipeline
from pipeline import run_pipeline as rp2
from config import ROOT, BATCH_SIZE, BATCH_TAG, SCAN_MODEL, IRAC_MODEL, JK_DIR, JPK_DIR, PLENUM_DIR
from clients import get_openrouter_client, safe_api_call
from kazus import get_kazus
from utils import select_agents, natural_sort_key, modda_id_key, batch_modda_ids, load_json_file
from prompts import build_scan_prompt, build_plenum_prompt, build_irac_prompt
from safety_net import apply_safety_net
from backup import backup_jk, backup_jpk, backup_plenums
from irac import generate_irac, _format_jk, _format_jpk, _format_plenums
from scanners.jk import scan_jk, _filter_items as jk_filter
from scanners.jpk import scan_jpk, _filter_items as jpk_filter
from scanners.plenum import scan_plenums

assert ROOT.exists()
assert os.path.isdir(JK_DIR) and os.path.isdir(JPK_DIR) and os.path.isdir(PLENUM_DIR)
assert BATCH_SIZE == 5
assert len(get_kazus()) > 100
print("1 IMPORTS OK")
print("   ROOT", ROOT)
print("   BATCH", BATCH_SIZE, BATCH_TAG)
print("   MODELS", SCAN_MODEL, "|", IRAC_MODEL)

client = get_openrouter_client()
print("2 CLIENT OK", type(client).__name__)

p = build_scan_prompt(get_kazus(), "modda", 1, 10, "JPK")
assert "OQIBAT" in p and "relevant_moddalar" in p
pjk = build_scan_prompt(get_kazus(), "modda", 1, 10, "JK")
assert "buzilganmi" in pjk
pp = build_plenum_prompt(get_kazus(), "plenum")
assert "tegishli_bandlar" in pp
pi = build_irac_prompt("k", "j", "j", "p")
assert "IRAC" in pi
print("3 PROMPTS OK")

files = sorted(glob.glob(os.path.join(JPK_DIR, "modda_*.json")), key=natural_sort_key)
b1 = [os.path.basename(f) for f in files[:5]]
assert b1 == ["modda_1.json", "modda_2.json", "modda_3.json", "modda_4.json", "modda_11.json"], b1
jk_files = sorted(glob.glob(os.path.join(JK_DIR, "modda_*.json")), key=natural_sort_key)
assert len(jk_files) == 411
assert [os.path.basename(f) for f in jk_files[:5]] == [f"modda_{i}.json" for i in range(1, 6)]
print("4 SORT OK JPK", b1)
print("   JK", len(jk_files), "files")

# sub-modda filter
b95 = [f for f in files if os.path.basename(f) in ("modda_95.json", "modda_95-1.json")]
m95 = [load_json_file(f) for f in b95]
vids = batch_modda_ids(b95, m95)
c = []
jpk_filter(
    [
        {"modda_raqami": 95, "modda_sarlavhasi": "A"},
        {"modda_raqami": "95-1", "modda_sarlavhasi": "B"},
        {"modda_raqami": 99999, "modda_sarlavhasi": "X"},
    ],
    vids,
    m95,
    c,
)
got = [x["modda_raqami"] for x in c]
assert "95" in got and "95-1" in got and "99999" not in got
print("5 FILTER OK", got)

col = [{"modda_raqami": "50"}]
apply_safety_net(get_kazus(), col, JPK_DIR, "https://lex.uz/docs/-111460", "JPK")
assert sum(1 for x in col if str(x.get("modda_raqami")) == "50") == 1
assert len(col) > 10
print("6 SAFETY_NET OK", len(col), "items")

# IRAC formatter
jk_sample = [{"modda_raqami": "83", "modda_sarlavhasi": "s", "qism_yoki_band": "", "kazusdagi_holat": "", "qonuniy_asos": "", "buzilganmi": True, "lex_url": "x"}]
jpk_sample = [{"modda_raqami": "95", "modda_sarlavhasi": "s", "qism_yoki_band": "", "kazusdagi_holat": "", "qonuniy_asos": "", "lex_url": "x"}]
pl_sample = [{"raqami": "17-son", "qaror_nomi": "n", "manba": "m", "tegishli_bandlar": [{"band_raqami": "16"}], "kazusga_aloqadorlik": "a", "tahlil": "t"}]
assert "JK 83" in _format_jk(jk_sample)
assert "JPK 95" in _format_jpk(jpk_sample)
assert "PLENUM" in _format_plenums(pl_sample)
assert _format_plenums([{"tegishli_bandlar": []}]) == ""
print("7 IRAC FORMAT OK")

# backup yozish (xavfsiz: batch5 nomi ostida eski faylga tegmaymiz — tmp)
import backup as bak
from config import ROOT as R
import json
tmp_list = [{"modda_raqami": "1"}]
# backup_plenums chaqirib ko'ramiz (yangi fayl)
backup_plenums(tmp_list)
assert (R / f"plenums_backup_{BATCH_TAG}.json").exists()
print("8 BACKUP OK", f"plenums_backup_{BATCH_TAG}.json")

# bitta real API (kichik)
raw = safe_api_call(client, "Faqat JSON: " + '{"status":"ok"}', provider_name="SMOKE", max_retries=2)
print("9 API", "OK" if raw else "FAIL", repr(raw)[:80] if raw else None)
assert raw is not None

# main.py kiritish
import importlib.util
spec = importlib.util.spec_from_file_location("lexai_main", r"C:\proyekt\huquqiy_agent\lexai\main.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert hasattr(mod, "run_pipeline")
print("10 main.py LOAD OK")

print()
print("=== SMOKE TEST PASSED ===")
