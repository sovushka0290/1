import os
import hashlib
import logging
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey

# Modular Boot Sequence
load_dotenv()

# ═══════════════════════════════════════════════════════════════
# ENGINE CONFIGURATION (ProtoQol Engine)
# ═══════════════════════════════════════════════════════════════

# Master Registry
VERSION = "3.8.5"
ENGINE_NAME = "ProtoQol Decentralized Integrity Engine"

# Persistence Layer settings
DB_PATH = os.path.join(os.path.dirname(__file__), "../protoqol_mvp.db")
DB_WAL_MODE = True
DB_TIMEOUT = 20.0

# ═══════════════════════════════════════════════════════════════
# LOGGING SYSTEM
# ═══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("PROTOCOL_ENGINE")

# ═══════════════════════════════════════════════════════════════
# SOLANA BLOCKCHAIN ADAPTER
# ═══════════════════════════════════════════════════════════════
RPC_URL = os.getenv("RPC_URL", "https://api.devnet.solana.com")
PROTOCOL_PROGRAM_ID = Pubkey.from_string("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS")
IDL_PATH = os.path.join(os.path.dirname(__file__), "../protoqol_core/target/idl/protoqol_core.json")

# Master Authority (PDA-based)
MASTER_AUTHORITY_SEED = os.getenv("MASTER_AUTHORITY_SECRET", "protoqol_master_engine_authority_2026")
authority_seed_bytes = hashlib.sha256(MASTER_AUTHORITY_SEED.encode()).digest()
MASTER_AUTHORITY_KEY = Keypair.from_seed(authority_seed_bytes)

# ═══════════════════════════════════════════════════════════════
# MULTI-AGENT AI CONSENSUS
# ═══════════════════════════════════════════════════════════════
RAW_KEYS = os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", ""))
PROTOCOL_AI_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]
AI_TIMEOUT = 12.0
_KEY_INDEX = 0

def get_next_engine_api_key():
    global _KEY_INDEX
    if not PROTOCOL_AI_KEYS:
        return None
    key = PROTOCOL_AI_KEYS[_KEY_INDEX % len(PROTOCOL_AI_KEYS)]
    _KEY_INDEX += 1
    return key

# ═══════════════════════════════════════════════════════════════
# SECURITY & AUTH
# ═══════════════════════════════════════════════════════════════
NOMAD_WALLET_SALT = os.getenv("WALLET_SALT", "protoqol_engine_standard_salt_2026")
PROTOCOL_API_WHITELIST = {"PQ_DEV_TEST_2026", "PLATFORM_ADMIN_SECRET", "PQ_LIVE_DEMO_SECRET"}

# ═══════════════════════════════════════════════════════════════
# SERVICE ADAPTERS (e.g., Qaiyrym)
# ═══════════════════════════════════════════════════════════════
SERVICE_STATIC_CAMPAIGNS = {
    "elders_aktobe": {
        "client": "Ak-Niyet Foundation",
        "foundation_id": "AK_NIYET",
        "theme_accent": "#FFD700",
        "requirements": "Delivery for senior citizens. Photo/desc required.",
        "status": "active",
        "impact_weight": 1.2,
    },
    "eco_asar": {
        "client": "Aqtobe IT-Hub",
        "foundation_id": "AQTOBE_HUB",
        "theme_accent": "#64FFDA",
        "requirements": "Cleaning public spaces. Desc/Video proof required.",
        "status": "active",
        "impact_weight": 1.0,
    }
}
