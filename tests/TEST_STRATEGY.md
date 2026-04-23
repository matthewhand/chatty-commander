# ChattyCommander Test Strategy

## Test Pyramid Architecture

```
        /\
       /  \      E2E Tests (10%)
      /    \     Browser automation, full workflows
     /------\
    /        \   Integration Tests (20%)
   /          \  API contracts, service boundaries
  /------------\
 /              \ Unit Tests (70%)
/                \ Business logic, edge cases, mocks
------------------
```

## Test Level Definitions

### 1. Unit Tests (70% of test suite)
**Purpose:** Test business logic in isolation
**Location:** `tests/unit/` and `tests/test_*.py`
**Characteristics:**
- Fast (< 10ms per test)
- No I/O, network, or external dependencies
- Heavy use of mocks and fixtures
- Test one concept per test

**Patterns:**
```python
class TestCommandExecutor:
    """Unit tests for CommandExecutor with mocked dependencies."""
    
    def test_execute_valid_command(self, mock_config, mock_executor):
        # Arrange
        mock_config.commands = {"test": {"action": "echo"}}
        
        # Act
        result = mock_executor.execute("test")
        
        # Assert
        assert result is True
```

### 2. Integration Tests (20% of test suite)
**Purpose:** Test component interactions and API contracts
**Location:** `tests/integration/`, FastAPI TestClient tests
**Characteristics:**
- Test real service boundaries
- Use TestClient for HTTP APIs
- Use temporary databases/files
- May use real (lightweight) dependencies

**Patterns:**
```python
def test_api_creates_agent(client, temp_db):
    # Arrange
    agent_data = {"name": "Test Agent"}
    
    # Act
    response = client.post("/agents", json=agent_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "Test Agent"
```

### 3. Smoke Tests (5% of test suite)
**Purpose:** Verify critical paths work in production-like environment
**Location:** `tests/smoke/`
**Characteristics:**
- Minimal but critical coverage
- Fast to run ( CI/CD gate)
- Test happy paths only
- May run against staging

### 4. E2E Tests (5% of test suite)
**Purpose:** Test complete user workflows
**Location:** `tests/e2e/`
**Characteristics:**
- Browser automation (Playwright)
- Full stack testing
- Slow but comprehensive
- Test critical user journeys

## DRY Principles for Tests

### 1. Shared Fixtures (conftest.py hierarchy)

```
tests/
├── conftest.py              # Root fixtures (applies to all)
├── unit/
│   └── conftest.py          # Unit-specific fixtures
├── integration/
│   └── conftest.py          # Integration fixtures (DB, API client)
└── e2e/
    └── conftest.py          # E2E fixtures (browser, live server)
```

**Fixture Scopes:**
- `session`: Database connections, heavy resources
- `module`: Module-level setup
- `function`: Default, fresh for each test
- `class`: Shared across class methods

### 2. Test Data Factories

Centralized in `conftest.py` or `tests/factories.py`:

```python
class TestDataFactory:
    """Creates consistent test data objects."""
    
    @staticmethod
    def create_agent(name="Test Agent", capabilities=None):
        return {
            "name": name,
            "capabilities": capabilities or ["speak", "listen"],
            "status": "active"
        }
    
    @staticmethod
    def create_config(wake_words=None, actions=None):
        return Config(
            wake_words=wake_words or ["hey test"],
            model_actions=actions or {}
        )
```

### 3. Mock Factories

```python
class MockFactory:
    """Creates pre-configured mocks for common dependencies."""
    
    @staticmethod
    def create_mock_llm_manager(response="test response"):
        manager = Mock(spec=LLMManager)
        manager.generate.return_value = response
        manager.is_available.return_value = True
        return manager
    
    @staticmethod
    def create_mock_voice_pipeline():
        pipeline = Mock(spec=VoicePipeline)
        pipeline.process_audio.return_value = "transcribed text"
        pipeline.is_listening = False
        return pipeline
```

### 4. Assertion Helpers

```python
class TestAssertions:
    """Custom assertion helpers for common patterns."""
    
    @staticmethod
    def assert_valid_json_response(response, expected_keys=None):
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        if expected_keys:
            for key in expected_keys:
                assert key in data, f"Missing key: {key}"
        return data
    
    @staticmethod
    def assert_command_executed(executor, command_name):
        executor.execute_command.assert_called_once_with(command_name)
    
    @staticmethod
    def assert_state_transition(state_manager, from_state, to_state):
        calls = state_manager.change_state.call_args_list
        assert any(str(call) == to_state for call in calls)
```

### 5. Parameterized Test Patterns

```python
# Shared test data for parameterized tests
COMMAND_TEST_CASES = [
    ("open_browser", {"type": "url", "url": "https://google.com"}, True),
    ("play_music", {"type": "shell", "command": "player play"}, True),
    ("invalid", None, False),
]

@pytest.mark.parametrize("command,config,expected", COMMAND_TEST_CASES)
def test_command_execution(command, config, expected, executor):
    if config:
        executor.config.commands[command] = config
    result = executor.execute(command)
    assert result is expected
```

## Highest Quality End State

### Vision: "Tests as Living Documentation"

#### 1. Test Organization
```
tests/
├── unit/                      # Pure unit tests
│   ├── test_command_logic.py
│   ├── test_state_transitions.py
│   └── test_config_validation.py
├── integration/               # Service integration
│   ├── test_llm_backends.py
│   ├── test_voice_pipeline.py
│   └── test_web_api.py
├── e2e/                       # End-to-end
│   ├── test_voice_workflow.py
│   └── test_web_workflow.py
├── smoke/                     # Critical path
│   └── test_system_health.py
├── fixtures/                  # Shared test data
│   ├── agents.py
│   ├── commands.py
│   └── configs.py
├── helpers/                   # Test utilities
│   ├── assertions.py
│   ├── mocks.py
│   └── factories.py
└── conftest.py               # Root fixtures
```

#### 2. Test Quality Standards

**Every test must have:**
1. Clear docstring explaining what's being tested
2. AAA structure (Arrange, Act, Assert)
3. Single responsibility (one concept per test)
4. Meaningful assertions (not just `assert True`)
5. Fast execution (< 100ms for unit tests)

**Example:**
```python
def test_command_executor_validates_before_execution():
    """
    Test that CommandExecutor validates command existence
    before attempting execution to prevent errors.
    
    This is important because invalid commands should fail
    gracefully without side effects.
    """
    # Arrange
    executor = CommandExecutor(config=Mock())
    executor.config.commands = {"valid": {"action": "test"}}
    
    # Act
    result = executor.execute("invalid_command")
    
    # Assert
    assert result is False
    executor._execute_action.assert_not_called()
```

#### 3. Test Maintenance Strategy

**Automated Quality Gates:**
```yaml
# .github/workflows/test.yml
- name: Unit Tests
  run: pytest tests/unit/ --cov=src --cov-report=xml
  
- name: Integration Tests
  run: pytest tests/integration/ --db-url=postgresql://test
  
- name: Smoke Tests
  run: pytest tests/smoke/ -x  # Stop on first failure
  
- name: E2E Tests
  run: pytest tests/e2e/ --headed=false
  if: github.event_name == 'schedule'  # Nightly only
```

**Coverage Targets:**
- Unit tests: 80% line coverage minimum
- Integration tests: Cover all API endpoints
- E2E tests: Cover all critical user journeys

### 4. Reusable Test Components

#### Context Managers for Complex Setup
```python
@contextmanager
def temporary_voice_pipeline(config=None):
    """Provides a voice pipeline that cleans up after test."""
    pipeline = VoicePipeline(config or Mock())
    pipeline.start()
    try:
        yield pipeline
    finally:
        pipeline.stop()
        pipeline.cleanup()

# Usage
def test_voice_recognition():
    with temporary_voice_pipeline() as pipeline:
        result = pipeline.listen_for_command()
        assert result is not None
```

#### Decorators for Common Patterns
```python
def with_mock_llm(response="test"):
    """Decorator to inject mock LLM manager."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with patch('chatty_commander.llm.manager.LLMManager') as mock:
                instance = mock.return_value
                instance.generate.return_value = response
                kwargs['llm_manager'] = instance
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@with_mock_llm(response='{"action": "play_music"}')
def test_llm_command_parsing(llm_manager):
    processor = CommandProcessor(llm_manager=llm_manager)
    result = processor.parse("play some music")
    assert result.action == "play_music"
```

### 5. Test Naming Convention

```python
# Pattern: test_[unit]_[condition]_[expected_result]

def test_command_executor_with_valid_command_returns_true():
    pass

def test_command_executor_with_invalid_command_returns_false():
    pass

def test_state_manager_given_idle_state_when_computer_detected_transitions_to_computer():
    pass

def test_voice_pipeline_given_no_audio_when_listening_returns_none():
    pass
```

### 6. Performance Test Strategy

```python
# tests/perf/test_performance.py

@pytest.mark.slow
@pytest.mark.timeout(30)
def test_voice_pipeline_processes_audio_in_realtime():
    """Ensure voice pipeline keeps up with audio stream."""
    pipeline = VoicePipeline()
    audio_chunk = generate_test_audio(duration_ms=100)
    
    start = time.perf_counter()
    result = pipeline.process_chunk(audio_chunk)
    elapsed = time.perf_counter() - start
    
    assert elapsed < 0.1  # Must process faster than real-time
    assert result is not None
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `tests/fixtures/` module
- [ ] Create `tests/helpers/` module  
- [ ] Refactor `conftest.py` to use imports from fixtures/
- [ ] Document all existing fixtures

### Phase 2: DRY Refactoring (Week 2)
- [ ] Extract repeated mock setups to MockFactory
- [ ] Create TestDataFactory for common data patterns
- [ ] Refactor similar test classes to use shared base classes
- [ ] Create parameterized test datasets

### Phase 3: Architecture Alignment (Week 3)
- [ ] Move tests to unit/integration/e2e structure
- [ ] Ensure each test has proper docstring
- [ ] Add missing AAA comments
- [ ] Create smoke test suite

### Phase 4: Quality Gates (Week 4)
- [ ] Add test coverage thresholds to CI
- [ ] Add test timing checks (fail if > 5s per test)
- [ ] Create test reliability scorecard
- [ ] Document test maintenance guidelines

## Test Review Checklist

Before merging any test:
- [ ] Test has clear, descriptive docstring
- [ ] Test follows AAA structure
- [ ] Test uses appropriate fixtures (not manual setup)
- [ ] Test assertions are meaningful
- [ ] Test runs in < 1 second (unit) or < 10 seconds (integration)
- [ ] Test cleans up after itself
- [ ] Test doesn't duplicate existing test logic
- [ ] Test uses shared helpers where applicable
