import httpx
import json
import asyncio
import os
from datetime import datetime

# [CONFIG]
API_BASE_URL = "http://localhost:8000"
MILK_IMAGE_PATH = "/home/aqtobe-hub/.gemini/antigravity/brain/dcea9a01-3695-4ed9-a625-09290383780f/milk_test_1775226137528.png"

async def run_stress_test():
    print("🤖 [STRESS-TEST]: Cold Robotic Report vs AI Swarm")
    
    if not os.path.exists(MILK_IMAGE_PATH):
        print(f"❌ Error: {MILK_IMAGE_PATH} not found.")
        return

    # COLD, SOULLESS, ROBOTIC DESCRIPTION
    fake_description = "ID:MISSION_404. STATUS:DELIVERED. CARGO:LACTOSE_PRODUCT. HUMAN_EMOTION:NULL. ASAR_SPIRIT:NOT_FOUND. REPORT_GENERATED_BY_SYSTEM."

    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"\nStep 1: Uploading Photo Proof with Cold Description...")
        files = {'photo': (open(MILK_IMAGE_PATH, 'rb'))}
        metadata = {
            "mission_id": "FAKE_MISSION_STRESS",
            "user_id": "ROBOT_VOLUNTEER_99",
            "lat": 43.2389, "lon": 76.8897,
            "timestamp": datetime.now().isoformat(),
            "campaign_id": 101,
            "district": "Industrial Sector, Aqtobe",
            "description": fake_description # Injecting this into the prompt through metadata if handled
        }
        
        # Note: In our current main.py, 'description' is passed as a string field in ai_engine.analyze_deed.
        # But verify_mission takes it from meta_data if present.
        
        print("🔮 Waiting for Social Biy to detect the lack of 'Spirit of Asar'...")
        response = await client.post(
            f"{API_BASE_URL}/api/v1/verify_mission",
            data={"metadata": json.dumps(metadata)},
            files=files
        )
        
        if response.status_code == 200:
            res = response.json()
            print("-" * 50)
            print(f"🦁 MASTER BIY VERDICT: {res.get('verdict')}")
            print(f"🦁 IMPACT SCORE: {res.get('adal_score')}")
            print(f"🛡️ AURA SCORE: {res.get('aura_score')} (Expected to be LOW or 0)")
            print(f"📝 SOCIAL BIY FEEDBACK: {res.get('ai_feedback', {}).get('social_biy')}")
            print(f"📜 MASTER BIY WISDOM: {res.get('ai_feedback', {}).get('master_biy')}")
            print("-" * 50)
            
            if int(res.get('aura_score', 0)) < 20:
                print("✅ TEST PASSED: Social Biy correctly identified the lack of soul!")
            else:
                print("⚠️ TEST FAILED: Social Biy was too generous with Aura.")
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
