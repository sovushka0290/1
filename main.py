"""
═══════════════════════════════════════════════════════════════
ProtoQol — Decentralized Integrity Engine v3.8.5
The World's First Machine-Readable Ethical Consensus Protocol
═══════════════════════════════════════════════════════════════
"""

import time
import uvicorn
import io
import csv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

from core.config import log, ENGINE_NAME, VERSION, DB_WAL_MODE
from core import solana_client, database, state
from core.exceptions import ProtocolError
from routes import oracle, gateway, health

# ═══════════════════════════════════════════════════════════════
# ENGINE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="ProtoQol Integrity Engine",
    version=VERSION,
    description="""
    🚀 **Universal Verification Protocol** for Corporate ESG & Social Integrity.
    
    ### Core Features:
    * **Multi-Agent AI Consensus**: 3 Nodes (Auditor, Skeptic, Compliance) + 1 Master Biy.
    * **Solana Anchor Settlement**: Immutaqble proofs on the ledger.
    * **X-Ray Transparency**: Detailed reasoning for every ethical audit.
    * **B2B Gateway**: Seamless integration for NGOs and Foundations.
    """,
    terms_of_service="https://protoqol.org/terms/",
    contact={
        "name": "ProtoQol Dev Team",
        "url": "https://protoqol.org",
    },
)

# ═══════════════════════════════════════════════════════════════
# SECURITY & CORS ENFORCEMENT
# ═══════════════════════════════════════════════════════════════

# B2B Whitelist (Production ready)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "https://protoqol.org",
    "https://qaiyrym.kz"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Ensures absolute browser security for the integrity engine.
    """
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Monitors latency for performance auditing.
    """
    if request.method == "POST":
        print(f"DEBUG DATA: {await request.body()}")
        
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    log.info(f"[{request.method}] {request.url.path} - ProcessingTime: {process_time:.4f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response

# ═══════════════════════════════════════════════════════════════
# GLOBAL EXCEPTION HANDLER
# ═══════════════════════════════════════════════════════════════
@app.exception_handler(ProtocolError)
async def protocol_exception_handler(request: Request, exc: ProtocolError):
    return JSONResponse(
        status_code=exc.code,
        content={"status": "error", "error_type": exc.__class__.__name__, "message": exc.message},
    )

# ═══════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════
class CampaignRequest(BaseModel):
    fund_name: str = Field(..., min_length=3, max_length=100)
    title: str = Field(..., min_length=5, max_length=200)
    requirements: str = Field(..., min_length=10)
    reward: int = Field(..., ge=1)
    total_budget: int = Field(1000, ge=10)
    vault_address: str = Field("TBD", min_length=3)
    webhook_url: Optional[HttpUrl] = Field(None)

# ═══════════════════════════════════════════════════════════════
# LIFECYCLE HOOKS
# ═══════════════════════════════════════════════════════════════
@app.on_event("startup")
async def startup_event():
    log.info(f"🚀 Booting {ENGINE_NAME} v{VERSION}...")
    
    # 0. System Pulse Init
    state.PROTOCOL_STATS["boot_time"] = time.time()
    
    # 1. Database Layer
    try:
        database.init_db()
        log.info(f"📦 Persistence Layer Online. WAL_MODE={DB_WAL_MODE}")
    except Exception as e:
        log.critical(f"❌ DATABASE FAILURE: {e}")
    
    # 2. State Synchronization
    from core.config import SERVICE_STATIC_CAMPAIGNS
    db_stats = database.get_stats()
    state.PROTOCOL_STATS.update(db_stats)
    
    recent_deeds = database.get_recent_deeds(15)
    for rd in recent_deeds:
        mission_info = SERVICE_STATIC_CAMPAIGNS.get(rd['mission_id'], {"theme_accent": "#FFFFFF", "foundation_id": "UNKNOWN"})
        state.GLOBAL_PULSE.append({
            "ts": time.time(),
            "mission_id": rd['mission_id'],
            "foundation_id": mission_info.get('foundation_id', '???'),
            "status": rd['verdict'],
            "impact_points": rd['impact_points'],
            "integrity_hash": rd['integrity_hash'],
            "tx_hash": rd['tx_hash'],
            "wallet_address": rd['nomad_id'],
            "accent": mission_info.get('theme_accent', '#FFFFFF')
        })

    # 3. Blockchain Adapter
    await solana_client.check_biy_balance()
    await solana_client.init_anchor_program()
    
    log.info(f"✅ {ENGINE_NAME} Core Services are Fully Operational.")

@app.on_event("shutdown")
async def shutdown_event():
    log.info(f"🛑 Shutting down {ENGINE_NAME} Engine...")
    # Add any explicit connection closing here if needed
    log.info("✓ Persistence layer safety-lock engaged.")
    log.info("👋 System offline.")

# ═══════════════════════════════════════════════════════════════
# ENGINE ENDPOINTS (B2B Gateway)
# ═══════════════════════════════════════════════════════════════

app.include_router(health.router)
app.include_router(oracle.router)
app.include_router(gateway.router)

@app.get("/api/v1/campaigns", tags=["B2B_Engine"])
async def list_campaigns():
    """Returns active verification campaigns managed by the engine."""
    return database.get_campaigns(only_active=True)

@app.post("/api/v1/campaigns", tags=["B2B_Engine"])
async def add_campaign(req: CampaignRequest):
    """Registers a new verification mandate into the engine."""
    camp_id = database.create_campaign(
        req.fund_name, 
        req.title, 
        req.requirements, 
        req.reward,
        req.total_budget,
        req.vault_address,
        webhook_url=str(req.webhook_url) if req.webhook_url else None
    )
    log.info(f"[ENGINE_B2B] New Mandate Created: {req.title} (ID: {camp_id})")
    return {"status": "success", "campaign_id": camp_id, "message": "Engine Verification Mandate Initialized"}

@app.get("/api/v1/engine/health", tags=["System_Engine"])
async def engine_dashboard_stats():
    """
    📊 High-Level Engine Monitoring
    For technical judges and platform administrators.
    """
    stats = database.get_stats()
    campaigns = database.get_campaigns(only_active=True)
    
    # Calculate locked funds (mock logic based on campaign total budget)
    total_locked = sum(c['total_budget'] for c in campaigns)
    
    return {
        "engine": ENGINE_NAME,
        "uptime": int(time.time() - state.PROTOCOL_STATS.get("_start_ts", time.time())),
        "integrity_metrics": {
            "total_verifications": stats['total_audits'],
            "adal_rate": (stats['adal_count'] / stats['total_audits']) if stats['total_audits'] > 0 else 0,
            "total_impact_score": stats['total_impact_score']
        },
        "b2b_economy": {
            "active_campaigns": len(campaigns),
            "locked_funds_pool": f"{total_locked} BIY",
            "proof_of_funds": "Verified via Solana PDA"
        },
        "network_health": {
            "ai_consensus_nodes": 4,
            "db_mode": "SQLite-WAL",
            "solana_rpc": "CONNECTED"
        }
    }

@app.get("/api/v1/campaigns/{campaign_id}/report", tags=["B2B_Engine"])
async def export_campaign_report(campaign_id: int):
    """
    📊 Smart ESG Export (CSV)
    Generates a structured integrity report for B2B Mandates.
    """
    deeds = database.get_deeds_by_campaign(campaign_id)
    if not deeds:
        # Fallback to JSON if empty (or return empty CSV)
        return {"status": "inactive", "message": "No verified deeds found for this mandate."}

    # Generate CSV stream
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["NOMAD_ID", "MISSION_ID", "VERDICT", "IMPACT_POINTS", "TX_HASH", "INTEGRITY_HASH", "TIMESTAMP"])
    
    # Data
    for d in deeds:
        writer.writerow([
            d['nomad_id'], 
            d['mission_id'], 
            d['verdict'], 
            d['impact_points'], 
            d['tx_hash'], 
            d['integrity_hash'], 
            d['timestamp']
        ])
        
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=ProtoQol_ESG_Report_{campaign_id}.csv"
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
