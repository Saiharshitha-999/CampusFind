from pydantic import BaseModel, Field

class ClaimCreate(BaseModel):
    item_id: int
    proof_description: str = Field(min_length=1, max_length=3000)
