import re
import json
import os
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import get_next_engine_api_key, log

def parse_biy_verdict(raw_llm_output):
    """
    Бронебойный парсер: вытаскивает JSON из любого ответа Master Biy.
    """
    try:
        if not raw_llm_output:
            raise ValueError("Empty LLM output")

        # Пытаемся найти кусок текста, который начинается с { и заканчивается на }
        # Convert to string if it's a CrewAI output object
        raw_text = str(raw_llm_output)
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            clean_text = match.group(0)
            return json.loads(clean_text)
        
        # Если регулярка не сработала, пробуем распарсить как есть
        return json.loads(raw_text)
        
    except (json.JSONDecodeError, ValueError, Exception) as e:
        # Если ИИ выдал полную кашу, возвращаем дефолтный ARAM, чтобы сервер НЕ УПАЛ
        log.error(f"КРИТИЧЕСКАЯ ОШИБКА ПАРСИНГА: {e} | Raw: {raw_llm_output}")
        return {
            "status": "ARAM",
            "confidence_score": 0,
            "biy_wisdom": "System Error: Нарушение формата консенсуса. Требуется ручная проверка."
        }

# ACT AS: Senior AI/Python Architect
# OBJECTIVE: Refactor ProtoQol verify_deed logic with CrewAI Multi-Agent Orchestration

# ═══════════════════════════════════════════════════════════════
# ETHICAL LEXICON (The Oracle's Dictionary)
# ═══════════════════════════════════════════════════════════════
ETHICAL_LEXICON = {
    "ADAL": {  # Positive Keywords (Steppe Integrity)
        "доставил": 15, "клиника": 20, "помощь": 10, "волонтер": 15, "экология": 10, 
        "отчет": 5, "подтверждение": 5, "дерево": 10, "посадил": 15, "накормил": 15, 
        "собрал": 10, "пожертвовал": 20, "спасение": 15, "бесплатно": 10, "добро": 15
    },
    "ARAM": { # Negative Keywords (Shadow Logic)
        "взятка": -100, "обман": -50, "фейк": -40, "деньги": -10, "купил": -20, 
        "криминал": -100, "оружие": -100, "наркотики": -100, "казино": -80, "террор": -100
    }
}

def calculate_lexical_integrity(text: str) -> tuple[int, list]:
    """
    Scans text for ethical markers and correlates them into a base integrity score.
    """
    score = 40 # Base neutrality
    matches = []
    text_lower = text.lower()
    
    for word, weight in ETHICAL_LEXICON["ADAL"].items():
        if word in text_lower:
            score += weight
            matches.append(f"+{word}")
    
    for word, weight in ETHICAL_LEXICON["ARAM"].items():
        if word in text_lower:
            score += weight
            matches.append(f"!{word}")
            
    return min(max(score, 0), 100), matches

def run_biy_council(deed_data: dict):
    """
    Executes the 'Zheti Zhargy' Triple-Agent Consensus.
    """
    api_key = get_next_engine_api_key()
    if not api_key:
        return {"status": "ARAM", "confidence_score": 0, "biy_wisdom": "API Key Missing. The Oracle is silent."}

    # 0. LEXICAL PRE-PROCESSING
    base_integrity, lexical_matches = calculate_lexical_integrity(deed_data.get('description', ''))
    log.info(f"[ENGINE_ORACLE] Lexical Scan: {base_integrity}% | Matches: {lexical_matches}")

    # 1. Initialize Gemini 2.0 Flash for High-Speed Reasoning
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        api_key=api_key,
        temperature=0.1
    )

    # 2. THE AGENTS (The AI-Biy Council)
    
    auditor = Agent(
        role='The Auditor',
        goal='Objectively describe what is in the provided ESG report and metadata.',
        backstory='You are a meticulous forensic auditor trained to extract raw facts from user reports. You do not judge, you only document.',
        allow_delegation=False,
        llm=llm,
        verbose=True
    )

    skeptic = Agent(
        role='The Skeptic',
        goal='Actively look for anomalies, fraud, or mismatches in the ESG report.',
        backstory='You are a professional cynic. You look for inconsistencies between the description, the mission requirements, and potential stock images. If something looks too good to be true, you flag it.',
        allow_delegation=False,
        llm=llm,
        verbose=True
    )

    master_biy = Agent(
        role='Master Biy (Final Judge)',
        goal='Review the Auditor\'s facts and the Skeptic\'s doubts. Form a final verdict based on Digital Steppe Law.',
        backstory='You are the embodiment of ancestral wisdom and modern compliance. You synthesize the council\'s opinions into a final, immutable verdict. Your word is law.',
        allow_delegation=True,
        llm=llm,
        verbose=True
    )

    # 3. THE TASK
    
    processing_task = Task(
        description=f"""
        Process the following ESG Report with Integrity Benchmarks:
        - User Report: {deed_data.get('description')}
        - Mission Mandate: {deed_data.get('mission_requirements')}
        - Lexical Integrity Base: {base_integrity}% (Matches: {lexical_matches})
        - Context: {json.dumps(deed_data.get('metadata', {}))}

        Step 1: Auditor must list the facts and confirm Lexical matches.
        Step 2: Skeptic must analyze any mismatch between the Base Integrity and report claims.
        Step 3: Master Biy must synthesize everything for a final Digital Steppe Law verdict.
        """,
        expected_output="""
        A strictly formatted JSON object:
        {
            "status": "ADAL" or "ARAM",
            "confidence_score": 0-100,
            "biy_wisdom": "A single sentence Kazakh-inspired wisdom summarizing the result"
        }
        """,
        agent=master_biy
    )

    # 4. THE CREW
    
    council = Crew(
        agents=[auditor, skeptic, master_biy],
        tasks=[processing_task],
        process=Process.sequential, # Step-by-step consensus
        verbose=True
    )

    # 5. EXECUTION
    
    try:
        log.info(f"[CREW_AI] Awakening the Council for: {deed_data.get('description')[:30]}...")
        result_raw = council.kickoff()
        
        # Ensure result is clean JSON using the robust parser
        return parse_biy_verdict(result_raw)
        
    except Exception as e:
        log.error(f"[CREW_AI] Council Dispute: {e}")
        return {
            "status": "ARAM",
            "confidence_score": 0,
            "biy_wisdom": "A storm has clouded the vision of the council."
        }
