"""
═══════════════════════════════════════════════════════════════
ProtoQol — Custom Protocol Exception Hierarchy
Standardized Error Handling for Digital Biy Oracle
═══════════════════════════════════════════════════════════════
"""

class ProtocolError(Exception):
    """Base exception for all ProtoQol Engine errors."""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)

class BlockchainError(ProtocolError):
    """Raised when Solana RPC or Anchor program interactions fail."""
    def __init__(self, message: str, tx_hash: str = None):
        super().__init__(f"Blockchain Error: {message}", code=503)
        self.tx_hash = tx_hash

class AIConsensusError(ProtocolError):
    """Raised when Multi-agent Gemini consensus fails or is malformed."""
    def __init__(self, message: str, reasoning: str = None):
        super().__init__(f"AI Consensus Failed: {message}", code=503)
        self.reasoning = reasoning

class UnauthorizedAccessError(ProtocolError):
    """Raised when B2B API keys or signatures are invalid."""
    def __init__(self, message: str = "Invalid Protocol API Key"):
        super().__init__(message, code=401)

class DatabaseLockError(ProtocolError):
    """Raised during SQLite write contention despite WAL/Timeout."""
    def __init__(self, message: str = "Database Engine is currently busy"):
        super().__init__(message, code=503)
