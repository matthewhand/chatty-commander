import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

from chatty_commander.app.config import Config
from chatty_commander.app.model_manager import ModelManager


class TestModelManager:
    def test_init(self):
        config = Config()
        mm = ModelManager(config)
        assert hasattr(mm, "config")
        assert hasattr(mm, "models")

    def test_reload_models(self):
        config = Config()
        mm = ModelManager(config)
        with patch('chatty_commander.app.model_manager.Model', return_value=MagicMock()):
            models = mm.reload_models('idle')
            assert isinstance(models, dict)

    def test_reload_models_invalid_state(self):
        config = Config()
        mm = ModelManager(config)
        with patch('chatty_commander.app.model_manager.Model', return_value=MagicMock()):
            models = mm.reload_models('invalid')
            assert models == {}

    def test_listen_for_commands(self):
        config = Config()
        mm = ModelManager(config)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = asyncio.run(mm.listen_for_commands())
        assert result is None or isinstance(result, str)

        #     def test_hot_reload(self, tmp_path):
        #         config = Config()
        #         config.general_models_path = os.path.join(tmp_path, "general")
        #         config.system_models_path = os.path.join(tmp_path, "system")
        #         config.chat_models_path = os.path.join(tmp_path, "chat")
        #         for p in [config.general_models_path, config.system_models_path, config.chat_models_path]:
        #             os.makedirs(p, exist_ok=True)
        #         mm = ModelManager(config)
        #         with patch("model_manager.Model", return_value=MagicMock()):
        #             async def run():
        #                 await mm.start_watching()
        #                 model_file = os.path.join(config.general_models_path, "new.onnx")
        #                 open(model_file, "w").close()
        #                 await asyncio.sleep(0.2)
        #                 assert "new" in mm.models["general"]
        #                 await mm.stop_watching()

        #             asyncio.run(run())

        # Should not raise, but returns None or str
        result = asyncio.run(mm.async_listen_for_commands())
        assert result is None or isinstance(result, str)

    def test_hot_reload_detects_new_model(self, tmp_path):
        cfg = Config()
        model_dir = tmp_path / "models"
        model_dir.mkdir()
        cfg.general_models_path = str(model_dir)
        (model_dir / "first.onnx").write_text("dummy")
        mm = ModelManager(cfg)
        assert "first" in mm.models["general"]
        (model_dir / "second.onnx").write_text("dummy2")

        async def _run():
            await asyncio.gather(
                mm.async_listen_for_commands(),
                asyncio.to_thread(mm.reload_models, "idle"),
            )

        asyncio.run(_run())
        assert "second" in mm.models["general"]
