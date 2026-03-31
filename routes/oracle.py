import time
import hashlib
import asyncio
from fastapi import APIRouter, Form, HTTPException, Query, BackgroundTasks, Depends, Request

from core.config import SERVICE_STATIC_CAMPAIGNS, PROTOCOL_API_WHITELIST, log, MASTER_AUTHORITY_KEY
from core import ai_engine, solana_client, state, database, guardian, webhooks

router = APIRouter(prefix="", tags=["Protocol_Engine"])

@router.get("/", tags=["System"])
async def root():
    return {
        "protocol": "ProtoQol_v4_Decentralized",
        "status": "online",
        "oracle_nodes": 3,
        "chain": "Solana Devnet",
        "total_events": len(state.GLOBAL_PULSE),
        "boot_time": state.PROTOCOL_STATS["boot_time"],
    }

async def async_consensus_routine(nomad_pubkey, deed_id, mission_id, points, agent_verdicts, integrity_hash, campaign_id=None):
    """
    Decentralized Workflow:
    1. Propose Deed (Escrow funds)
    2. Broadcast for Biy Oracles to vote
    3. Consensus reached -> Auto release
    """
    try:
        log.info(f"[DECENTRALIZED_PULSE] Starting consensus for {deed_id}")
        
        # 1. PROPOSE (On behalf of Foundation/B2B Proposer)
        propose_tx = await solana_client.propose_deed_on_chain(
            deed_id, nomad_pubkey, MASTER_AUTHORITY_KEY, mission_id, points
        )
        
        # 2. VOTE (Sequential Agent Submission)
        last_vote_tx = None
        for agent_v in agent_verdicts:
            node_name = agent_v.get("node")
            verdict_bool = agent_v.get("verdict") == "ADAL"
            last_vote_tx = await solana_client.vote_deed_on_chain(
                deed_id, node_name, verdict_bool, nomad_pubkey, MASTER_AUTHORITY_KEY.pubkey()
            )
            # Small delay to prevent RPC congestion
            await asyncio.sleep(0.5)

        # 3. Finalization Monitor
        chain_state = await solana_client.confirm_transaction_status(last_vote_tx)
        
        # Update persistence layer
        database.update_deed_status(integrity_hash, last_vote_tx, chain_state)
        
        # Update Global Pulse
        for event in state.GLOBAL_PULSE:
            if event.get("integrity_hash") == integrity_hash:
                event["tx_hash"] = last_vote_tx
                event["chain_status"] = chain_state
                break
        
        log.info(f"[DECENTRALIZED_PULSE] Protocol Resolution: {deed_id} -> {chain_state}")

        # Fire Webhooks
        if campaign_id:
            camp = database.get_campaign_by_id(campaign_id)
            if camp and camp.get('webhook_url'):
                webhook_payload = {
                    "event": "CONSENSUS_REACHED",
                    "deed_id": deed_id,
                    "nomad_id": str(nomad_pubkey),
                    "chain_status": chain_state,
                    "tx_hash": last_vote_tx
                }
                await webhooks.fire_webhook(camp['webhook_url'], webhook_payload)

    except Exception as e:
        log.error(f"[DECENTRALIZED_CORE] Consensus disruption: {e}")
        database.update_deed_status(integrity_hash, "FAILED", "failed")

@router.post("/verify", tags=["Oracle"])
async def ritual_verify(
    background_tasks: BackgroundTasks,
    request: Request,
    description: str = Form(...),
    telegram_id: str = Form("UnknownNomad"),
    mission_id: str = Form(None),
    campaign_id: int = Form(None),
    api_key: str = Form("PQ_DEV_TEST_2026"),
    _guard: bool = Depends(guardian.rate_limit_check)
):
    if api_key not in PROTOCOL_API_WHITELIST:
        raise HTTPException(status_code=401, detail="Unauthorized Protocol Access.")

    mission_info = SERVICE_STATIC_CAMPAIGNS.get(mission_id, {"requirements": "General Engine Mandate", "foundation_id": "GLOBAL", "theme_accent": "#00FFA3", "impact_weight": 1.0})
    
    if campaign_id:
        camp_data = database.get_campaign_by_id(campaign_id)
        if camp_data:
            mission_info["requirements"] = camp_data["requirements"]
            mission_info["foundation_id"] = camp_data["fund_name"]
    
    # 1. AI CONSENSUS (Multi-Agent Analysis)
    ai_res = await ai_engine.analyze_deed(description, mission_info, campaign_id=campaign_id)
    verdict = ai_res.get("verdict", "ARAM")
    
    if verdict == "SYSTEM_ERROR":
        raise HTTPException(status_code=503, detail="Protocol Brain Desynced.")

    wisdom = ai_res.get("wisdom", "...")
    raw_score = float(ai_res.get("impact_score", 0))
    weighted_score = raw_score * mission_info.get("impact_weight", 1.0)
    
    points = 0
    if verdict == "ADAL":
        if campaign_id:
            camp_data = database.get_campaign_by_id(campaign_id)
            points = camp_data["reward"] if camp_data else int(weighted_score * 100)
        else:
            points = int(weighted_score * 100)

    # 2. PQ-INTEGRITY
    deed_id = f"D_{int(time.time()*1000)}"
    content_payload = f"{description}|{mission_id}|{telegram_id}|{deed_id}"
    integrity_hash = hashlib.sha256(content_payload.encode()).hexdigest()[:16]

    # 3. NOMAD WALLET
    user_kp = solana_client.get_nomad_wallet(telegram_id)
    
    # 4. DECENTRALIZED EXECUTION QUEUE
    agent_verdicts = ai_res.get("consensus_logs", [])
    
    background_tasks.add_task(
        async_consensus_routine,
        user_kp.pubkey(), 
        deed_id, 
        mission_id, 
        points, 
        agent_verdicts,
        integrity_hash,
        campaign_id=campaign_id
    )

    # 5. UI PULSE
    new_event = {
        "ts": time.time(),
        "mission_id": mission_id,
        "foundation_id": mission_info['foundation_id'],
        "status": verdict,
        "impact_points": points,
        "wisdom": wisdom,
        "integrity_hash": integrity_hash,
        "tx_hash": "CRYSTALLIZING",
        "chain_status": "voting",
        "wallet_address": str(user_kp.pubkey()),
        "accent": mission_info['theme_accent'],
        "ai_dialogue": agent_verdicts 
    }
    state.GLOBAL_PULSE.append(new_event)
    database.save_deed(new_event, mission_info)

    state.PROTOCOL_STATS["total_audits"] += 1
    if verdict == "ADAL":
        state.PROTOCOL_STATS["adal_count"] += 1
    else:
        state.PROTOCOL_STATS["aram_count"] += 1

    return new_event
