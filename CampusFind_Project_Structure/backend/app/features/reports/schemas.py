from datetime import datetime
from pydantic import BaseModel, Field

class ReportCreate(BaseModel):
    item_name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=3000)
    occurred_at: datetime
    location: str = Field(min_length=1, max_length=200)
    custody_location: str = Field(default='', max_length=200)
