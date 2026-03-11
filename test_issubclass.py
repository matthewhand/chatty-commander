import sys
from pydantic import BaseModel

print(sys.version)

class MyModel(BaseModel):
    name: str

print(issubclass(MyModel, BaseModel))
