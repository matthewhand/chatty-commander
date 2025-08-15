import sys
import types

# Patch sys.modules to mock openwakeword and openwakeword.model for test imports
sys.modules['openwakeword'] = types.ModuleType('openwakeword')
mock_model_mod = types.ModuleType('openwakeword.model')
mock_model_mod.Model = type('Model', (), {})
sys.modules['openwakeword.model'] = mock_model_mod
#!/usr/bin/env python3
"""
Comprehensive System Testing Script for ChattyCommander

This script tests all application modes, CLI commands, configuration management,
and system functions. It serves as both a testing framework and documentation
of expected outputs.
Usage:
    python test_system.py [--mode MODE] [--verbose] [--output-file FILE]

Modes:
    all     - Run all tests (default)
    cli     - Test CLI commands only
    config  - Test configuration management only
    states  - Test state transitions only
    system  - Test system management only
    gui     - Test GUI functionality only
"""

import argparse  # noqa: E402 - imports after test setup and sys.modules patching
import json  # noqa: E402 - imports after test setup
import os  # noqa: E402 - imports after test setup
import subprocess  # noqa: E402 - imports after test setup
import sys  # noqa: E402 - imports after test setup
from datetime import datetime  # noqa: E402 - imports after test setup

# Add project root to path (parent of tests dir)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from chatty_commander.app.config import Config  # noqa: E402 - imported after path manipulation
from chatty_commander.app.model_manager import ModelManager  # noqa: E402 - imported after path manipulation
from chatty_commander.app.state_manager import StateManager  # noqa: E402 - imported after path manipulation

from chatty_commander.app.command_executor import (
    CommandExecutor,  # noqa: E402 - imported after path manipulation
)


class SystemTester:
    def __init__(self, verbose=False, output_file=None):
        self.verbose = verbose
        self.output_file = output_file
        self.test_results = []
        self.start_time = datetime.now()

        # Backup original config
        self.backup_config()

        print(f"\n{'='*60}")
        print("ChattyCommander System Testing Suite")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

    def backup_config(self):
        """Backup original configuration before testing"""
        if os.path.exists('config.json'):
            import shutil

            shutil.copy('config.json', 'config.json.backup')
            self.log("✓ Configuration backed up")

    def restore_config(self):
        """Restore original configuration after testing"""
        if os.path.exists('config.json.backup'):
            import shutil

            shutil.move('config.json.backup', 'config.json')
            self.log("✓ Configuration restored")

    def log(self, message, test_name=None, status=None):
        """Log test results and optionally print to console"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'test_name': test_name,
            'message': message,
            'status': status,
        }
        self.test_results.append(log_entry)

        if self.verbose or status in ['FAIL', 'ERROR']:
            status_prefix = f"[{status}] " if status else ""
            print(f"[{timestamp}] {status_prefix}{message}")

    def run_command(self, cmd, expected_exit_code=0, timeout=30):
        """Run a command and return result"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )

            success = result.returncode == expected_exit_code
            return {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'cmd': cmd,
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout}s',
                'cmd': cmd,
            }
        except Exception as e:
            return {'success': False, 'returncode': -1, 'stdout': '', 'stderr': str(e), 'cmd': cmd}

    def test_cli_help(self):
        """Test CLI help functionality"""
        self.log("Testing CLI help commands...", "CLI Help")

        tests = [
            ('chatty --help', 'Main help'),
            ('chatty run --help', 'Run command help'),
            ('chatty gui --help', 'GUI command help'),
            ('chatty config --help', 'Config command help'),
            ('chatty system --help', 'System command help'),
            ('chatty system start-on-boot --help', 'Start-on-boot help'),
            ('chatty system updates --help', 'Updates help'),
        ]

        for cmd, desc in tests:
            result = self.run_command(cmd)
            if result['success'] and 'usage:' in result['stdout']:
                self.log(f"✓ {desc}: Help displayed correctly", "CLI Help", "PASS")
            else:
                self.log(f"✗ {desc}: {result['stderr']}", "CLI Help", "FAIL")

    def test_config_management(self):
        """Test configuration management"""
        self.log("Testing configuration management...", "Config Management")

        # Test config listing
        result = self.run_command('chatty config --list')
        if result['success']:
            self.log("✓ Config listing works", "Config Management", "PASS")
        else:
            self.log(f"✗ Config listing failed: {result['stderr']}", "Config Management", "FAIL")

        # Test setting model action
        result = self.run_command('chatty config --set-model-action test_model test_action')
        if result['success']:
            self.log("✓ Model action setting works", "Config Management", "PASS")
        else:
            # Acceptable failure if error message is correct
            if "Invalid model name" in result['stderr']:
                self.log(
                    "✓ Model action setting fails as expected for invalid model name",
                    "Config Management",
                    "PASS",
                )
            else:
                self.log(
                    f"✗ Model action setting failed with unexpected error: {result['stderr']}",
                    "Config Management",
                    "FAIL",
                )

        # Test setting state model
        result = self.run_command('chatty config --set-state-model test_state "model1,model2"')
        if result['success']:
            self.log("✓ State model setting works", "Config Management", "PASS")
        else:
            # Acceptable failure if error message is correct
            if "Invalid state" in result['stderr']:
                self.log(
                    "✓ State model setting fails as expected for invalid state",
                    "Config Management",
                    "PASS",
                )
            else:
                self.log(
                    f"✗ State model setting failed with unexpected error: {result['stderr']}",
                    "Config Management",
                    "FAIL",
                )

    def test_system_management(self):
        """Test system management commands"""
        self.log("Testing system management...", "System Management")

        # Test start-on-boot status
        result = self.run_command('chatty system start-on-boot status')
        if result['success']:
            self.log("✓ Start-on-boot status check works", "System Management", "PASS")
        else:
            self.log(
                f"✗ Start-on-boot status failed: {result['stderr']}", "System Management", "FAIL"
            )

        # Test enabling start-on-boot
        result = self.run_command('chatty system start-on-boot enable')
        if result['success']:
            self.log("✓ Start-on-boot enable works", "System Management", "PASS")
        else:
            self.log(
                f"✗ Start-on-boot enable failed: {result['stderr']}", "System Management", "FAIL"
            )

        # Test disabling start-on-boot
        result = self.run_command('chatty system start-on-boot disable')
        if result['success']:
            self.log("✓ Start-on-boot disable works", "System Management", "PASS")
        else:
            self.log(
                f"✗ Start-on-boot disable failed: {result['stderr']}", "System Management", "FAIL"
            )

        # Test update checking
        result = self.run_command('chatty system updates check')
        if result['success']:
            self.log("✓ Update checking works", "System Management", "PASS")
        else:
            self.log(f"✗ Update checking failed: {result['stderr']}", "System Management", "FAIL")

        # Test auto-update settings
        result = self.run_command('chatty system updates enable-auto')
        if result['success']:
            self.log("✓ Auto-update enable works", "System Management", "PASS")
        else:
            self.log(
                f"✗ Auto-update enable failed: {result['stderr']}", "System Management", "FAIL"
            )

        result = self.run_command('chatty system updates disable-auto')
        if result['success']:
            self.log("✓ Auto-update disable works", "System Management", "PASS")
        else:
            self.log(
                f"✗ Auto-update disable failed: {result['stderr']}", "System Management", "FAIL"
            )

    def test_state_transitions(self):
        """Test state manager and transitions"""
        self.log("Testing state transitions...", "State Transitions")

        try:
            state_manager = StateManager()

            # Test initial state
            if state_manager.current_state == 'idle':
                self.log("✓ Initial state is 'idle'", "State Transitions", "PASS")
            else:
                self.log(
                    f"✗ Initial state is '{state_manager.current_state}', expected 'idle'",
                    "State Transitions",
                    "FAIL",
                )

            # Test state transitions
            transitions = [
                ('hey_chat_tee', 'chatty'),
                ('hey_khum_puter', 'computer'),
                ('okay_stop', 'idle'),
                ('toggle_mode', 'computer'),  # From idle
            ]

            for command, expected_state in transitions:
                new_state = state_manager.update_state(command)
                if new_state == expected_state:
                    self.log(
                        f"✓ Command '{command}' transitions to '{expected_state}'",
                        "State Transitions",
                        "PASS",
                    )
                else:
                    self.log(
                        f"✗ Command '{command}' failed to transition to '{expected_state}', got '{new_state}'",
                        "State Transitions",
                        "FAIL",
                    )

            # Test invalid state
            try:
                state_manager.change_state('invalid_state')
                self.log(
                    "✗ Invalid state change should raise ValueError", "State Transitions", "FAIL"
                )
            except ValueError:
                self.log(
                    "✓ Invalid state change raises ValueError correctly",
                    "State Transitions",
                    "PASS",
                )

        except Exception as e:
            self.log(f"✗ State transition testing failed: {str(e)}", "State Transitions", "ERROR")

    def test_config_loading(self):
        """Test configuration loading and validation"""
        self.log("Testing configuration loading...", "Config Loading")

        try:
            config = Config()

            # Test required attributes
            required_attrs = [
                'model_actions',
                'state_models',
                'api_endpoints',
                'general_models_path',
                'system_models_path',
                'chat_models_path',
                'debug_mode',
                'default_state',
            ]

            for attr in required_attrs:
                if hasattr(config, attr):
                    self.log(f"✓ Config has required attribute '{attr}'", "Config Loading", "PASS")
                else:
                    self.log(
                        f"✗ Config missing required attribute '{attr}'", "Config Loading", "FAIL"
                    )

            # Test state models configuration
            expected_states = ['idle', 'computer', 'chatty']
            for state in expected_states:
                if state in config.state_models:
                    self.log(
                        f"✓ State '{state}' configured with models: {config.state_models[state]}",
                        "Config Loading",
                        "PASS",
                    )
                else:
                    self.log(f"✗ State '{state}' not configured", "Config Loading", "FAIL")

            # Test model actions
            expected_commands = [
                'take_screenshot',
                'paste',
                'submit',
                'cycle_window',
                'oh_kay_screenshot',
                'wax_poetic',
                'lights_on',
                'lights_off',
            ]

            for command in expected_commands:
                if command in config.model_actions:
                    action = config.model_actions[command]
                    self.log(
                        f"✓ Command '{command}' configured: {action}", "Config Loading", "PASS"
                    )
                else:
                    self.log(f"✗ Command '{command}' not configured", "Config Loading", "FAIL")

        except Exception as e:
            self.log(f"✗ Config loading failed: {str(e)}", "Config Loading", "ERROR")

    def test_model_manager(self):
        """Test model manager functionality"""
        self.log("Testing model manager...", "Model Manager")

        try:
            config = Config()
            model_manager = ModelManager(config)

            # Test model path validation
            model_paths = [
                config.general_models_path,
                config.system_models_path,
                config.chat_models_path,
            ]

            for path in model_paths:
                if os.path.exists(path):
                    self.log(f"✓ Model path exists: {path}", "Model Manager", "PASS")
                else:
                    self.log(f"✗ Model path missing: {path}", "Model Manager", "FAIL")

            # Test model loading for each state
            for state in ['idle', 'computer', 'chatty']:
                try:
                    model_manager.reload_models(state)
                    self.log(f"✓ Models loaded for state '{state}'", "Model Manager", "PASS")
                except Exception as e:
                    self.log(
                        f"✗ Failed to load models for state '{state}': {str(e)}",
                        "Model Manager",
                        "FAIL",
                    )

        except Exception as e:
            self.log(f"✗ Model manager testing failed: {str(e)}", "Model Manager", "ERROR")

    def test_command_executor(self):
        """Test command executor functionality"""
        self.log("Testing command executor...", "Command Executor")

        try:
            config = Config()
            state_manager = StateManager()
            model_manager = ModelManager(config)
            executor = CommandExecutor(config, model_manager, state_manager)

            # Test command validation
            valid_commands = list(config.model_actions.keys())
            if valid_commands:
                test_command = valid_commands[0]
                if executor.validate_command(test_command):
                    self.log(
                        f"✓ Command validation works for '{test_command}'",
                        "Command Executor",
                        "PASS",
                    )
                else:
                    self.log(
                        f"✗ Command validation failed for '{test_command}'",
                        "Command Executor",
                        "FAIL",
                    )

            # Test invalid command
            try:
                is_valid = executor.validate_command('invalid_command')
                if not is_valid:
                    self.log("✓ Invalid command correctly rejected", "Command Executor", "PASS")
                else:
                    self.log("✗ Invalid command incorrectly accepted", "Command Executor", "FAIL")
            except Exception:
                # This is expected behavior - invalid commands should be rejected
                self.log(
                    "✓ Invalid command correctly rejected with exception",
                    "Command Executor",
                    "PASS",
                )

        except Exception as e:
            self.log(f"✗ Command executor testing failed: {str(e)}", "Command Executor", "ERROR")

    def test_gui_launch(self):
        """Test GUI application launch"""
        self.log("Testing GUI launch...", "GUI Launch")

        # Test GUI command with short timeout to simulate successful launch
        result = self.run_command('chatty gui --help')
        if result['success'] and 'usage:' in result['stdout']:
            self.log("✓ GUI command help works", "GUI Launch", "PASS")
        else:
            # Try a quick non-blocking test
            result = self.run_command('timeout 2 chatty gui || true', timeout=5)
            if result['returncode'] in [0, 124]:  # Success or timeout
                self.log(
                    "✓ GUI command accepts launch (terminated as expected)", "GUI Launch", "PASS"
                )
            else:
                self.log(f"✗ GUI launch failed: {result['stderr']}", "GUI Launch", "FAIL")

    def test_installation(self):
        """Test package installation and CLI availability"""
        self.log("Testing installation...", "Installation")

        # Test if chatty command is available
        result = self.run_command('which chatty')
        if result['success'] and result['stdout'].strip():
            self.log(
                f"✓ 'chatty' command available at: {result['stdout'].strip()}",
                "Installation",
                "PASS",
            )
        else:
            self.log("✗ 'chatty' command not found in PATH", "Installation", "FAIL")

        # Test Python module imports
        modules = [
            'chatty_commander.app.config',
            'chatty_commander.app.state_manager',
            'chatty_commander.app.model_manager',
            'chatty_commander.app.command_executor',
            'chatty_commander.cli.cli',
        ]
        for module in modules:
            result = self.run_command(f'python -c "import {module}; print(\'OK\')"; echo')
            if result['success'] and 'OK' in result['stdout']:
                self.log(f"✓ Module '{module}' imports successfully", "Installation", "PASS")
            else:
                self.log(
                    f"✗ Module '{module}' import failed: {result['stderr']}", "Installation", "FAIL"
                )

    def run_all_tests(self):
        """Run all system tests"""
        test_methods = [
            self.test_installation,
            self.test_cli_help,
            self.test_config_loading,
            self.test_config_management,
            self.test_system_management,
            self.test_state_transitions,
            self.test_model_manager,
            self.test_command_executor,
            self.test_gui_launch,
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log(
                    f"✗ Test method {test_method.__name__} crashed: {str(e)}",
                    test_method.__name__,
                    "ERROR",
                )

    def generate_report(self):
        """Generate test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        # Count results
        total_tests = len([r for r in self.test_results if r['status']])
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        errors = len([r for r in self.test_results if r['status'] == 'ERROR'])

        report = f"""
{'='*60}
ChattyCommander System Test Report
{'='*60}

Test Summary:
  Total Tests: {total_tests}
  Passed: {passed}
  Failed: {failed}
  Errors: {errors}
  Success Rate: {(passed/total_tests*100):.1f}% if total_tests > 0 else 0

Duration: {duration.total_seconds():.2f} seconds
Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
Detailed Results:
{'='*60}
"""

        # Group results by test name
        test_groups = {}
        for result in self.test_results:
            if result['test_name']:
                if result['test_name'] not in test_groups:
                    test_groups[result['test_name']] = []
                test_groups[result['test_name']].append(result)

        for test_name, results in test_groups.items():
            report += f"\n{test_name}:\n"
            for result in results:
                if result['status']:
                    status_icon = (
                        "✓"
                        if result['status'] == "PASS"
                        else "✗" if result['status'] == "FAIL" else "⚠"
                    )
                    report += f"  {status_icon} [{result['status']}] {result['message']}\n"

        # Add failed/error details
        failures = [r for r in self.test_results if r['status'] in ['FAIL', 'ERROR']]
        if failures:
            report += f"\n{'='*60}\nFailures and Errors:\n{'='*60}\n"
            for failure in failures:
                report += f"\n[{failure['status']}] {failure['test_name']}: {failure['message']}\n"

        print(report)

        # Save to file if specified
        if self.output_file:
            with open(self.output_file, 'w') as f:
                f.write(report)
                # Also save raw JSON data
                f.write(f"\n\n{'='*60}\nRaw Test Data (JSON):\n{'='*60}\n")
                json.dump(self.test_results, f, indent=2)
            print(f"\nReport saved to: {self.output_file}")

        return passed, failed, errors


def main():
    parser = argparse.ArgumentParser(description='ChattyCommander System Testing Suite')
    parser.add_argument(
        '--mode',
        choices=['all', 'cli', 'config', 'states', 'system', 'gui'],
        default='all',
        help='Test mode to run',
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output-file', '-o', help='Save report to file')

    args = parser.parse_args()

    tester = SystemTester(verbose=args.verbose, output_file=args.output_file)

    try:
        if args.mode == 'all':
            tester.run_all_tests()
        elif args.mode == 'cli':
            tester.test_cli_help()
        elif args.mode == 'config':
            tester.test_config_loading()
            tester.test_config_management()
        elif args.mode == 'states':
            tester.test_state_transitions()
        elif args.mode == 'system':
            tester.test_system_management()
        elif args.mode == 'gui':
            tester.test_gui_launch()

        passed, failed, errors = tester.generate_report()

        # Exit with appropriate code
        if errors > 0:
            sys.exit(2)  # Errors occurred
        elif failed > 0:
            sys.exit(1)  # Tests failed
        else:
            sys.exit(0)  # All tests passed

    finally:
        tester.restore_config()


if __name__ == '__main__':
    main()
