from fastapi import APIRouter
from chatty_commander.web.routes.core import SystemStatus

router = APIRouter()
print('router created')
@router.get("/api/v1/status", response_model=SystemStatus)
def get_status():
    return {}
print('route added')
