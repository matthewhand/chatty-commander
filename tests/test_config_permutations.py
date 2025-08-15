from itertools import product

import pytest

from chatty_commander.app.config import Config


@pytest.fixture
def config():
    return Config()


def test_state_model_permutations(config):
    states = ['idle', 'computer', 'chatty']
    models = [['model1'], ['model1', 'model2'], []]  # Example permutations
    for state, model_list in product(states, models):
        config.state_models[state] = model_list
        config.validate()  # Check if validation passes or raises expected errors
        assert config.state_models[state] == model_list


# Add more tests for listen_for, modes, etc.
