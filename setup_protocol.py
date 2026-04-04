
import asyncio
import json
import hashlib
import sys
import os
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Idl, Program, Provider, Wallet, Context
from solders.pubkey import Pubkey
from solders.keypair import Keypair

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.config import RPC_URL, MASTER_AUTHORITY_KEY, PROTOCOL_PROGRAM_ID, IDL_PATH, NOMAD_WALLET_SALT, log

async def setup_protocol():
    print("--- [DEBUG] Starting ProtoQol V4 Setup Script ---")
    
    # 1. Load IDL
    print(f"-> Loading IDL from {IDL_PATH}...")
    try:
        with open(IDL_PATH, "r") as f:
            idl_json = f.read()
        idl = Idl.from_json(idl_json)
        print("   ✓ IDL loaded successfully.")
    except Exception as e:
        print(f"   X CRITICAL: Failed to load IDL: {e}")
        return

    # 2. Initialize RPC Client with Timeout
    print(f"-> Initializing AsyncClient (devnet) with 30s timeout...")
    client = AsyncClient(RPC_URL, commitment=Confirmed, timeout=30.0)
    wallet = Wallet(MASTER_AUTHORITY_KEY)
    provider = Provider(client, wallet)
    program = Program(idl, PROTOCOL_PROGRAM_ID, provider)
    print(f"   ✓ Client & Program context ready. Program ID: {PROTOCOL_PROGRAM_ID}")

    # 3. Initialize Protocol Stats PDA
    stats_pda, _ = Pubkey.find_program_address([b"stats"], PROTOCOL_PROGRAM_ID)
    print(f"-> Initializing Global Stats PDA: {stats_pda}...")
    try:
        tx = await program.rpc["initialize_protocol"](
            ctx=Context(
                accounts={
                    "stats": stats_pda,
                    "admin": MASTER_AUTHORITY_KEY.pubkey(),
                    "system_program": Pubkey.from_string("11111111111111111111111111111111"),
                },
                signers=[MASTER_AUTHORITY_KEY]
            )
        )
        print(f"   ✓ Protocol Stats Initialized. TX: {tx}")
    except Exception as e:
        err_msg = str(e).lower()
        if "already in use" in err_msg or "already initialized" in err_msg or "0x0" in err_msg:
             print("   ✓ Protocol Stats already active. (Skipping)")
        else:
             print(f"   ! Warning/Error in Stats Init: {e}")

    # 4. Register Biy Oracles (AUDITOR, SKEPTIC, SOCIAL_BIY)
    agents = ["AUDITOR", "SKEPTIC", "SOCIAL_BIY"]
    for agent in agents:
        print(f"-> Processing Biy Oracle: {agent}...")
        seed = hashlib.sha256(f"BIY_{agent}_{NOMAD_WALLET_SALT}".encode()).digest()
        oracle_kp = Keypair.from_seed(seed)
        
        oracle_reg_pda, _ = Pubkey.find_program_address(
            [b"oracle", bytes(oracle_kp.pubkey())],
            PROTOCOL_PROGRAM_ID
        )
        
        try:
            print(f"   ~ Registering Node {oracle_kp.pubkey()}...")
            tx = await program.rpc["add_oracle"](
                oracle_kp.pubkey(),
                ctx=Context(
                    accounts={
                        "oracle_registry": oracle_reg_pda,
                        "admin": MASTER_AUTHORITY_KEY.pubkey(),
                        "system_program": Pubkey.from_string("11111111111111111111111111111111"),
                    },
                    signers=[MASTER_AUTHORITY_KEY]
                )
            )
            print(f"   ✓ {agent} Registered Successfully. TX: {tx}")
        except Exception as e:
            err_msg = str(e).lower()
            if "already in use" in err_msg or "already initialized" in err_msg or "0x0" in err_msg:
                 print(f"   ✓ {agent} node already active. (Skipping)")
            else:
                 print(f"   X Failed to register {agent}: {e}")

    print("\n✅ DECENTRALIZED PROTOCOL FULLY CALIBRATED & READY.")
    await client.close()

if __name__ == "__main__":
    asyncio.run(setup_protocol())
