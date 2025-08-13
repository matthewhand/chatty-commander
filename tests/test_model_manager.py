from unittest.mock import MagicMock, patch

from chatty_commander.app.model_manager import ModelManager

from chatty_commander.app.config import Config


class TestModelManager:
    def test_init(self):
        config = Config()
        mm = ModelManager(config)
        assert hasattr(mm, 'config')
        assert hasattr(mm, 'models')

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

    def test_async_listen_for_commands(self):
        config = Config()
        mm = ModelManager(config)
        # Should not raise, but returns None or str
        import asyncio

        result = asyncio.run(mm.async_listen_for_commands())
        assert result is None or isinstance(result, str)
