from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

class SystemStatus(BaseModel):
    status: str = Field(description="Overall system status")
    current_state: str = Field(description="Current operational state")
    active_models: list[str] = Field(description="List of loaded models")
    uptime: str = Field(description="System uptime")
    version: str = Field(default="0.2.0", description="Application version")

@router.get('/', response_model=SystemStatus)
def test():
    pass
