import json
import hashlib
import os
import asyncio
import uuid
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Idl, Program, Provider, Wallet
from core.config import RPC_URL, MASTER_AUTHORITY_KEY, PROTOCOL_PROGRAM_ID, IDL_PATH, log, SIMULATION_MODE
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from anchorpy import Context

ANCHOR_PROGRAM = None

async def check_biy_balance():
    """Checks the SOL balance of the Master Authority."""
    try:
        async with AsyncClient(RPC_URL) as client:
            resp = await client.get_balance(MASTER_AUTHORITY_KEY.pubkey())
            balance = resp.value / 1_000_000_000
            log.info(f"[SOLANA_CLIENT] Master Wallet Balance: {balance} SOL")
            return balance
    except Exception as e:
        log.warning(f"[SOLANA_CLIENT] Could not check balance: {e}")
        return 0.0

async def init_anchor_program():
    global ANCHOR_PROGRAM
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
        
        log.info("[BLOCKCHAIN_ADAPTER] ✓ ProtoQol Lean Protocol Interface Ready.")
    except Exception as e:
        log.warning(f"[ANCHOR_NODE] Protocol initialization failure: {e}")

async def etch_deed_on_chain(deed_id: str, integrity_hash: str, impact_score: int, verdict: str):
    """
    Finalizes a deed by etching the AI verdict directly to the Solana ledger.
    """
    if SIMULATION_MODE:
        log.info(f"[SIMULATION] Mocking 'etch_deed' for {deed_id}")
        return f"SIM_ETCH_{uuid.uuid4().hex[:8]}"

    global ANCHOR_PROGRAM
    if not ANCHOR_PROGRAM:
        await init_anchor_program()

    # Find PDA for the deed record
    deed_pda, _ = Pubkey.find_program_address(
        [b"deed", deed_id.encode("utf-8")],
        PROTOCOL_PROGRAM_ID
    )

    try:
        tx = await ANCHOR_PROGRAM.rpc["etchDeed"](
            deed_id, integrity_hash, impact_score, verdict,
            ctx=Context(
                accounts={
                    "deed_record": deed_pda,
                    "authority": MASTER_AUTHORITY_KEY.pubkey(),
                    "system_program": Pubkey.from_string("11111111111111111111111111111111"),
                },
                signers=[MASTER_AUTHORITY_KEY]
            )
        )
        log.info(f"[ANCHOR_TX] Integrity Etched: {deed_id} -> {tx}")
        return str(tx)
    except Exception as e:
        log.error(f"[ANCHOR_TX] Etch failed for {deed_id}: {e}")
        return None

async def confirm_transaction_status(tx_hash: str) -> str:
    if not tx_hash or tx_hash.startswith("SIM"):
        return "finalized"
    
    try:
        async with AsyncClient(RPC_URL) as client:
            status = await client.get_signature_statuses([tx_hash])
            if status.value[0] and status.value[0].confirmation_status:
                return str(status.value[0].confirmation_status)
            return "processing"
    except Exception:
        return "uncertain"

