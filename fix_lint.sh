sed -i 's/raise HTTPException(status_code=500, detail="Failed to update audio device configuration")/raise HTTPException(status_code=500, detail="Failed to update audio device configuration") from e/g' src/chatty_commander/web/routes/audio.py
sed -i '/except Exception as exc:/,/return {}/d' src/chatty_commander/web/routes/core.py
sed -i '/@router.get("\/api\/v1\/commands")/{N;N;N;N;d;}' src/chatty_commander/web/routes/core.py
sed -i 's/except ValueError:/except ValueError as err:/g' src/chatty_commander/web/routes/models.py
sed -i 's/detail="Invalid filename: path escapes target directory"/detail="Invalid filename: path escapes target directory"\n            ) from err/g' src/chatty_commander/web/routes/models.py
sed -i 's/from chatty_commander.web.routes.agents import _extract_json_from_response/from chatty_commander.web.routes.agents import _extract_json_from_response  # noqa: E402/g' tests/test_agents_helpers.py
sed -i 's/import unittest.mock/import unittest.mock  # noqa: E402/g' tests/test_avatar_api_list_success.py
sed -i 's/import os/import os  # noqa: E402/g' tests/test_cli_help_examples.py
sed -i 's/lines = \[l for l in output.splitlines() if l.strip()\]/lines = [line for line in output.splitlines() if line.strip()]/g' tests/test_structured_logging.py
