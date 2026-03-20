from fastapi import APIRouter
from chatty_commander.web.routes.core import SystemStatus

router = APIRouter()

@router.get("/api/v1/status", response_model=SystemStatus)
def status():
    pass
