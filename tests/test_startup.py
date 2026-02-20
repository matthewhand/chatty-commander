
import time

import pytest

from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager
from chatty_commander.web.web_mode import create_app


@pytest.mark.slow
def test_startup_speed():
    """Test that startup completes in reasonable time.

    Note: This test is marked as 'slow' and may take longer in CI environments.
    The threshold is set conservatively to account for various environments.
    """
    start = time.time()
    config = Config()
    # Ensure config has minimal required fields to avoid validation errors
    if not hasattr(config, "web_server"):
        config.web_server = {"host": "0.0.0.0", "port": 8100}

    mm = ModelManager(config, mock_models=True)
    create_app(config=config, model_manager=mm, no_auth=True)
    duration = time.time() - start
    print(f"Startup took {duration:.4f}s")
    # Set conservative threshold for CI environments
    assert duration < 60.0
