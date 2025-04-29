from pydantic import BaseModel
from typing import Optional, List

class CompanyInfo(BaseModel):
    name: str
    business_type: str  # "residential", "commercial", "both"
    chatbot_style: str  # "professional", "friendly", "luxury"
    preferred_properties: Optional[List[str]] = None

class PropertyData(BaseModel):
    raw_data: str  # CSV/JSON content
    summary: Optional[str] = None
    issues: Optional[List[str]] = None