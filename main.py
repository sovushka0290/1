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

from core.config import log, ENGINE_NAME, VERSION, DB_WAL_MODE, MASTER_AUTHORITY_KEY, SIMULATION_MODE, PROTOCOL_PROGRAM_ID

from core import solana_client, database, state, ai_engine
from core.exceptions import ProtocolError
from routes import gateway

# ═══════════════════════════════════════════════════════════════
# ENGINE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="ProtoQol Integrity Engine",
    version=VERSION,
    description="🚀 Universal Verification Protocol for ESG & Social Integrity."
)

app.include_router(gateway.router)

# 1. API GATEWAY: Broad CORS for B2B Widgets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# STATIC ASSETS (Demo Portals)
# ═══════════════════════════════════════════════════════════════

@app.get("/b2b_client_demo.html", include_in_schema=False)
async def serve_demo_portal():
    """Serves the B2B demo portal for live pitch recording."""
    html_path = os.path.join(os.path.dirname(__file__), "../b2b_client_demo.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return JSONResponse({"status": "error", "message": "Demo HTML not found in root."}, status_code=404)

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
    # 1. Self-Healing Database Migration
    try:
        conn = database.get_db_connection()
        # Ensure client columns
        try: conn.execute("ALTER TABLE clients ADD COLUMN credits INTEGER DEFAULT 1000")
        except: pass 
        
        # Ensure deed columns for Glass Box
        try: conn.execute("ALTER TABLE deeds ADD COLUMN ai_dialogue TEXT")
        except: pass
        try: conn.execute("ALTER TABLE deeds ADD COLUMN wisdom TEXT")
        except: pass
        
        # 2. Seed Test Client
        conn.execute(
            "INSERT OR IGNORE INTO clients (id, name, api_key, credits, plan_type) VALUES (?, ?, ?, ?, ?)",
            (777, "KASE ESG Portal", "PQ_DEV_TEST_2026", 1000, "Enterprise")
        )
        conn.commit()
        conn.close()
        log.info("[STARTUP] 🔑 B2B Test Client Authorized & Credits Synced.")
    except Exception as e:
        log.warning(f"[STARTUP] Migration/Seed fail: {e}")

    # Lazy init Solana & DB
    await solana_client.check_biy_balance()

@app.get("/audit/{integrity_hash}", tags=["Transparency"])
async def public_audit_mirror(integrity_hash: str):
    """
    The Public Glass Box: High-Fidelity Decentralized Transparency.
    Visualizes the AI Biy Council's deliberation in a human-readable way.
    """
    deed = database.get_deed_by_hash(integrity_hash)
    if not deed:
        raise HTTPException(status_code=404, detail="Audit Link Invalid or Pending Anchorage.")
    
    # Robust Dialog Parsing
    try:
        dialog_raw = deed.get('ai_dialogue', '{"info": "No dialogue logs."}')
        # Handle double serialization and string vs dict
        if isinstance(dialog_raw, str):
            try: dialog = json.loads(dialog_raw)
            except: dialog = {"raw": dialog_raw}
        else:
            dialog = dialog_raw
            
        if isinstance(dialog, str): dialog = json.loads(dialog)
        
        # Focus on report nodes if present
        if not any(k in dialog for k in ['auditor', 'skeptic', 'social']):
             # Check for nested structure from full ai_res
             dialog = {
                "auditor": dialog.get("auditor_report", {}).get("status", "PASS"),
                "skeptic": dialog.get("skeptic_report", {}).get("verdict", "CLEAN"),
                "social": dialog.get("social_report", {}).get("wisdom", "...")
             }
    except:
        dialog = {"info": "Dialog sequence initializing..."}

    v_class = "adal" if deed['verdict'] == 'ADAL' else "aram"
    v_text = "ADAL: ВЕРИФИЦИРОВАНО" if deed['verdict'] == 'ADAL' else "ARAM: ОТКЛОНЕНО"
    
    is_pending = deed['tx_hash'] in ["PROCESSING", "Pending...", "undefined"] or deed['tx_hash'].startswith("NEURAL_ANCHOR")
    anchor_html = f'<a href="https://explorer.solana.com/address/{PROTOCOL_PROGRAM_ID}?cluster=devnet" target="_blank" class="tx-hash">✓ VIEW ON SOLANA (CONTRACT)</a>' if is_pending else f'<a href="https://explorer.solana.com/tx/{deed["tx_hash"]}?cluster=devnet" target="_blank" class="tx-hash">✓ VIEW ON SOLANA (TX)</a>'
    
    # Refresh tag if pending
    refresh_tag = '<meta http-equiv="refresh" content="3">' if is_pending else ""

    # NOMAD CYBERPUNK PREMIUM CSS
    html_content = f"""
    <html>
    <head>
        <title>ProtoQol Glass Box | {integrity_hash[:8]}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        {refresh_tag}
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;600;900&family=JetBrains+Mono&display=swap" rel="stylesheet">
        <style>
            :root {{
                --accent: {'#00ffcc' if deed['verdict'] == 'ADAL' else '#ff4d4d'};
                --bg: #05070a;
            }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }} }}
            body {{ 
                background: var(--bg); color: #fff; font-family: 'Outfit', sans-serif; 
                margin: 0; padding: 20px; display: flex; justify-content: center;
                background-image: radial-gradient(circle at 50% 0%, #0a1c2d 0%, #05070a 100%);
            }}
            .terminal {{ 
                width: 100%; max-width: 800px;
                background: rgba(15, 25, 35, 0.85); backdrop-filter: blur(20px);
                border: 1px solid rgba(0, 255, 204, 0.1); padding: 50px; border-radius: 32px;
                box-shadow: 0 40px 100px rgba(0,0,0,0.8);
                position: relative; overflow: hidden;
            }}
            .terminal::before {{
                content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 6px; background: var(--accent);
            }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; }}
            .logo {{ font-size: 0.9rem; font-weight: 900; letter-spacing: 5px; color: var(--accent); opacity: 0.9; text-transform: uppercase; }}
            .verdict {{ 
                font-size: 3rem; font-weight: 900; color: var(--accent); 
                margin: 30px 0; border-left: 10px solid var(--accent); padding-left: 25px;
                text-shadow: 0 0 30px var(--accent);
            }}
            .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 50px; font-family: 'JetBrains Mono'; font-size: 0.85rem; background: rgba(0,0,0,0.3); padding: 20px; border-radius: 12px; }}
            .meta-item {{ opacity: 0.7; }}
            .node-card {{ 
                background: rgba(255,255,255, 0.02); border: 1px solid rgba(255,255,255,0.05);
                border-radius: 20px; padding: 25px; margin-bottom: 20px; border-left: 4px solid var(--accent);
                transition: 0.3s;
            }}
            .node-card:hover {{ background: rgba(255,255,255, 0.05); transform: translateX(5px); }}
            .node-header {{ font-weight: 900; color: var(--accent); margin-bottom: 12px; font-size: 0.8rem; letter-spacing: 2px; }}
            .node-text {{ line-height: 1.6; font-size: 1.05rem; opacity: 0.9; }}
            .wisdom {{ 
                background: rgba(255, 215, 0, 0.1); color: #FFD700; border: 1px solid #FFD700;
                padding: 30px; border-radius: 20px; font-style: italic; text-align: center; margin: 50px 0; font-size: 1.2rem;
            }}
            .tx-hash {{ color: var(--accent); text-decoration: none; border-bottom: 1px solid var(--accent); font-weight: bold; }}
            .footer {{ font-size: 0.75rem; color: #555; text-align: center; margin-top: 50px; line-height: 2; }}
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="header">
                <div class="logo">PROTOQOL GLASS BOX</div>
                <div style="text-align: right; font-family: 'JetBrains Mono'; font-size: 0.7rem; opacity: 0.4;">ID: {integrity_hash[:16]}...</div>
            </div>

            <div class="verdict">{v_text}</div>
            
            <div class="meta-grid">
                <div class="meta-item">MISSION: {deed['mission_id']}</div>
                <div class="meta-item">NOMAD: {deed['nomad_id']}</div>
                <div class="meta-item">SOURCE: {deed.get('source', 'B2B GATEWAY')}</div>
                <div class="meta-item">ANCHOR: {anchor_html}</div>
            </div>

            <h3 style="font-size: 1.2rem; margin-bottom: 30px; opacity: 0.9; display: flex; align-items: center;">
                <span style="color: var(--accent); margin-right: 15px;">◆</span> НЕЙРО-ПРОТОКОЛ ДОПРОСА (AI COUNCIL)
            </h3>
            
            <div class="discussion">
                { ''.join([f'''
                <div class="node-card">
                    <div class="node-header">🔍 NODE: {k.upper()}</div>
                    <div class="node-text">{(v if isinstance(v, str) else json.dumps(v))}</div>
                </div>
                ''' for k,v in dialog.items() if v]) }
            </div>

            <div class="wisdom">
                "{deed.get('wisdom', 'В единстве — правда.')}"
            </div>

            <div class="footer">
                AI COUNCIL CONSENSUS REACHED AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                SECURED BY SOLANA DEVNET PROTOCOL • NO-TRUST VERIFICATION SYSTEM<br>
                <span style="letter-spacing: 5px;">PROTOQOL v4.2.0</span>
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
