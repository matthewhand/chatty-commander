from fastapi import APIRouter
from chatty_commander.web.routes.core import SystemStatus
from fastapi.routing import APIRoute
from fastapi._compat.shared import annotation_is_pydantic_v1, is_pydantic_v1_model_class, lenient_issubclass

print("Type:", type(SystemStatus))
print("Dict annotation:", SystemStatus.__annotations__)

router = APIRouter()
router.add_api_route("/status", lambda: {}, response_model=SystemStatus)
