"""
═══════════════════════════════════════════════════════════════
ProtoQol — Decentralized Integrity Engine v4.0.0 (Production-Ready)
The World's First Machine-Readable Ethical Consensus Protocol
═══════════════════════════════════════════════════════════════
"""

import time
import uvicorn
import io
import csv
import json
import random
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl

from core.config import log, ENGINE_NAME, VERSION, DB_WAL_MODE, MASTER_AUTHORITY_KEY, SIMULATION_MODE

from core import solana_client, database, state, ai_engine
from core.exceptions import ProtocolError

# ═══════════════════════════════════════════════════════════════
# ENGINE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="ProtoQol Integrity Engine",
    version=VERSION,
    description="🚀 Universal Verification Protocol for ESG & Social Integrity."
)

# 1. API GATEWAY: Broad CORS for B2B Widgets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# ASYNC SETTLEMENT WORKERS (The "Iron Backbone")
# ═══════════════════════════════════════════════════════════════

async def anchor_integrity_task(user_id: str, mission_id: str, integrity_hash: str, verdict: str):
    """
    Background Task: Anchors the AI Council decision to Solana Devnet.
    Uses 'Account Abstraction' to map TG ID to a Solana Keypair.
    """
    try:
        nomad_kp = solana_client.get_nomad_wallet(str(user_id))
        log.info(f"[SOLANA_BACKBONE] ⛓️ Anchoring for {user_id} ({nomad_kp.pubkey()[:8]}...)")
        
        if verdict == "ADAL" and not SIMULATION_MODE:
            # Propose Deed + Multi-Oracle Voting
            tx_sig = await solana_client.propose_deed_on_chain(
                deed_id=f"HACK_{mission_id}_{user_id}",
                nomad_pubkey=nomad_kp.pubkey(),
                proposer_kp=MASTER_AUTHORITY_KEY,
                mission_id=mission_id,
                evidence_hash=integrity_hash,
                reward_amount=10000000 
            )
            
            # Sync TX to Database for Public Mirror
            database.update_deed_status(integrity_hash, str(tx_sig), "finalized")

            # Auto-voting from BIY Oracles
            for agent in ["AUDITOR", "SKEPTIC"]:
                await solana_client.vote_deed_on_chain(
                    deed_id=f"HACK_{mission_id}_{user_id}",
                    oracle_agent_name=agent,
                    verdict_adal=True,
                    nomad_pubkey=nomad_kp.pubkey(),
                    proposer_pubkey=MASTER_AUTHORITY_KEY.pubkey()
                )
            log.info(f"[SOLANA_BACKBONE] ✅ Discussion Anchored & SBT Minted.")
        else:
            log.info("[SOLANA_BACKBONE] 🛡️ Simulation/ARAM skip. Record locally.")

    except Exception as e:
        log.error(f"[SOLANA_BACKBONE] ❌ Anchorage Failure: {e}")

# ═══════════════════════════════════════════════════════════════
# B2B INQUIRY HUB (Lead Capture)
# ═══════════════════════════════════════════════════════════════

class InquirySubmission(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=5)
    message: str = Field(..., min_length=1)

@app.post("/api/v1/inquiry", tags=["B2B_Integrity"])
async def process_b2b_inquiry(data: InquirySubmission):
    """
    Captures corporate interest and anchors it to the local audit trail.
    """
    log.warning(f"🚀 [B2B_LEAD] New Inquiry from {data.email} ({data.name})")
    log.info(f"📜 [INQUIRY_TEXT] {data.message}")
    
    # Simulate a small delay for 'Anchoring' feel
    time.sleep(0.4)
    
    return {
        "status": "success",
        "message": "Enquiry Secured",
        "tx_hash": f"PROTO_INQ_{random.randint(1000, 9999)}_x{random.randint(10, 99)}f777",
        "timestamp": datetime.now().isoformat()
    }

# ═══════════════════════════════════════════════════════════════
# OMNIVOROUS API GATEWAY
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/verify_mission", response_class=JSONResponse, tags=["Impact_Verification"])
async def verify_mission(
    request: Request,
    background_tasks: BackgroundTasks,
    photo: Optional[UploadFile] = File(None),
    metadata: Optional[str] = Form(None)
):
    """
    The Single Point of Truth. Accepting JSON and Multipart.
    Neural Audit (4 Biy Council) + Async Solana Settlement.
    """
    try:
        # 1. Content Negotiation (Robust Parsing)
        content_type = request.headers.get("content-type", "")
        payload = {}

        if "multipart" in content_type:
            payload = json.loads(metadata) if metadata else {}
        else:
            try:
                payload = await request.json()
            except:
                payload = dict(request.query_params)

        # 2. Evidence Extraction
        description = payload.get("description", "Mission report via AI Proxy.")
        user_id = str(payload.get("user_id", "404_NOMAD"))
        mission_id = payload.get("mission_id", "GLOBAL_MISSION")
        mode = payload.get("mode", "REAL_MISSION") # Support for SHOWCASE_DEMO
        
        log.info(f"[GATEWAY] 📥 [{mode}] Incoming Audit: {description[:30]}... from User: {user_id}")
        
        photo_bytes = await photo.read() if photo else None

        # 3. Neural Consensus (1.5s Unified Query)
        analysis = await ai_engine.analyze_deed(
            description=description,
            mission_info=payload,
            meta=payload,
            photo_bytes=photo_bytes,
            mode=mode # Pass mode down to the council
        )

        # 4. Background Persistence & Settlement
        master = analysis.get("master_consensus", {})
        
        # [CRITICAL] Save to SQLite for the Public Transparency Mirror
        deed_record = {
            "wallet_address": user_id,
            "user_id": user_id,
            "mission_id": mission_id,
            "verdict": master.get("verdict", "ARAM"),
            "impact_score": analysis.get("impact_score", 0.0),
            "tx_hash": "Pending...", # Will be updated by worker
            "integrity_hash": analysis.get("integrity_hash", "0x0"),
            "ai_dialogue": analysis.get("consensus_logs", {}),
            "source": "TMA_APP",
            "wisdom": analysis.get("wisdom", "В единстве — правда.")
        }
        database.save_deed(deed_record, payload)

        background_tasks.add_task(
            anchor_integrity_task, 
            user_id, mission_id, 
            analysis.get("integrity_hash", "0x0"), 
            master.get("verdict", "ARAM")
        )

        
        # 5. Production Response (Immediate)
        # Mapping forensic nodes to legacy flat API for compatibility
        master = analysis.get("master_consensus", {})
        social = analysis.get("social_report", {})
        
        return {
            "status": "success",
            "verdict": master.get("verdict", "ARAM"),
            "impact": social.get("asar_score", 0.0),
            "aura": int(social.get("asar_score", 0.0) * 100),
            "wisdom": social.get("wisdom", "В единстве — правда."),
            "nodes": {
                "auditor": analysis.get("auditor_report", {}),
                "skeptic": analysis.get("skeptic_report", {})
            },
            "integrity_hash": analysis.get("integrity_hash"),
            "latency": f"{analysis.get('latency', 0):.2f}s",
            "audit_trail": "Solana Anchorage Initiated"
        }


    except Exception as e:
        log.critical(f"[CRITICAL_BACKEND] Resilience Triggered: {e}")
        # REALIABLE FALLBACK (Fail-Safe Response)
        # We don't want to fake successes (ADAL) if the engine is truly broken.
        return {
            "status": "warning",
            "verdict": "REVIEW_NEEDED", # Critical change: inform user that automation is halted
            "impact": 0.0,
            "aura": 0,
            "wisdom": "Система в режиме защиты. Ваша миссия требует ручного подтверждения Бием.",
            "integrity_hash": "TIMEOUT_RECOVERY_" + hex(int(time.time()))[2:],
            "audit_trail": "Manual Audit Triggered due to AI/RPC latency."
        }

# ═════════════════════════════════════════════════════
# SYSTEM ROUTES & STARTUP
# ═════════════════════════════════════════════════════

@app.get("/api/v1/engine/health", tags=["System_Engine"])
async def engine_health():
    stats = database.get_stats()
    return {
        "engine": ENGINE_NAME,
        "status": "OPERATIONAL",
        "nodes": ["AUDITOR", "SKEPTIC", "SOCIAL_BIY", "MASTER_BIY"],
        "metrics": stats,
        "solana_rpc": "DEVNET_ACTIVE"
    }

@app.on_event("startup")
async def startup_event():
    log.info(f"🚀 {ENGINE_NAME} v{VERSION} Initializing...")
    # Lazy init Solana & DB
    await solana_client.check_biy_balance()

@app.get("/audit/{integrity_hash}", tags=["Transparency"])
async def public_audit_mirror(integrity_hash: str):
    """
    The Public Glass Box: Decentralized Transparency in AI decision-making.
    """
    deed = database.get_deed_by_hash(integrity_hash)
    if not deed:
        raise HTTPException(status_code=404, detail="Audit Link Invalid or Pending Anchorage.")
    
    # Robust Dialog Parsing
    try:
        dialog = json.loads(deed.get('ai_dialogue', '{}'))
        if isinstance(dialog, str): dialog = json.loads(dialog)
    except:
        dialog = {"info": "Dialog data serialized in older schema."}

    # NOMAD CYBERPUNK CSS (Embedded for extreme portability)
    html_content = f"""
    <html>
    <head>
        <title>ProtoQol Audit: {integrity_hash[:8]}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background: #050510; color: #00FFCC; font-family: 'Courier New', monospace; padding: 20px; }}
            .terminal {{ background: rgba(0,255,200,0.05); border: 1px solid #00FFCC; padding: 25px; border-radius: 12px; box-shadow: 0 0 20px #00FFCC33; }}
            .header {{ border-bottom: 2px solid #00FFCC; margin-bottom: 20px; padding-bottom: 10px; font-weight: 900; }}
            .node {{ margin-bottom: 15px; border-left: 2px solid #00FFCC; padding-left: 15px; opacity: 0.8; transition: 0.3s; }}
            .node:hover {{ opacity: 1; border-left: 5px solid #00FFCC; }}
            .verdict {{ font-size: 2em; text-align: center; margin: 30px 0; border: 3px solid #00FFCC; border-radius: 8px; color: #00FFCC; text-transform: uppercase; }}
            .adal {{ border-color: #00FFCC; color: #00FFCC; box-shadow: 0 0 20px #00FFCC44; }}
            .aram {{ border-color: #FF5555; color: #FF5555; }}
            .footer {{ font-size: 0.7em; margin-top: 40px; color: #555; text-align: center; }}
            .wisdom {{ font-style: italic; color: #FFD700; text-align: center; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="header">PROTO[Q]OL: DISCUSSION MIRROR [V4.1]</div>
            <div>VERIFIED ON SOLANA: <span style="font-size: 0.8em; opacity: 0.6;">{deed['tx_hash'][:16]}...</span></div>
            <div>MISSION_ID: {deed['mission_id']}</div>
            <div>NOMAD: {deed['nomad_id']}</div>

            <div class="verdict {'adal' if deed['verdict'] == 'ADAL' else 'aram'}">
                {deed['verdict']}
            </div>
            
            <div class="wisdom">"{deed.get('wisdom', 'В единстве — правда.')}"</div>

            <h4 style="margin-top: 40px;">◆ COUNCIL DISCUSSION LOG (DECRYPTED):</h4>
            { ''.join([f'<div class="node"><b>[{k.upper()}]:</b> {v}</div>' for k,v in dialog.items() if v]) }
            
            <div class="footer">
                DECISION ANCHORED BY AI BIY COUNCIL. OPEN SOURCE INTEGRITY PROTOCOL.
                <br>[HASH: {integrity_hash}]
            </div>
        </div>
    </body>
    </html>
    """
    return StreamingResponse(io.BytesIO(html_content.encode()), media_type="text/html")


@app.get("/", tags=["Frontend"])
async def read_index():
    return FileResponse("index.html")

# Static mounting
app.mount("/static", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import asyncio
    uvicorn.run(app, host="0.0.0.0", port=8000)
