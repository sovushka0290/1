from fastapi import Header, HTTPException, Depends
from core.database import get_db_connection, check_client_credits

async def get_api_key(x_api_key: str = Header(...)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is missing.")
    
    conn = get_db_connection()
    client = conn.execute("SELECT * FROM clients WHERE api_key = ?", (x_api_key,)).fetchone()
    conn.close()
    
    if not client:
        raise HTTPException(status_code=403, detail="Invalid API Key. Unauthorized access.")
    
    return dict(client)

async def require_credits(client: dict = Depends(get_api_key)):
    """
    Dependency that enforces the credit quota.
    Returns 402 Payment Required if no credits left.
    """
    if not check_client_credits(client['id']):
        raise HTTPException(
            status_code=402, 
            detail={
                "error": "Quota Exhausted",
                "message": "You have reached your limit for the current billing period. Please upgrade your plan at protoqol.org/pricing",
                "plan": client.get('plan_type', 'Free')
            }
        )
    return client
