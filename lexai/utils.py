import os
import re
import glob
import json

_SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def clean_to_json(text_content: str) -> str:
    text_content = text_content.strip()
    if "```json" in text_content:
        text_content = text_content.split("```json")[1].split("```")[0].strip()
    elif "```" in text_content:
        text_content = text_content.split("```")[1].split("```")[0].strip()
    return text_content


def natural_sort_key(path: str):
    name = os.path.basename(path).replace("-bob.json", "").replace(".json", "")
    nums = [int(n) for n in re.findall(r"\d+", name)]
    return nums if nums else [0]


def modda_id_key(value) -> str:
    """n yoki modda_raqami ni string kalitga aylantiradi.

    95 → "95", "95-1" → "95-1", "254¹⁰" → "25410"
    """
    if value is None:
        return ""
    return str(value).strip().translate(_SUPERSCRIPT_MAP)


def modda_match_keys(value) -> set:
    """Bitta modda uchun moslashuv kalitlari (superscript/hyphen uchun)."""
    key = modda_id_key(value)
    keys = {key} if key else set()
    compact = re.sub(r"[^0-9A-Za-z]+", "", key)
    if compact:
        keys.add(compact)
    return keys


def batch_modda_ids(batch_files, batch_moddalar) -> set:
    """Batch ichidagi barcha modda IDlari (fayl nomi + n maydoni)."""
    ids = set()
    for fp in batch_files:
        base = os.path.basename(fp)
        if base.startswith("modda_") and base.endswith(".json"):
            ids |= modda_match_keys(base[6:-5])
    for m in batch_moddalar:
        ids |= modda_match_keys(m.get("n"))
    ids.discard("")
    return ids


def load_json_file(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


def extract_element_id(sarlavha_id: str) -> str:
    if "#" in sarlavha_id:
        return sarlavha_id.split("#")[-1]
    return ""


def format_modda_for_prompt(modda_data: dict, include_sharh: bool = False) -> str:
    lines = []
    sarlavha = modda_data.get("sarlavha", f"{modda_data.get('n')}-modda")
    sarlavha_id = modda_data.get("sarlavha_id", "")
    id_qismi = f" (ID: {sarlavha_id})" if sarlavha_id else ""
    lines.append(f"\n{sarlavha}{id_qismi}")

    for qism in modda_data.get("qismlar", []):
        q_id = qism.get("id", "")
        id_tag = f" [ID:{q_id}]" if q_id else ""
        lines.append(f"  Qism {qism.get('q')}{id_tag}: {qism.get('matn', '')}")
        for band in qism.get("bandlar", []):
            b_id = band.get("id", "")
            id_tag = f" [ID:{b_id}]" if b_id else ""
            lines.append(f"    Band {band.get('b')}{id_tag}: {band.get('matn', '')}")

    if include_sharh:
        if "umumiy_sharh" in modda_data:
            sharh = modda_data["umumiy_sharh"]
            if isinstance(sharh, list) and sharh:
                lines.append("  UMUMIY SHARH:")
                for item in sharh[:3]:
                    lines.append(f"    {item}")
        if "sharh" in modda_data:
            sharh = modda_data["sharh"]
            lines.append("  SHARH:")
            if isinstance(sharh, list):
                for item in sharh[:5]:
                    lines.append(f"    {item}")
        for qism in modda_data.get("qismlar", []):
            if "sharh" in qism:
                q_sharh = qism["sharh"]
                if isinstance(q_sharh, list):
                    for item in q_sharh[:3]:
                        lines.append(f"    {item}")
            for band in qism.get("bandlar", []):
                if "sharh" in band:
                    b_sharh = band["sharh"]
                    if isinstance(b_sharh, list):
                        for item in b_sharh[:2]:
                            lines.append(f"    {item}")

    return "\n".join(lines)


def format_plenum_for_prompt(plenum_dir: str, plenum_root: str) -> tuple:
    plenum_path = os.path.join(plenum_root, plenum_dir)
    meta_path = os.path.join(plenum_path, "_plenum.json")
    if not os.path.exists(meta_path):
        return None, None
    meta = load_json_file(meta_path)
    mavzu_nomi = meta.get("qaror_nomi", plenum_dir)
    raqam = meta.get("raqami", "")
    manba = meta.get("manba", "")
    sana = meta.get("sana", "")
    lines = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"PLENUM: {mavzu_nomi}")
    lines.append(f"Raqami: {raqam} | Sana: {sana}")
    lines.append(f"Manba: {manba}")
    lines.append(f"{'=' * 60}")
    band_files = sorted(
        glob.glob(os.path.join(plenum_path, "band_*.json")),
        key=natural_sort_key,
    )
    for bf in band_files:
        try:
            band = load_json_file(bf)
            band_n = band.get("band_raqami", "")
            band_matn = band.get("matn", "")
            band_id = band.get("id", "")
            lines.append(f"\nBand {band_n} (ID: {band_id}):")
            lines.append(f"  {band_matn}")
            for xatbosh in band.get("xatboshilar", []):
                if xatbosh:
                    lines.append(f"  - {xatbosh}")
        except Exception:
            continue
    return meta, "\n".join(lines)


def select_agents() -> dict:
    print("\n" + "=" * 60)
    print("📋 QAYSI MANBALARNI SKANERLASH KERAK?")
    print("=" * 60)
    print("   1 - JK       (Jinoyat Kodeksi, ~411 modda)")
    print("   2 - JPK      (Jinoyat-Protsessual Kodeksi, ~764 modda)")
    print("   3 - PLENUM   (Oliy Sud Plenumlari, 43 mavzu)")
    print("-" * 60)
    print("   Misollar:  '2'  |  '2,3'  |  '1,2,3'")
    print("=" * 60)

    while True:
        choice = input("\n   Tanlovingiz: ").strip()
        selected = {"JK": False, "JPK": False, "PLENUM": False}
        valid = True
        for part in choice.split(","):
            part = part.strip()
            if part == "1":
                selected["JK"] = True
            elif part == "2":
                selected["JPK"] = True
            elif part == "3":
                selected["PLENUM"] = True
            elif part == "":
                continue
            else:
                print(f"   ❌ Noto'g'ri: '{part}'. Faqat 1, 2, 3.")
                valid = False
                break
        if valid and any(selected.values()):
            return selected
        if valid:
            print("   ⚠️ Kamida bitta manba tanlanishi kerak.")
