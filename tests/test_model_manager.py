import asyncio
import os
from unittest.mock import MagicMock, patch, AsyncMock

from model_manager import ModelManager

from src.chatty_commander.config import Config


class TestModelManager:
    def test_init(self):
        config = Config()
        mm = ModelManager(config)
        assert hasattr(mm, "config")
        assert hasattr(mm, "models")

    def test_reload_models(self):
        config = Config()
        mm = ModelManager(config)
        with patch("model_manager.Model", return_value=MagicMock()):
            models = asyncio.run(mm.reload_models("idle"))
            assert isinstance(models, dict)

    def test_reload_models_invalid_state(self):
        config = Config()
        mm = ModelManager(config)
        with patch("model_manager.Model", return_value=MagicMock()):
            models = asyncio.run(mm.reload_models("invalid"))
            assert models == {}

    def test_listen_for_commands(self):
        config = Config()
        mm = ModelManager(config)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.run(mm.listen_for_commands())
        assert result is None or isinstance(result, str)

    def test_hot_reload(self, tmp_path):
        config = Config()
        config.general_models_path = os.path.join(tmp_path, "general")
        config.system_models_path = os.path.join(tmp_path, "system")
        config.chat_models_path = os.path.join(tmp_path, "chat")
        for p in [config.general_models_path, config.system_models_path, config.chat_models_path]:
            os.makedirs(p, exist_ok=True)
        mm = ModelManager(config)
        with patch("model_manager.Model", return_value=MagicMock()):
            async def run():
                await mm.start_watching()
                model_file = os.path.join(config.general_models_path, "new.onnx")
                open(model_file, "w").close()
                await asyncio.sleep(0.2)
                assert "new" in mm.models["general"]
                await mm.stop_watching()

            asyncio.run(run())
