from fastapi._compat.shared import lenient_issubclass
from pydantic import BaseModel

print(lenient_issubclass("string_type", BaseModel))
print(lenient_issubclass(BaseModel, BaseModel))
