from unittest.mock import patch

import chatty_commander.main as main_module


def test_propagate_patches():
    # Setup some dummy values to simulate patches
    dummy_config = object()
    dummy_model_manager = object()

    # Store original values to restore them later
    original_config = getattr(main_module._cli, "Config", None)
    original_model_manager = getattr(main_module._cli, "ModelManager", None)

    try:
        # Patch the local module namespace
        main_module.Config = dummy_config
        main_module.ModelManager = dummy_model_manager

        # Run propagate
        main_module._propagate_patches()

        # Check if they were propagated to the CLI module
        assert main_module._cli.Config is dummy_config
        assert main_module._cli.ModelManager is dummy_model_manager
    finally:
        # Restore
        if original_config:
            main_module._cli.Config = original_config
            main_module.Config = original_config
        if original_model_manager:
            main_module._cli.ModelManager = original_model_manager
            main_module.ModelManager = original_model_manager


@patch("chatty_commander.cli.cli.cli_main")
def test_main(mock_cli_main):
    # Test that calling main delegates to cli_main
    mock_cli_main.return_value = 0
    result = main_module.main()
    assert result == 0
    mock_cli_main.assert_called_once()
