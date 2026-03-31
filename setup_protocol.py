import asyncio
import json
import hashlib
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Idl, Program, Provider, Wallet, Context
from core.config import RPC_URL, MASTER_AUTHORITY_KEY, PROTOCOL_PROGRAM_ID, IDL_PATH, NOMAD_WALLET_SALT, log
from solders.pubkey import Pubkey
from solders.keypair import Keypair

async def setup_protocol():
    print("🚀 Initializing ProtoQol V4 Decentralized Protocol...")
    
    # Load IDL
    with open(IDL_PATH, "r") as f:
        idl_json = f.read()
    idl = Idl.from_json(idl_json)
    
    client = AsyncClient(RPC_URL, commitment=Confirmed)
    wallet = Wallet(MASTER_AUTHORITY_KEY)
    provider = Provider(client, wallet)
    program = Program(idl, PROTOCOL_PROGRAM_ID, provider)
    
    # 1. Initialize Protocol Stats (Global PDA)
    stats_pda, _ = Pubkey.find_program_address([b"stats"], PROTOCOL_PROGRAM_ID)
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
        print(f"✓ Protocol Initialized. TX: {tx}")
    except Exception as e:
        print(f"X Initialization failed (already initialized?): {e}")

    # 2. Register Biy Oracles (AUDITOR, SKEPTIC, COMPLIANCE)
    agents = ["AUDITOR", "SKEPTIC", "COMPLIANCE"]
    for agent in agents:
        seed = hashlib.sha256(f"BIY_{agent}_{NOMAD_WALLET_SALT}".encode()).digest()
        oracle_kp = Keypair.from_seed(seed)
        
        oracle_reg_pda, _ = Pubkey.find_program_address(
            [b"oracle", bytes(oracle_kp.pubkey())],
            PROTOCOL_PROGRAM_ID
        )
        
        try:
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
            print(f"✓ Biy Oracle Registered: {agent} ({oracle_kp.pubkey()}). TX: {tx}")
            
            # Airdrop some SOL to the oracle so it can vote
            print(f"  Requesting fuel for agent node {agent}...")
            await client.request_airdrop(oracle_kp.pubkey(), 1_000_000_000)
            
        except Exception as e:
            print(f"X Failed to register {agent}: {e}")

    print("\n✅ Decentralized Trust Protocol fully calibrated.")

if __name__ == "__main__":
    import os
    import sys
    # Add project root to path for imports
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(setup_protocol())
