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
# 📦 PROTOCOL SIMULATION ENGINE (Enable for unstable network conditions/demos)
SIMULATION_MODE = False
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
PROTOCOL_PROGRAM_ID = Pubkey.from_string("EdrjHLN9K9eogJ5Pui8WYJRAghdN4knAdAoDcZesAirc")
IDL_PATH = os.path.join(os.path.dirname(__file__), "../protoqol_core/target/idl/protoqol_core_compat.json")

# Master Authority (PDA-based)
MASTER_AUTHORITY_SEED = os.getenv("MASTER_AUTHORITY_SECRET", "protoqol_master_engine_authority_2026")
authority_seed_bytes = hashlib.sha256(MASTER_AUTHORITY_SEED.encode()).digest()
MASTER_AUTHORITY_KEY = Keypair.from_seed(authority_seed_bytes)

# ═══════════════════════════════════════════════════════════════
# MULTI-AGENT AI CONSENSUS
# ═══════════════════════════════════════════════════════════════

class KeyManager:
    """Manages pool of Gemini API keys with Round-Robin selection."""
    def __init__(self):
        self.raw_keys = os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", ""))
        self.pool = [k.strip() for k in self.raw_keys.split(",") if k.strip()]
        self._index = 0
        
    def get_key(self) -> str | None:
        if not self.pool:
            return None
        key = self.pool[self._index % len(self.pool)]
        self._index += 1
        return key
    
    def get_pool_size(self) -> int:
        return len(self.pool)

# Global Instance for the Engine
ai_keys = KeyManager()

def get_next_engine_api_key():
    return ai_keys.get_key()


AI_TIMEOUT = 12.0

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
    },
    "eco_cleanup_aktobe": {
        "client": "Eco Foundation",
        "foundation_id": "ECO_AKTOBE",
        "theme_accent": "#00FFA3",
        "requirements": "Community waste collection and impact assessment.",
        "status": "active",
        "impact_weight": 1.1,
    }
}
