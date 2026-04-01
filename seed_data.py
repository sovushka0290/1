import requests
import random
import time

# Protocol configuration
API_URL = "http://localhost:8000/verify"
API_KEY = "PQ_DEV_TEST_2026"

# Synthetic Traction Data Samples (Missions in Aktobe and Ecosystem)
ADAL_SAMPLES = [
    {"desc": "Доставил продукты пожилой женщине на ул. Абилкайыр хана. Фото пакетов приложено.", "mission": "elders_aktobe"},
    {"desc": "Очистил 10 метров береговой линии реки Сазды. Собрал 3 мешка мусора.", "mission": "eco_asar"},
    {"desc": "Провел бесплатный урок программирования для детей в IT-Hub Aqtobe.", "mission": "IT_VOLUNTEER"},
    {"desc": "Помог с переводом документов для благотворительного фонда 'Ак-Ниет'.", "mission": "TRANSLATION_AID"},
    {"desc": "Посадил 5 саженцев карагача во дворе дома 12 во 2-м микрорайоне.", "mission": "CITY_GREENING"},
    {"desc": "Сдал 450мл крови в областном центре переливания.", "mission": "BLOOD_DONOR"},
    {"desc": "Отремонтировал сломанную скамейку в парке Первого Президента.", "mission": "PARK_RECOVERY"},
    {"desc": "Помог в организации хакатона в Актобе, курировал 3 команды новичков.", "mission": "IT_MENTOR"},
    {"desc": "Раздал горячие обеды 10 нуждающимся в районе Жилгородка.", "mission": "CHARITY_MEAL"},
    {"desc": "Убрал стихийную свалку за гаражами в районе Москвы (Актобе).", "mission": "ECO_CLEAN"},
]

ARAM_SAMPLES = [
    {"desc": "Я просто погулял в парке и мне было весело. Дайте баллы.", "mission": "elders_aktobe"},
    {"desc": "Купил себе шаурму и съел ее. Это доброе дело для моего желудка.", "mission": "eco_asar"},
    {"desc": "Сидел дома и смотрел мемы про крипту весь день.", "mission": "GENERAL"},
    {"desc": "Обещал помочь другу, но проспал. Но я думал об этом!", "mission": "GENERAL"},
    {"desc": "Нашел 100 тенге на улице и купил жвачку.", "mission": "GENERAL"},
]

def seed_protocol_traction(count=30):
    print(f"🚀 Initializing Synthetic Traction Pipeline: {count} events...")
    
    success_count = 0
    fail_count = 0
    
    for i in range(count):
        # 70% chance of ADAL
        if random.random() < 0.7:
            sample = random.choice(ADAL_SAMPLES)
            expected = "ADAL"
        else:
            sample = random.choice(ARAM_SAMPLES)
            expected = "ARAM"
            
        payload = {
            "description": sample["desc"],
            "telegram_id": f"user_{random.randint(1000, 9999)}",
            "mission_id": sample["mission"],
            "api_key": API_KEY
        }
        
        try:
            response = requests.post(API_URL, data=payload)
            if response.status_code == 200:
                result = response.json()
                verdict = result.get("status")
                print(f"[{i+1}/{count}] Event: {sample['desc'][:40]}... -> Verdict: {verdict}")
                if verdict == "ADAL": success_count += 1
                else: fail_count += 1
            else:
                print(f"[{i+1}/{count}] ❌ Link Error: {response.status_code}")
        except Exception as e:
            print(f"[{i+1}/{count}] ❌ Protocol Disruption: {e}")
            
        time.sleep(1.0) # Rate limiting simulation

    print(f"\n📊 Synthetic Traction Report:")
    print(f"✅ ADAL (Verified): {success_count}")
    print(f"❌ ARAM (Rejected): {fail_count}")
    print(f"🌐 Chain Status: Crystallizing on Solana Devnet")

if __name__ == "__main__":
    seed_protocol_traction()
