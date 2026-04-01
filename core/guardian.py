import time
from fastapi import Request, HTTPException
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# ProtoQol Guardian — Anti-Spam & Rate Limiting System
# ═══════════════════════════════════════════════════════════════

# In-memory storage for IP request tracking
# { ip: [timestamp1, timestamp2, ...] }
_request_history = defaultdict(list)

# Configuration (Demo Mode: High Capacity)
LIMIT_REQUESTS = 100
LIMIT_WINDOW_SECONDS = 60

async def rate_limit_check(request: Request):
    """
    Simple IP-based rate limiter to protect Gemini/Solana budget.
    Threshold: 3 requests per 60 seconds per IP.
    """
    client_ip = request.client.host
    now = time.time()
    
    # 1. Clean up old timestamps
    _request_history[client_ip] = [ts for ts in _request_history[client_ip] if now - ts < LIMIT_WINDOW_SECONDS]
    
    # 2. Check threshold
    if len(_request_history[client_ip]) >= LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429, 
            detail="Protocol is cooling down. Please wait before next verification."
        )
    
    # 3. Log request
    _request_history[client_ip].append(now)
    return True
