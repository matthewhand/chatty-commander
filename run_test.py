import pytest
import chatty_commander.web.routes.agents

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["tests/test_agents_api_create_from_description.py", "-v", "-s"]))
