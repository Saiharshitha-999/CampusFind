from pydantic import BaseModel, Field

class ClaimCreate(BaseModel):
    proof_reference: str = Field(min_length=1, max_length=255)
