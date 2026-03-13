from chatty_commander.web.routes.core import SystemStatus
from fastapi._compat.shared import annotation_is_pydantic_v1, is_pydantic_v1_model_class, lenient_issubclass
import pydantic.v1 as v1

print("SystemStatus:", SystemStatus)
print("Is pydantic v1 model class:", is_pydantic_v1_model_class(SystemStatus))
print("v1.BaseModel:", v1.BaseModel)
print("type of SystemStatus:", type(SystemStatus))
print("type of v1.BaseModel:", type(v1.BaseModel))
