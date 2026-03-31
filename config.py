"""
═══════════════════════════════════════════════════════════════
ProtoQol — Legacy Configuration Bridge
[DEPRECATION NOTICE] Please migrate to core.config
═══════════════════════════════════════════════════════════════
"""

from core.config import *
import logging

# Retro-compatibility aliases for legacy Qaiyrym naming
ACTIVE_MISSIONS = SERVICE_STATIC_CAMPAIGNS
VALID_API_KEYS = PROTOCOL_API_WHITELIST
MASTER_BIY = MASTER_AUTHORITY_KEY
WALLET_SALT = NOMAD_WALLET_SALT
get_next_gemini_key = get_next_engine_api_key

logging.getLogger("PROTOCOL_ENGINE").warning(
    "⚠️  LEGACY_IMPORT: A module is still importing 'api/config.py'. "
    "Please update to 'from core.config import ...'"
)
