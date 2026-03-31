from pydantic import BaseModel, Field
from typing import Optional

class DeedRequest(BaseModel):
    description: str = Field(..., min_length=10, description="The ethical deed description")
    nomad_id: Optional[str] = Field(None, description="The ID of the human agent (Nomad)")
    mission_id: str = Field(..., description="The ID of the protocol mandate")
    source: Optional[str] = Field("API Gateway", description="Source of the request")

class CampaignCreate(BaseModel):
    fund_name: str = Field(..., min_length=3)
    title: str = Field(..., min_length=5)
    requirements: str = Field(..., min_length=10)
    reward: int = Field(..., ge=1)
    total_budget: int = Field(1000, ge=10)
    vault_address: str = Field("TBD")
