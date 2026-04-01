import time
import hashlib
import asyncio
from fastapi import APIRouter, Form, HTTPException, Depends, Request, BackgroundTasks
from solders.pubkey import Pubkey

from core.config import SERVICE_STATIC_CAMPAIGNS, MASTER_AUTHORITY_KEY, PROTOCOL_PROGRAM_ID, log
from core import ai_engine, solana_client, state, database, auth

router = APIRouter(prefix="/api/v1", tags=["B2B_Engine_Gateway"])


async def background_settlement(
    deed_id: str, 
    integrity_hash: str, 
    impact_score: int, 
    verdict: str,
    client_id: int
):
    """
    Lean Background Settlement: One AI decision = One Solana Transaction.
    Ensures high reliability and low latency for the hackathon.
    """
    try:
        log.info(f"[BACKGROUND_SETTLEMENT] Etching final verdict for: {deed_id}")
        
        # 1. Finalize on-chain with a single transaction
        tx_hash = await solana_client.etch_deed_on_chain(
            deed_id, integrity_hash, impact_score, verdict
        )
        
        if not tx_hash:
             log.error("[BACKGROUND_SETTLEMENT] Blockchain execution failed. Check Devnet status.")
             return

        # 2. Update Credit pool & Local Registry
        database.deduct_credit(client_id)
        
        conn = database.get_db_connection()
        conn.execute("UPDATE deeds SET tx_hash = ? WHERE integrity_hash = ?", (tx_hash, integrity_hash))
        conn.commit()
        conn.close()
        
        log.info(f"[BACKGROUND_SETTLEMENT] Successfully crystalized: {tx_hash}")
        
    except Exception as e:
        log.error(f"[BACKGROUND_SETTLEMENT] Critical Failure: {e}")


@router.post("/etch_deed")
async def enterprise_etch_deed(
    request: Request,
    background_tasks: BackgroundTasks,
    client: dict = Depends(auth.require_credits)
):
    """
    Enterprise Standard Endpoint for B2B Clients.
    Returns AI Verdict immediately; Settlement happens in Background.
    """
    # 1. INPUT RESOLUTION
    content_type = request.headers.get("Content-Type", "")
    form_data = await request.form()
    json_data = {}
    
    if "application/json" in content_type:
        try: json_data = await request.json()
        except: pass

    data = {**form_data, **json_data}
    description = data.get("description")
    nomad_id = data.get("nomad_id", "Anonymous")
    mission_id = data.get("mission_id")
    source = data.get("source", "B2B Gateway")
    
    # Meta for AI Filters
    lat = data.get("lat")
    lon = data.get("lon")
    ts = data.get("timestamp")

    if not description or not mission_id:
        raise HTTPException(status_code=422, detail="Missing required data: description and mission_id.")

    mission_info = SERVICE_STATIC_CAMPAIGNS.get(mission_id)
    if not mission_info:
        raise HTTPException(status_code=400, detail="Unknown Protocol mandate.")

    # 2. AI CONSENSUS (Multi-Agent Neural Audit)
    log.info(f"[B2B_GATEWAY] Neural Audit started for client: {client['name']}")
    ai_res = await ai_engine.analyze_deed(
        description, mission_info, campaign_id=None, meta={"lat": lat, "lon": lon, "timestamp": ts}
    )
    
    verdict = ai_res.get("verdict", "ARAM")
    points = int(float(ai_res.get("impact_score", 0)) * 100) if verdict == "ADAL" else 0
    wisdom = ai_res.get("wisdom", "Justice is the path.")
    agent_verdicts = ai_res.get("consensus_logs", [])

    # 3. PRE-SETTLEMENT
    integrity_hash = hashlib.sha256(f"{description}|{nomad_id}|{time.time()}".encode()).hexdigest()[:16]
    deed_id = f"B2B_{int(time.time()*1000)}"
    user_kp = solana_client.get_nomad_wallet(nomad_id)

    # 4. PERSISTENCE (Initial state)
    conn = database.get_db_connection()
    conn.execute(
        "INSERT INTO deeds (client_id, nomad_id, mission_id, verdict, impact_points, tx_hash, integrity_hash, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (client['id'], nomad_id, mission_id, verdict, points, "PROCESSING", integrity_hash, source)
    )
    conn.commit()
    conn.close()


    # 5. OFFLOAD HEAVY TASKS TO BACKGROUND
    if verdict == "ADAL":
        background_tasks.add_task(
            background_settlement,
            deed_id, integrity_hash, points, verdict, client['id']
        )


    return {
        "status": "crystalizing" if verdict == "ADAL" else "denied",
        "verdict": verdict,
        "tx_hash": "CRYSTAL_PENDING",
        "integrity_hash": integrity_hash,
        "impact_points": points,
        "wisdom": wisdom,
        "ai_dialogue": agent_verdicts
    }

@router.get("/dashboard/stats")
async def get_client_stats(client: dict = Depends(auth.get_api_key)):
    conn = database.get_db_connection()
    stats = conn.execute(
        "SELECT COUNT(*) as total_deeds, SUM(impact_points) as total_points FROM deeds WHERE client_id = ?",
        (client['id'],)
    ).fetchone()
    
    recent = conn.execute(
        "SELECT tx_hash, verdict, impact_points, timestamp, source FROM deeds WHERE client_id = ? ORDER BY id DESC LIMIT 10",
        (client['id'],)
    ).fetchall()
    conn.close()
    
    return {
        "client_name": client['name'],
        "total_impact": stats['total_points'] or 0,
        "total_verifications": stats['total_deeds'] or 0,
        "recent_activity": [dict(r) for r in recent]
    }

@router.get("/gateway/missions")
async def get_all_missions():
    missions = {**SERVICE_STATIC_CAMPAIGNS}
    conn = database.get_db_connection()
    campaigns = conn.execute("SELECT * FROM campaigns WHERE is_active = 1").fetchall()
    conn.close()
    for c in campaigns:
        missions[f"db_camp_{c['id']}"] = {
            "client": c['fund_name'],
            "requirements": c['requirements'],
            "theme_accent": "#8B5CF6",
            "title": c['title']
        }
    return missions

@router.get("/generate_mock_scenario")
async def get_mock_scenario():
    """AI-powered generator for high-fidelity demo scenarios."""
    scenario = await ai_engine.generate_scenario()
    return scenario
