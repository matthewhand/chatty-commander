import asyncio
from pydantic import BaseModel, Field

class SystemStatus(BaseModel):
    status: str = Field(..., description="Overall system status")
    current_state: str = Field(..., description="Current operational state")
    active_models: list[str] = Field(..., description="List of loaded models")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(default="0.2.0", description="Application version")

from fastapi import FastAPI, APIRouter
router = APIRouter()
@router.get("/api/v1/status", response_model=SystemStatus)
async def status():
    return {"status": "ok"}
