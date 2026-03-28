import os
import importlib
import sys
import pytest

def test_pytest_collection():
    from pydantic import BaseModel
    from fastapi._compat.shared import annotation_is_pydantic_v1
    class SystemStatus(BaseModel):
        status: str

    for root, dirs, files in os.walk("tests"):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                mod_name = os.path.join(root, file).replace("/", ".")[:-3]
                try:
                    importlib.import_module(mod_name)
                except Exception:
                    continue
                try:
                    annotation_is_pydantic_v1(SystemStatus)
                except TypeError:
                    print(f"FAILED AFTER IMPORTING: {mod_name}")
                    return
    print("ALL TESTS IMPORTED, NO ERROR!")

test_pytest_collection()
