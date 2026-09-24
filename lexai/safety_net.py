import os
from utils import load_json_file, extract_element_id, modda_id_key, modda_match_keys

SAFETY_NET_KEYWORDS_JPK = {
    "himoyachi": [50, 51, 52, 53],
    "advokat": [53, 115],
    "voz kech": [52],
    "dalil": [88, 95],
    "qo'rqit": [17, 22, 116, 117],
    "qo'rqitish": [17, 22, 116, 117],
    "qiynoq": [17, 22, 95],
    "ushlab tur": [221, 224, 225, 230],
    "ushlash": [221, 224, 225, 230],
    "reabilitatsiya": [301, 302, 304, 305, 306, 307],
    "oqlov": [301, 464, 470],
    "so'roq": [88, 95, 108, 114],
    "prokuror": [33, 34, 219],
    "hibsxona": [215, 225, 230],
    "kompensatsiya": [304, 305, 306, 307, 312],
    "ish haqi": [304, 305, 306],
    "pora": [140, 141, 203, 205, 206, 207],
    "qonuniylik": [11],
    "ma'naviy zarar": [301, 302, 304],
    "fuqaroviy da'vo": [276, 277, 280, 281, 283],
}

SAFETY_NET_KEYWORDS_JK = {
    "pora": [210, 211, 212],
    "oqlov": [83],
    "reabilitatsiya": [83],
    "qasddan odam": [97],
    "o'g'rilik": [169],
    "firibgarlik": [168],
}


def apply_safety_net(kazus, collected_list, source_dir, base_url, manba="JPK"):
    existing_ids = set()
    for item in collected_list:
        existing_ids |= modda_match_keys(item.get("modda_raqami"))
    added = []
    keywords = SAFETY_NET_KEYWORDS_JPK if manba == "JPK" else SAFETY_NET_KEYWORDS_JK
    kazus_lower = kazus.lower()

    for keyword, moddalar in keywords.items():
        if keyword.lower() in kazus_lower:
            for modda_n in moddalar:
                modda_keys = modda_match_keys(modda_n)
                if not (modda_keys & existing_ids):
                    file_path = os.path.join(source_dir, f"modda_{modda_n}.json")
                    if os.path.exists(file_path):
                        try:
                            modda_data = load_json_file(file_path)
                            sarlavha = modda_data.get("sarlavha", f"{modda_n}-modda")
                            element_id = extract_element_id(modda_data.get("sarlavha_id", ""))
                            lex_link = f"{base_url}#{element_id}" if element_id else base_url
                            collected_list.append({
                                "manba": manba,
                                "modda_raqami": modda_id_key(modda_n),
                                "modda_sarlavhasi": sarlavha,
                                "element_id": element_id,
                                "lex_url": lex_link,
                                "qism_yoki_band": "Safety Net",
                                "kazusdagi_holat": (
                                    f"Kazusda '{keyword}' tushunchasi mavjud. "
                                    f"Bu modda kritik ahamiyatga ega."
                                ),
                                "qonuniy_asos": f"{manba} {modda_n}-modda: {sarlavha}",
                                "safety_net": True,
                            })
                            existing_ids |= modda_keys
                            added.append(modda_n)
                        except Exception as e:
                            print(f"  ⚠️ Safety Net: {modda_n} o'qilmadi: {e}")

    if added:
        print(f"  🛡️ Safety Net [{manba}]: {len(added)} ta → {added}")
    return collected_list
