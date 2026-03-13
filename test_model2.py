import pytest
from fastapi import FastAPI
from chatty_commander.web.routes.core import SystemStatus, include_core_routes
import pydantic.v1 as v1

print("SystemStatus:", SystemStatus)
print("Type SystemStatus:", type(SystemStatus))
print("v1 BaseModel:", v1.BaseModel)
print("Type v1 BaseModel:", type(v1.BaseModel))
print("isinstance SystemStatus type:", isinstance(SystemStatus, type))

from fastapi._compat.shared import lenient_issubclass
try:
    print(lenient_issubclass(SystemStatus, v1.BaseModel))
except Exception as e:
    print(repr(e))
