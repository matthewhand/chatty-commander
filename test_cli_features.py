#!/usr/bin/env python3
"""
test_cli_features.py

Validation script for CLI enhancements including interactive shell,
tab completion, argument validation, and configuration wizard.
"""

import subprocess
import sys
import os
import time
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CLIValidator:
    """Validates CLI functionality and enhancements."""
    
    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.test_results: List[Tuple[str, bool, str]] = []
        
    def run_command(self, command: List[str], description: str, input_text: Optional[str] = None, timeout: int = 10) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            logger.info(f"🔄 Testing: {description}")
            logger.debug(f"Command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                cwd=self.project_root,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            if success:
                logger.info(f"✅ {description} - PASSED")
            else:
                logger.error(f"❌ {description} - FAILED (exit code: {result.returncode})")
                if output:
                    logger.debug(f"Output: {output[-300:]}...")  # Last 300 chars
            
            return success, output
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {description} - TIMEOUT")
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"❌ {description} - ERROR: {e}")
            return False, str(e)
    
    def test_help_command(self) -> bool:
        """Test the enhanced --help command."""
        command = ["uv", "run", "python", "main.py", "--help"]
        success, output = self.run_command(command, "Enhanced --help command")
        
        if success:
            # Check for key help content
            required_sections = [
                "usage:",
                "--web",
                "--gui", 
                "--config",
                "--shell",
                "--no-auth",
                "--port",
                "--log-level"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section.lower() not in output.lower():
                    missing_sections.append(section)
            
            if missing_sections:
                logger.warning(f"⚠️  Help missing sections: {missing_sections}")
                success = False
            else:
                logger.info("✅ Help command contains all expected sections")
        
        self.test_results.append(("Help Command", success, output))
        return success
    
    def test_argument_validation(self) -> bool:
        """Test argument validation with invalid inputs."""
        test_cases = [
            (["uv", "run", "python", "main.py", "--port", "invalid"], "Invalid port validation"),
            (["uv", "run", "python", "main.py", "--log-level", "INVALID"], "Invalid log level validation"),
            (["uv", "run", "python", "main.py", "--web", "--gui"], "Conflicting mode validation"),
        ]
        
        all_passed = True
        for command, description in test_cases:
            success, output = self.run_command(command, description, timeout=5)
            
            # For validation tests, we expect failure (non-zero exit code)
            validation_passed = not success and ("error" in output.lower() or "invalid" in output.lower())
            
            if validation_passed:
                logger.info(f"✅ {description} - Properly rejected invalid input")
            else:
                logger.error(f"❌ {description} - Failed to validate input")
                all_passed = False
            
            self.test_results.append((f"Validation: {description}", validation_passed, output))
        
        return all_passed
    
    def test_interactive_shell_basic(self) -> bool:
        """Test basic interactive shell functionality."""
        # Test shell mode startup
        command = ["uv", "run", "python", "main.py", "--shell"]
        
        # Provide some basic commands to test
        test_input = "help\nstatus\nquit\n"
        
        success, output = self.run_command(command, "Interactive shell basic test", input_text=test_input, timeout=15)
        
        if success:
            # Check for shell indicators
            shell_indicators = [
                "chatty>",  # Shell prompt
                "interactive",
                "shell",
                "help"
            ]
            
            found_indicators = []
            for indicator in shell_indicators:
                if indicator.lower() in output.lower():
                    found_indicators.append(indicator)
            
            if found_indicators:
                logger.info(f"✅ Shell mode active with indicators: {found_indicators}")
            else:
                logger.warning("⚠️  Shell mode may not be working properly")
                success = False
        
        self.test_results.append(("Interactive Shell Basic", success, output))
        return success
    
    def test_config_wizard_dry_run(self) -> bool:
        """Test configuration wizard (dry run)."""
        # Create a temporary config file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_config:
            temp_config.write('{"test": true}')
            temp_config_path = temp_config.name
        
        try:
            # Test config wizard startup (should exit quickly with our input)
            command = ["uv", "run", "python", "main.py", "--config"]
            
            # Provide input to exit wizard quickly
            test_input = "\n" * 10 + "q\n"  # Multiple enters then quit
            
            success, output = self.run_command(command, "Configuration wizard test", input_text=test_input, timeout=10)
            
            # For config wizard, we expect it to start and show prompts
            wizard_indicators = [
                "configuration",
                "wizard",
                "setup",
                "path",
                "model"
            ]
            
            found_indicators = []
            for indicator in wizard_indicators:
                if indicator.lower() in output.lower():
                    found_indicators.append(indicator)
            
            if found_indicators:
                logger.info(f"✅ Config wizard started with indicators: {found_indicators}")
                success = True
            else:
                logger.warning("⚠️  Config wizard may not be working")
            
            self.test_results.append(("Configuration Wizard", success, output))
            return success
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_config_path)
            except:
                pass
    
    def test_mode_flags(self) -> bool:
        """Test different mode flags for basic functionality."""
        test_cases = [
            (["uv", "run", "python", "main.py", "--web", "--help"], "Web mode help"),
            (["uv", "run", "python", "main.py", "--gui", "--help"], "GUI mode help"),
        ]
        
        all_passed = True
        for command, description in test_cases:
            success, output = self.run_command(command, description, timeout=5)
            
            if success and "usage:" in output.lower():
                logger.info(f"✅ {description} - Mode flag recognized")
            else:
                logger.error(f"❌ {description} - Mode flag issue")
                all_passed = False
            
            self.test_results.append((f"Mode Flag: {description}", success, output))
        
        return all_passed
    
    def test_display_environment_handling(self) -> bool:
        """Test DISPLAY environment variable handling."""
        # Test GUI mode without DISPLAY (should fail gracefully)
        env = os.environ.copy()
        if 'DISPLAY' in env:
            del env['DISPLAY']
        
        try:
            result = subprocess.run(
                ["uv", "run", "python", "main.py", "--gui"],
                cwd=self.project_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Should fail gracefully with appropriate error message
            success = result.returncode != 0 and "display" in result.stderr.lower()
            
            if success:
                logger.info("✅ GUI mode properly handles missing DISPLAY")
            else:
                logger.error("❌ GUI mode doesn't handle missing DISPLAY properly")
            
            self.test_results.append(("DISPLAY Environment Handling", success, result.stderr))
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("❌ DISPLAY test timed out")
            self.test_results.append(("DISPLAY Environment Handling", False, "Timeout"))
            return False
        except Exception as e:
            logger.error(f"❌ DISPLAY test error: {e}")
            self.test_results.append(("DISPLAY Environment Handling", False, str(e)))
            return False
    
    def print_summary(self) -> bool:
        """Print test summary and return overall success."""
        logger.info("\n" + "="*50)
        logger.info("📊 CLI FEATURES TEST SUMMARY")
        logger.info("="*50)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, success, _ in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"   {test_name:<30} {status}")
            if success:
                passed += 1
        
        logger.info(f"\n🎯 Overall: {passed}/{total} CLI tests passed")
        
        if passed == total:
            logger.info("🎉 All CLI features working correctly!")
            return True
        else:
            logger.warning(f"⚠️  {total - passed} CLI test(s) failed.")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all CLI validation tests."""
        logger.info("🚀 Starting CLI Features Validation")
        logger.info(f"Project root: {self.project_root}")
        
        # Run all test categories
        self.test_help_command()
        self.test_argument_validation()
        self.test_interactive_shell_basic()
        self.test_config_wizard_dry_run()
        self.test_mode_flags()
        self.test_display_environment_handling()
        
        return self.print_summary()


def main():
    """Main execution function."""
    validator = CLIValidator()
    success = validator.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)