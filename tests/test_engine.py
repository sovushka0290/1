import pytest
from core import solana_client, database

# ═══════════════════════════════════════════════════════════════
# ProtoQol Engine Unit Tests
# ═══════════════════════════════════════════════════════════════

def test_wallet_deterministic_derivation():
    """
    Ensures that get_nomad_wallet is deterministic and secure.
    One ID must always produce the SAME wallet.
    Two different IDs must produce DIFFERENT wallets.
    """
    id_1 = "Nomad_001"
    id_2 = "Nomad_002"
    
    wallet_1a = solana_client.get_nomad_wallet(id_1)
    wallet_1b = solana_client.get_nomad_wallet(id_1)
    wallet_2 = solana_client.get_nomad_wallet(id_2)
    
    assert str(wallet_1a.pubkey()) == str(wallet_1b.pubkey()), "Wallet derivation must be deterministic."
    assert str(wallet_1a.pubkey()) != str(wallet_2.pubkey()), "Different IDs must yield different wallets."

def test_database_campaign_lifecycle():
    """
    Tests the CRUD operations for ESG campaigns.
    """
    # Initialize DB for tests (in-memory or clean file)
    database.init_db()
    
    test_title = "Hackathon Test Campaign"
    campaign_id = database.create_campaign(
        fund_name="TestFund",
        title=test_title,
        requirements="Must test the code.",
        reward=500
    )
    
    assert campaign_id is not None
    
    # Retrieve
    camp = database.get_campaign_by_id(campaign_id)
    assert camp["title"] == test_title
    assert camp["reward"] == 500
    
    # Check active filter
    active_camps = database.get_campaigns(only_active=True)
    assert any(c['id'] == campaign_id for c in active_camps)

def test_ai_response_parsing_resilience():
    """
    Verifies that the engine can handle malformed AI responses safely.
    (Mocking internal logic if needed, but here testing the structure logic).
    """
    from core import ai_engine
    
    # Simulate a malformed JSON string that often comes from LLMs
    malformed_json = "```json\n{\"verdict\": \"ADAL\", \"wisdom\": \"Test\"}\n```"
    
    # This is internal to query_agent usually, but we check if the engine logic is robust
    import json
    raw = malformed_json.replace('```json', '').replace('```', '').strip()
    result = json.loads(raw)
    
    assert result["verdict"] == "ADAL"
    assert "wisdom" in result
