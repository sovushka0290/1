import httpx
import json
import asyncio
import os
import hashlib
from datetime import datetime

# [CONFIG]
API_BASE_URL = "http://localhost:8000"  # ProtoQol FastAPI
MILK_IMAGE_PATH = "/home/aqtobe-hub/.gemini/antigravity/brain/dcea9a01-3695-4ed9-a625-09290383780f/milk_test_1775226137528.png" 

# Mock Metadata
MISSION_ID = "MILK_404_ASAR"
USER_ID = "777000" # Simulating Lead Volunteer
LAT, LON = 43.2389, 76.8897 # Aqtobe/Almaty coordinate spoof

async def run_operation_milk():
    print("🥛 [OPERATION MILK]: Zero-Trust Headless E2E Started")
    print(f"📡 Target Oracle: {API_BASE_URL}")
    
    if not os.path.exists(MILK_IMAGE_PATH):
        print(f"❌ Error: {MILK_IMAGE_PATH} not found. Generate it first!")
        return

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Phase 1: Health Check
        print("\nStep 1: Pinging AI Oracle Health...")
        try:
            resp = await client.get(f"{API_BASE_URL}/health")
            print(f"✅ Oracle Status: {resp.json()}")
        except Exception as e:
            print(f"❌ Oracle Offline: {e}")
            return

        # Phase 2: Neural Audit (The Core Test)
        print(f"\nStep 2: Uploading Photo Proof ({MILK_IMAGE_PATH})...")
        files = {
            'photo': (MILK_IMAGE_PATH, open(MILK_IMAGE_PATH, 'rb'), 'image/jpeg')
        }
        
        metadata = {
            "mission_id": MISSION_ID,
            "user_id": USER_ID,
            "lat": LAT,
            "lon": LON,
            "timestamp": datetime.now().isoformat(),
            "district": "Astana District, Aqtobe",
            "campaign_id": 101
        }
        
        data = {
            "metadata": json.dumps(metadata)
        }

        print("🔮 Waiting for Council of Biys consensus...")
        start_time = datetime.now()
        
        response = await client.post(
            f"{API_BASE_URL}/api/v1/verify_mission",
            data=data,
            files=files
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            res = response.json()
            print(f"✅ AI Audit Completed in {duration:.2f}s")
            print("-" * 50)
            print(f"🦁 MASTER BIY VERDICT: {res.get('verdict')}")
            print(f"☪️ WISDOM: {res.get('wisdom')}")
            print(f"📊 IMPACT SCORE: {res.get('impact_score')}")
            print(f"📝 REASONING: {res.get('final_reasoning') or res.get('reasoning')}")
            print(f"⛓ INTEGRITY HASH: {res.get('integrity_hash')[:16]}...")
            print("-" * 50)
            
            if res.get('verdict') == "ADAL":
                print("🏆 SUCCESS: The milk was recognized as AUTHENTIC.")
            else:
                print("⚠️ ALERT: Skeptic detected an anomaly in the milk proof!")
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")

        # Phase 3: Check Data Records
        print("\nStep 3: Checking System Logs...")
        pulse_resp = await client.get(f"{API_BASE_URL}/api/v1/deeds/recent")
        if pulse_resp.status_code == 200:
            deeds = pulse_resp.json().get("deeds", [])
            my_deed = next((d for d in deeds if d.get("mission_id") == MISSION_ID), None)
            if my_deed:
                 print(f"✅ Pulse Record Found: {my_deed['verdict']} | TX: {my_deed.get('tx_hash', 'PENDING')}")
            else:
                 print("⚠️ Record not found in recent deeds (Persistence delay?)")

if __name__ == "__main__":
    asyncio.run(run_operation_milk())
