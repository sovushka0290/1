import time
import hashlib
import asyncio
import json
from fastapi import APIRouter, Form, HTTPException, Depends, Request, BackgroundTasks
from solders.pubkey import Pubkey

from core.config import SERVICE_STATIC_CAMPAIGNS, MASTER_AUTHORITY_KEY, PROTOCOL_PROGRAM_ID, log
from core import ai_engine, solana_client, state, database, auth

router = APIRouter(prefix="/api/v1", tags=["B2B_Engine_Gateway"])

async def background_settlement(
    deed_id: str, 
    nomad_pubkey: Pubkey, 
    mission_id: str, 
    reward_amount: int, 
    ai_full_res: dict, 
    client_id: int,
    integrity_hash: str
):
    """Handles heavy blockchain operations in the background to ensure fast UX."""
    try:
        log.info(f"[BACKGROUND_SETTLEMENT] Crystalizing {deed_id} in Solana...")
        
        # 1. Propose Deed on-chain (Correct Order)
        # Signature: (deed_id, nomad_pubkey, proposer_kp, mission_id, evidence_hash, reward_amount)
        tx_hash = await solana_client.propose_deed_on_chain(
            deed_id, 
            nomad_pubkey, 
            MASTER_AUTHORITY_KEY, 
            mission_id, 
            integrity_hash, 
            reward_amount
        )
        
        # 2. Submit Specialist Agent Votes
        votes = [
            ("AUDITOR", ai_full_res.get("auditor_report", {}).get("status") == "PASS"),
            ("SKEPTIC", ai_full_res.get("skeptic_report", {}).get("verdict") == "CLEAN"),
            ("SOCIAL_BIY", ai_full_res.get("master_consensus", {}).get("verdict") == "ADAL")
        ]
        
        for agent_name, is_adal in votes:
            try:
                await solana_client.vote_deed_on_chain(
                    deed_id, agent_name, is_adal, 
                    nomad_pubkey, MASTER_AUTHORITY_KEY.pubkey()
                )
            except Exception as ve:
                log.warning(f"Node {agent_name} voting failed: {ve}")
        
        # 3. Finalize locally
        database.deduct_credit(client_id)
        
        # 4. Update TX Hash in DB
        conn = database.get_db_connection()
        conn.execute("UPDATE deeds SET tx_hash = ? WHERE integrity_hash = ?", (tx_hash, integrity_hash))
        conn.commit()
        conn.close()
        
        log.info(f"[BACKGROUND_SETTLEMENT] ✓ Successfully crystalized: {tx_hash}")
        
    except Exception as e:
        log.error(f"[BACKGROUND_SETTLEMENT] Critical Failure: {e}")

@router.post("/etch_deed")
async def enterprise_etch_deed(
    request: Request,
    background_tasks: BackgroundTasks,
    client: dict = Depends(auth.require_credits)
):
    content_type = request.headers.get("Content-Type", "")
    form_data = await request.form()
    json_data = {}
    
    if "application/json" in content_type:
        try: json_data = await request.json()
        except: pass

    data = {**form_data, **json_data}
    description = data.get("description")
    nomad_id = data.get("nomad_id", "KASE_USER")
    mission_id = data.get("mission_id")
    source = data.get("source", "B2B Gateway")
    
    lat = data.get("lat")
    lon = data.get("lon")
    ts = data.get("timestamp")

    if not description or not mission_id:
        raise HTTPException(status_code=422, detail="Missing required data.")

    mission_info = SERVICE_STATIC_CAMPAIGNS.get(mission_id)
    if not mission_info:
        mission_info = {"client": "External Client", "foundation_id": "UNKNOWN"}

    # AI Consensus
    ai_res = await ai_engine.analyze_deed(
        description, mission_info, meta={"lat": lat, "lon": lon, "timestamp": ts}
    )
    
    master = ai_res.get("master_consensus", {})
    verdict = master.get("verdict", "ARAM")
    reward = int(float(ai_res.get("social_report", {}).get("asar_score", 0.5)) * 1000) # In base units
    wisdom = ai_res.get("social_report", {}).get("wisdom", "Justice is the path.")
    
    integrity_hash = ai_res.get("integrity_hash") or hashlib.sha256(f"{description}|{time.time()}".encode()).hexdigest()
    deed_id = f"B2B_{int(time.time()*1000)}"
    user_kp = solana_client.get_nomad_wallet(nomad_id)

    # DB Persistence
    ai_logs_json = json.dumps(ai_res)
    conn = database.get_db_connection()
    conn.execute(
        "INSERT INTO deeds (client_id, nomad_id, mission_id, verdict, impact_points, tx_hash, integrity_hash, source, ai_dialogue, wisdom) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (client['id'], nomad_id, mission_id, verdict, reward, "PROCESSING", integrity_hash, source, ai_logs_json, wisdom)
    )
    conn.commit()
    conn.close()

    # Offload to Solana
    if verdict == "ADAL":
        background_tasks.add_task(
            background_settlement,
            deed_id, user_kp.pubkey(), mission_id, reward, ai_res, client['id'], integrity_hash
        )

    return {
        "status": "crystalizing" if verdict == "ADAL" else "denied",
        "verdict": verdict,
        "tx_hash": "PROCESSING",
        "integrity_hash": integrity_hash,
        "impact_points": reward,
        "wisdom": wisdom
    }

@router.get("/dashboard/stats")
async def get_client_stats(client: dict = Depends(auth.get_api_key)):
    conn = database.get_db_connection()
    stats = conn.execute(
        "SELECT COUNT(*) as total_deeds, SUM(impact_points) as total_points FROM deeds WHERE client_id = ?",
        (client['id'],)
    ).fetchone()
    conn.close()
    return {"client_name": client['name'], "total_impact": stats['total_points'] or 0}

@router.get("/generate_mock_scenario")
async def get_mock_scenario():
    scenario = await ai_engine.generate_scenario()
    return scenario
