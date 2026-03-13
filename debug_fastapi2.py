from chatty_commander.web.routes.core import SystemStatus
from fastapi._compat.shared import annotation_is_pydantic_v1, is_pydantic_v1_model_class, lenient_issubclass

print(annotation_is_pydantic_v1(SystemStatus))
