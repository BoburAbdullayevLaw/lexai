import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
TOKENHARBOR_KEY = os.environ.get("TOKENHARBOR_API_KEY")
TOKENHARBOR_BASE = os.environ.get("TOKENHARBOR_BASE_URL", "https://tokenharbor.ai/v1")
BYNARA_KEY = os.environ.get("BYNARA_API_KEY")
BYNARA_BASE = os.environ.get("BYNARA_BASE_URL", "https://router.bynara.id/v1")

SCAN_MODEL = "deepseek/deepseek-v4-flash"
IRAC_MODEL = "deepseek/deepseek-v4-pro"

BATCH_SIZE = 5
BATCH_TAG = f"batch{BATCH_SIZE}"

JK_DOC_ID = "-111453"
JPK_DOC_ID = "-111460"
JK_BASE_URL = f"https://lex.uz/docs/{JK_DOC_ID}"
JPK_BASE_URL = f"https://lex.uz/docs/{JPK_DOC_ID}"

JK_DIR = str(ROOT / "data/jinoyat/kodekslar/jk")
JPK_DIR = str(ROOT / "data/jinoyat/kodekslar/jpk")
PLENUM_DIR = str(ROOT / "data/jinoyat/plenumlar")

EXTRA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "HTTP-Referer": "https://lexai.uz",
    "X-Title": "LexAI Legal Analysis",
}
