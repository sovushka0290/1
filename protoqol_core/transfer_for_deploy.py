import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from core.config import MASTER_AUTHORITY_KEY, RPC_URL

async def main():
    cli_wallet = Pubkey.from_string("8tU7oXgQ9Uef2dcLHy9MdpxoaR5LRVfhRob73LV9CQSJ")
    async with AsyncClient(RPC_URL) as client:
        print(f"Transferring 3.0 SOL for deployment fuels...")
        tx = Transaction().add(transfer(TransferParams(
            from_pubkey=MASTER_AUTHORITY_KEY.pubkey(),
            to_pubkey=cli_wallet,
            lamports=3_000_000_000
        )))
        resp = await client.send_transaction(tx, MASTER_AUTHORITY_KEY)
        print(f"Transaction sent! TX: {resp.value}")
        print("Waiting for confirmation...")
        await asyncio.sleep(5)
        print("Fuel injected! You can now run: anchor deploy")

if __name__ == "__main__":
    asyncio.run(main())
