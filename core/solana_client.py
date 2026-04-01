import json
import hashlib
import os
import asyncio
import time
import uuid
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Idl, Program, Provider, Wallet
from core.config import RPC_URL, MASTER_AUTHORITY_KEY, PROTOCOL_PROGRAM_ID, IDL_PATH, NOMAD_WALLET_SALT, log, SIMULATION_MODE
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from anchorpy import Context

ANCHOR_PROGRAM = None
ORACLE_KEYS = {} # Dictionary of Biy Agent Keypairs

async def check_biy_balance():
    """Checks the SOL balance of the Master Authority."""
    try:
        async with AsyncClient(RPC_URL) as client:
            resp = await client.get_balance(MASTER_AUTHORITY_KEY.pubkey())
            balance = resp.value / 1_000_000_000
            log.info(f"[SOLANA_CLIENT] Master Wallet Balance: {balance} SOL")
            if balance < 0.1:
                log.warning("[SOLANA_CLIENT] CRITICAL: Low balance on Master Authority wallet.")
            return balance
    except Exception as e:
        log.warning(f"[SOLANA_CLIENT] Could not check Master balance: {e}")
        return 0.0

async def init_anchor_program():
    global ANCHOR_PROGRAM, ORACLE_KEYS
    try:
        if not os.path.exists(IDL_PATH):
            log.warning(f"[ANCHOR_NODE] IDL not found at {IDL_PATH}")
            return

        with open(IDL_PATH, "r") as f:
            idl_json = f.read()
        idl = Idl.from_json(idl_json)
        client = AsyncClient(RPC_URL, commitment=Confirmed)
        wallet = Wallet(MASTER_AUTHORITY_KEY)
        provider = Provider(client, wallet)
        ANCHOR_PROGRAM = Program(idl, PROTOCOL_PROGRAM_ID, provider)
        
        # Initialize Biy Oracles (Deterministic for Demo)
        agents = ["AUDITOR", "SKEPTIC", "COMPLIANCE"]
        for agent in agents:
            seed = hashlib.sha256(f"BIY_{agent}_{NOMAD_WALLET_SALT}".encode()).digest()
            ORACLE_KEYS[agent] = Keypair.from_seed(seed)
            log.info(f"[ORACLE_INIT] {agent} Node Loaded: {ORACLE_KEYS[agent].pubkey()}")

        log.info("[BLOCKCHAIN_ADAPTER] ✓ ProtoQol Decentralized Protocol Interface Ready.")
    except Exception as e:
        log.warning(f"[ANCHOR_NODE] Protocol initialization failure: {e}")

async def propose_deed_on_chain(deed_id, nomad_pubkey, proposer_kp, mission_id, reward_amount):
    """
    Initializes a deed on-chain and escrows the reward.
    """
    if SIMULATION_MODE:
        log.info(f"[SIMULATION] Mocking 'propose_deed' for {deed_id}")
        return f"SIM_PROPOSE_{uuid.uuid4().hex[:8]}"

    global ANCHOR_PROGRAM

    deed_pda, _ = Pubkey.find_program_address(
        [b"deed", deed_id.encode("utf-8")],
        PROTOCOL_PROGRAM_ID
    )

    try:
        tx = await ANCHOR_PROGRAM.rpc["proposeDeed"](
            deed_id, mission_id, reward_amount,
            ctx=Context(
                accounts={
                    "deed": deed_pda,
                    "nomad": nomad_pubkey,
                    "proposer": proposer_kp.pubkey(),
                    "system_program": Pubkey.from_string("11111111111111111111111111111111"),
                },
                signers=[proposer_kp]
            )
        )
        log.info(f"[ANCHOR_TX] Deed Proposed: {deed_id} -> {tx}")
        return str(tx)
    except Exception as e:
        log.error(f"[ANCHOR_TX] Propose failed for {deed_id}: {e}")
        raise e

async def vote_deed_on_chain(deed_id, oracle_agent_name, verdict_adal, nomad_pubkey, proposer_pubkey):
    """
    Submits a verdict from a specific Biy Oracle node.
    """
    if SIMULATION_MODE:
        log.info(f"[SIMULATION] Mocking 'vote_deed' for {deed_id} by {oracle_agent_name}")
        return f"SIM_VOTE_{uuid.uuid4().hex[:8]}"

    global ANCHOR_PROGRAM, ORACLE_KEYS

    oracle_kp = ORACLE_KEYS.get(oracle_agent_name)
    if not oracle_kp:
        raise ValueError(f"Unknown Oracle Agent: {oracle_agent_name}")

    deed_pda, _ = Pubkey.find_program_address(
        [b"deed", deed_id.encode("utf-8")],
        PROTOCOL_PROGRAM_ID
    )
    
    oracle_reg_pda, _ = Pubkey.find_program_address(
        [b"oracle", bytes(oracle_kp.pubkey())],
        PROTOCOL_PROGRAM_ID
    )

    try:
        tx = await ANCHOR_PROGRAM.rpc["voteDeed"](
            deed_id, verdict_adal,
            ctx=Context(
                accounts={
                    "deed": deed_pda,
                    "nomad": nomad_pubkey,
                    "proposer": proposer_pubkey,
                    "oracle": oracle_kp.pubkey(),
                    "oracleRegistry": oracle_reg_pda,
                    "systemProgram": Pubkey.from_string("11111111111111111111111111111111"),
                },
                signers=[oracle_kp]
            )
        )
        log.info(f"[ANCHOR_TX] {oracle_agent_name} Voted: {verdict_adal} -> {tx}")
        return str(tx)
    except Exception as e:
        log.error(f"[ANCHOR_TX] Vote failed for {deed_id} by {oracle_agent_name}: {e}")
        raise e

async def confirm_transaction_status(tx_hash: str) -> str:
    if not tx_hash or tx_hash.startswith("SIM"):
        return "finalized"
    
    await asyncio.sleep(5) # Faster check for devnet
    try:
        async with AsyncClient(RPC_URL) as client:
            status = await client.get_signature_statuses([tx_hash])
            if status.value[0] and status.value[0].confirmation_status:
                return str(status.value[0].confirmation_status)
            return "failed"
    except Exception:
        return "uncertain"

def get_nomad_wallet(user_id: str):
    secured_payload = f"{user_id}::{NOMAD_WALLET_SALT}"
    seed = hashlib.sha256(secured_payload.encode()).digest()
    return Keypair.from_seed(seed)
