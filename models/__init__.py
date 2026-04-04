from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

Base = declarative_base()

# --- STATE ENUMS (The Oracle State Machine) ---

class UserState(str, PyEnum):
    IDLE = "IDLE"                   # Tavern/Online — free for work
    ASSEMBLY = "ASSEMBLY"           # Joining a team, awaiting peer confirmation
    IN_TRANSIT = "IN_TRANSIT"       # Active mission delivery (HUD Locked)
    VALIDATION = "VALIDATION"       # Reporting, awaiting AI/Peer verification

class MissionState(str, PyEnum):
    MARKETPLACE = "MARKETPLACE"           # Open bounty
    ASSEMBLING = "ASSEMBLING"             # Coordinator assigned, gathering peers
    IN_PROGRESS = "IN_PROGRESS"           # Delivery active, contact data revealed
    AWAITING_RECEIVER = "AWAITING_RECEIVER" # Delivery done, awaiting recipient double-check
    VERIFIED = "VERIFIED"                 # Consensus reached, SBT rewarded

# --- ORACLE MODELS (PostgreSQL Persistence) ---

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    state = Column(Enum(UserState), default=UserState.IDLE)
    role = Column(String, default="GUEST") # GUEST, MEMBER, COACH, ADMIN
    sbt_balance = Column(Integer, default=0)
    trust_score = Column(Float, default=100.0)
    registration_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    teams = relationship("Team", back_populates="user")

class Mission(Base):
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True)
    mission_id = Column(String, unique=True, index=True) # External ID hash 
    title = Column(String)
    description = Column(String)
    state = Column(Enum(MissionState), default=MissionState.MARKETPLACE)
    
    # JIT Privacy Data (Protected by Zero-Trust)
    target_address = Column(String) # Hidden until IN_PROGRESS
    target_phone = Column(String)   # Hidden until IN_PROGRESS
    lat = Column(Float)
    lon = Column(Float)
    
    cargo_type = Column(String, default="HUMANITARIAN_AID")
    reward_sbt = Column(Integer, default=20)
    
    coordinator_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(String) # Telegram ID of the beneficiary
    
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    
    # Consensus Logs
    integrity_hash = Column(String, nullable=True)
    consensus_logs = Column(JSON, nullable=True) # Swarm reports (Auditor, Skeptic, Master Biy)

class Team(Base):
    """Bridges Users to Missions (Team verification requirement)"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_confirmed = Column(Boolean, default=False) # Used for Peer-Approval state machine
    
    user = relationship("User", back_populates="teams")

# --- PYDANTIC SCHEMAS (API DTOs) ---

class VerificationMetadata(BaseModel):
    user_id: str
    mission_id: str
    lat: float
    lon: float
    timestamp: Optional[str] = None
    role: str = "COORDINATOR"
    photo_hash: Optional[str] = None

class VerificationResponse(BaseModel):
    status: str # 'ADAL' or 'ARAM'
    verdict: str
    adal_score: float
    integrity_hash: str
    ai_feedback: Dict[str, Any]
    solana_tx: Optional[str] = None
