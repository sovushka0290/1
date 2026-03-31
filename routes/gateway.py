import time
import hashlib
from fastapi import APIRouter, Form, HTTPException, Depends, Request, Body
from typing import Optional
from solders.pubkey import Pubkey
from anchorpy import Context

from core.config import SERVICE_STATIC_CAMPAIGNS, MASTER_AUTHORITY_KEY, PROTOCOL_PROGRAM_ID, log
from core import ai_engine, solana_client, state, database, auth, ai_consensus
from schemas import DeedRequest

router = APIRouter(prefix="/api/v1", tags=["B2B_Engine_Gateway"])

# 🚨 THE RED SWITCH: Set to True before the live pitch to bypass potential network failures.
DEMO_MODE = True

@router.post("/etch_deed")
async def enterprise_etch_deed(
    request: Request,
    client: dict = Depends(auth.require_credits)
):
    """
    Enterprise Standard Endpoint for B2B Clients.
    Supports both JSON and Form-Data for maximum robustness.
    """
    # 1. ROBUST INPUT RESOLUTION
    content_type = request.headers.get("Content-Type", "")
    form_data = await request.form()
    json_data = {}
    
    if "application/json" in request.headers.get("Content-Type", ""):
        try:
            json_data = await request.json()
        except Exception:
            pass

    # Merge data sources (JSON values take precedence)
    data = {**form_data, **json_data}
    
    description = data.get("description")
    nomad_id = data.get("nomad_id")
    mission_id = data.get("mission_id")
    source = data.get("source", "API Gateway")

    if not description or not mission_id:
        raise HTTPException(status_code=422, detail="Missing required data: description and mission_id.")

    log.info(f"[B2B_GW] [{content_type}] Client: {client['name']} | mission: {mission_id}")
    if mission_id not in SERVICE_STATIC_CAMPAIGNS:
        raise HTTPException(status_code=400, detail="Unknown Protocol mandate.")

    mission_info = SERVICE_STATIC_CAMPAIGNS[mission_id]
    log.info(f"[B2B_GW] Client: {client['name']} | mission: {mission_id}")

    # 🚨 EMERGENCY DEMO MODE OVERRIDE
    if DEMO_MODE:
        import asyncio
        log.warning(f"[DEMO] 🟡 Bypassing AI/Chain for live pitch. Seed: {description[:15]}...")
        await asyncio.sleep(1.5) # Maintain GSAP cinematic timing
        ai_res = {
            "status": "ADAL",
            "confidence_score": 99,
            "biy_wisdom": "[DEMO] Совет Биев подтверждает: действие соответствует Zheti Zhargy. Транзакция готова к записи."
        }
    else:
        # 🟢 REAL-WORLD EXECUTION (CrewAI + Gemini 2.0)
        deed_payload = {
            "description": description,
            "mission_requirements": mission_info['requirements'],
            "metadata": {"source": source, "client": client['name']}
        }
        ai_res = ai_consensus.run_biy_council(deed_payload)
    
    verdict = ai_res.get("status", "ARAM")
    points = int(float(ai_res.get("confidence_score", 0))) if verdict == "ADAL" else 0
    wisdom = ai_res.get("biy_wisdom", "Justice is blind.")

    # 2. INTEGRITY HASH (PQ-Standard v1)
    integrity_hash = hashlib.sha256(f"{description}|{client['name']}|{time.time()}".encode()).hexdigest()[:16]

    # 3. SETTLEMENT
    tx_hash = "SIMULATED_TX"
    user_kp = solana_client.get_nomad_wallet(nomad_id or f"nomad_{time.time()}")
    
    if verdict == "ADAL":
        if solana_client.ANCHOR_PROGRAM:
            try:
                deed_id = f"EQ_{int(time.time()*1000)}"
                nomad_pubkey = user_kp.pubkey()
                deed_pda, _ = Pubkey.find_program_address([b"deed", bytes(nomad_pubkey), deed_id.encode()], PROTOCOL_PROGRAM_ID)
                profile_pda, _ = Pubkey.find_program_address([b"profile", bytes(nomad_pubkey)], PROTOCOL_PROGRAM_ID)

                tx = await solana_client.ANCHOR_PROGRAM.rpc["etch_deed"](
                    nomad_pubkey, deed_id, mission_id, points, verdict, integrity_hash,
                    ctx=Context(accounts={
                        "deed_record": deed_pda, "nomad_profile": profile_pda,
                        "oracle": MASTER_AUTHORITY_KEY.pubkey(), "system_program": Pubkey.from_string("11111111111111111111111111111111")
                    }, signers=[MASTER_AUTHORITY_KEY])
                )
                tx_hash = str(tx)
                # Success! Deduct one credit from B2B subscription
                database.deduct_credit(client['id'])
            except Exception as e:
                log.error(f"[GATEWAY_TX] Error: {e}")
                # We still want to log the event in DB as "Attempted/Failed"? 
                # For MVP we simple raise 503
                raise HTTPException(status_code=503, detail="Blockchain sync failed.")

    # 4. DB LOGGING (Persistence)
    conn = database.get_db_connection()
    conn.execute(
        "INSERT INTO deeds (client_id, nomad_id, mission_id, verdict, impact_points, tx_hash, integrity_hash, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (client['id'], nomad_id or "Anonymous", mission_id, verdict, points, tx_hash, integrity_hash, source)
    )
    conn.commit()
    conn.close()

    return {
        "status": "crystalized" if verdict == "ADAL" else "denied",
        "verdict": verdict,
        "tx_hash": tx_hash,
        "integrity_hash": integrity_hash,
        "impact_points": points,
        "auditor_wisdom": wisdom
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

@router.post("/dashboard/generate_key")
async def generate_new_api_key(new_client_name: str = Form(...), client: dict = Depends(auth.get_api_key)):
    # Simple internal admin-like check or just allow creation for MVP
    new_key = hashlib.sha256(f"{new_client_name}|{time.time()}".encode()).hexdigest()[:32]
    conn = database.get_db_connection()
    try:
        conn.execute("INSERT INTO clients (name, api_key) VALUES (?, ?)", (new_client_name, new_key))
        conn.commit()
        return {"name": new_client_name, "api_key": new_key}
    except Exception:
        raise HTTPException(status_code=400, detail="Client already exists.")
    finally:
        conn.close()

@router.get("/gateway/missions")
async def get_all_missions():
    """Merge static missions from config with dynamic campaigns from DB"""
    missions = {**SERVICE_STATIC_CAMPAIGNS}
    
    # Add dynamic campaigns from DB
    conn = database.get_db_connection()
    campaigns = conn.execute("SELECT * FROM campaigns WHERE is_active = 1").fetchall()
    conn.close()
    
    for c in campaigns:
        m_id = f"db_camp_{c['id']}"
        missions[m_id] = {
            "client": c['fund_name'],
            "foundation_id": f"CAMP_{c['id']}",
            "theme_accent": "#8B5CF6",
            "requirements": c['requirements'],
            "status": "active",
            "impact_weight": 1.0,
            "title": c['title'],
            "reward": c['reward']
        }
    
    return missions

@router.get("/client/usage")
async def get_client_usage(client: dict = Depends(auth.get_api_key)):
    """
    Returns subscription details and quota status for the authenticated client.
    """
    usage = database.get_client_usage(client['id'])
    return {
        "client": client['name'],
        "plan": usage['plan_type'],
        "credits": {
            "total": usage['credits_total'],
            "used": usage['credits_used'],
            "remaining": usage['credits_total'] - usage['credits_used']
        },
        "expires_at": usage['expires_at'],
        "status": "active" if usage['credits_used'] < usage['credits_total'] else "limited"
    }
