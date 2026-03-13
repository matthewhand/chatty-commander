from pydantic import BaseModel

class MyModel(BaseModel):
    name: str

import pydantic.v1 as v1

print(isinstance(v1.BaseModel, type))
print(type(v1.BaseModel))
