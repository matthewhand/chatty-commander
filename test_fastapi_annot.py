from __future__ import annotations

from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import fastapi

app = FastAPI()

class Item(BaseModel):
    name: str

@app.get("/", response_model=Item)
def read_root():
    return {"name": "hello"}

print(fastapi.__version__)
