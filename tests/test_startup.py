
import time
from chatty_commander.web.web_mode import create_app
from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager

def test_startup_speed():
    start = time.time()
    config = Config()
    # Ensure config has minimal required fields to avoid validation errors
    if not hasattr(config, "web_server"):
        config.web_server = {"host": "0.0.0.0", "port": 8100}

    mm = ModelManager(config, mock_models=True)
    create_app(config=config, model_manager=mm, no_auth=True)
    duration = time.time() - start
    print(f"Startup took {duration:.4f}s")
    assert duration < 2.0
