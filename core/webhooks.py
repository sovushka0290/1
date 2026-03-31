import httpx
from core.config import log

async def fire_webhook(url: str, payload: dict):
    """
    Sends an asynchronous POST notification to a B2B partner's endpoint.
    Includes deed verdict and transaction metadata.
    """
    if not url:
        return
        
    try:
        async with httpx.AsyncClient() as client:
            # We use a 5-second timeout for the demo to prevent blocking the worker
            response = await client.post(url, json=payload, timeout=5.0)
            log.info(f"[WEBHOOK] Dispatch Successful to {url} | Status: {response.status_code}")
    except Exception as e:
        log.error(f"[WEBHOOK] Delivery Failed for {url}: {str(e)}")
