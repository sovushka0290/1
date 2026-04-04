# 🧬 ProtoQol: The Decentralized Integrity Engine

[![Solana Devnet](https://img.shields.io/badge/Network-Solana_Devnet-blueviolet?style=for-the-badge&logo=solana)](https://explorer.solana.com/)
[![AI Consensus](https://img.shields.io/badge/AI_Engine-Gemini_2.0_Flash-blue?style=for-the-badge&logo=google-gemini)](https://deepmind.google/technologies/gemini/)
[![B2B Integrity](https://img.shields.io/badge/Sector-B2B_SaaS_RegTech-white?style=for-the-badge)](https://protoqol.vercel.app/)

**ProtoQol** is a high-fidelity integrity orchestration layer that bridges corporate ESG (Environmental, Social, and Governance) claims with on-chain reality. By combining a **Multi-Agent AI Swarm (Q-AI Compass)** and the **Solana Blockchain**, we eliminate "Impact Washing" and transform social good into verifiable, immutable digital assets.

---

## 🏛️ System Architecture

### 1. The Q-AI Compass (Three-Tier Verification)
Unlike traditional static check-boxes, ProtoQol utilizes a dynamic **Zero-Trust Neural Audit**:
*   **Layer 0: Deterministic Shield**: Haversine Geo-fencing, ISO Time-Window validation, and a Keyword Fraud Gate.
*   **Layer 1: The Biy Council (Swarm)**: 
    - 🧾 **Accountant node**: Detects financial anomalies and price-gouging.
    - 👁️ **Visual Logic node**: Evaluates if the reported action is physically and logically possible.
    - 🤝 **Ethical HR node**: Assesses social sincerity and potential exploitation.
*   **Layer 2: Quorum Gate**: A decentralized consensus where 2/3 agents must agree. The Accountant node holds **VETO** power over financial irregularities.
*   **Layer 3: Final Synthesis**: The *Master Biy* agent synthesizes a final verdict, assigns an **Impact Score**, and attaches a traditional Kazakh wisdom relevant to the action.

### 2. Integrity Ledger (Solana Program)
All verified deeds are etched into the **Solana Devnet** as immutable records:
*   **Program ID**: `EdrjHLN9K9eogJ5Pui8WYJRAghdN4knAdAoDcZesAirc`
*   **Consensus Mechanism**: Vested oracles (AI nodes) submit `ADAL` (Truth) or `ARAM` (Deception) votes.
*   **Escrow Logic**: Rewards are locked in PDA accounts and only released to the *Nomad* (contributor) upon 3 successfully verified AI votes.

---

## 🚀 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Blockchain** | Solana / Anchor (Rust) |
| **Backend** | Python 3.12 / FastAPI / Pydantic |
| **AI Intelligence** | Gemini 2.0 Flash / Agentic Swarm Architecture |
| **Frontend** | Vanilla JS / GSAP / Nomad Cyberpunk UI |
| **Database** | SQLite (Metadata Mirroring) |

---

## 🛠️ Quick Start (Local Development)

### 1. Prerequisites
*   Node.js & npm (for UI)
*   Python 3.12+
*   Solana CLI & Anchor (for contract interaction)

### 2. Backend Setup
```bash
cd api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

### 3. Deploy/Anchor Setup
```bash
cd api/protoqol_core
anchor build
anchor deploy --provider.cluster devnet
```

### 4. UI Launch
The UI is a self-contained high-fidelity experience. Simply serve the `index.html` from the root or the `api` folder.
```bash
# Using Python to host locally
python3 -m http.server 8000
```

---

## 📡 Oracle & Protocol Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/deeds/verify` | `POST` | Triggers the 3-layer AI Swarm audit. |
| `/api/v1/missions/active` | `GET` | Fetches live ESG missions from the ledger. |
| `/api/v1/oracle/consensus` | `GET` | Returns real-time quorum status of a deed. |

---

## 🔐 Security & Privacy
*   **PII Scrubbing**: Automatic redaction of phone numbers, emails, and card details before AI processing.
*   **Prompt Injection Protection**: Hardened system prompts with `[SECURITY_DIRECTIVE]` overrides.
*   **Deterministic Fallbacks**: Local mock-wisdoms and quorum-lost guards ensure protocol uptime during high latency.

---

### 🏆 Hackathon Context
Created for the **Decentrathon / Solana Hackathon** to prove that integrity isn't just a mission statement—it's a verifiable, on-chain mathematical constant.

**ProtoQol: Honesty is the only asset that doesn't depreciate.**
