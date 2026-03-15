from fastapi import FastAPI
from chatty_commander.web.routes.core import include_core_routes
from unittest.mock import MagicMock
import time
app = FastAPI()

router = include_core_routes(
    get_start_time=lambda: time.time(),
    get_state_manager=lambda: MagicMock(),
    get_config_manager=lambda: MagicMock(),
    get_last_command=lambda: None,
    get_last_state_change=lambda: time.time(),
    execute_command_fn=MagicMock(),
)

app.include_router(router)
print("router loaded")
