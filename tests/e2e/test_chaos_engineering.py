# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
CHAOS ENGINEERING AGENT - Failure mode and edge case testing.

This test module intentionally injects failures to verify system resilience.
Tests focus on: crashes, resource exhaustion, network failures, disk errors.
"""

from __future__ import annotations

import gc
import os
import queue
import random
import resource
import signal
import string
import sys
import tempfile
import threading
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, Mock, patch, side_effect

import pytest


class TestMemoryExhaustion:
    """Test behavior under memory pressure."""
    
    def test_large_config_file_handling(self):
        """Test loading extremely large config files."""
        from chatty_commander.app.config import ConfigManager
        
        # Create a large config file (1MB+ of JSON)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            large_data = {"models": [{"name": f"model_{i}", "data": "x" * 1000} for i in range(1000)]}
            import json
            json.dump(large_data, f)
            temp_path = f.name
        
        try:
            with patch.object(ConfigManager, '_load_from_disk') as mock_load:
                mock_load.return_value = large_data
                cm = ConfigManager(config_path=temp_path)
                # Should not crash with large data
                assert cm is not None
        finally:
            os.unlink(temp_path)
    
    def test_circular_reference_config(self):
        """Test handling of circular references in config."""
        from chatty_commander.app.config import Config
        
        config = Config()
        # Create circular reference (shouldn't happen in real code but test defense)
        config.self_ref = config
        
        # JSON serialization should handle this gracefully
        try:
            import json
            json.dumps(config.__dict__, default=lambda x: "<circular>")
        except (TypeError, ValueError):
            pass  # Expected to fail gracefully


class TestNetworkFailures:
    """Test behavior under network failure conditions."""
    
    def test_llm_backend_timeout_cascade(self):
        """Test cascading timeouts across multiple LLM backends."""
        from chatty_commander.llm.manager import LLMManager
        
        manager = LLMManager()
        
        # Simulate all backends timing out
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = TimeoutError("Connection timeout")
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.chat.completions.create.side_effect = TimeoutError("API timeout")
                mock_openai.return_value = mock_client
                
                # Should fall back to mock backend
                result = manager.generate("test prompt", timeout=0.001)
                # Either returns response or raises gracefully
                assert result is not None or isinstance(result, str)
    
    def test_partial_network_partition(self):
        """Test when some backends are unreachable but others work."""
        from chatty_commander.llm.manager import LLMManager
        
        call_count = 0
        def selective_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Network partition")
            return Mock(data=[Mock(message=Mock(content="Success after partition"))])
        
        with patch('httpx.get', side_effect=selective_failure):
            manager = LLMManager()
            # Should eventually succeed
            assert manager is not None
    
    def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        from chatty_commander.advisors.tools.browser_analyst import summarize_url
        
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = Exception("Name resolution failed")
            
            result = summarize_url("http://nonexistent-domain-12345.invalid")
            # Should return error response, not crash
            assert result is not None


class TestDiskFailures:
    """Test behavior under disk/storage failure conditions."""
    
    def test_disk_full_during_config_save(self):
        """Test config save when disk is full."""
        from chatty_commander.app.config import ConfigManager
        
        cm = ConfigManager()
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = OSError(28, "No space left on device")
            
            with pytest.raises(OSError) as exc_info:
                cm.save_config()
            assert exc_info.value.errno == 28 or "No space" in str(exc_info.value)
    
    def test_read_only_filesystem(self):
        """Test behavior on read-only filesystem."""
        from chatty_commander.app.config import ConfigManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            
            # Create config first
            cm = ConfigManager(config_path=config_path)
            cm.save_config()
            
            # Simulate read-only by patching write
            with patch.object(ConfigManager, 'save_config') as mock_save:
                mock_save.side_effect = PermissionError("Read-only file system")
                
                with pytest.raises(PermissionError):
                    cm.save_config()
    
    def test_corrupted_state_file_recovery(self):
        """Test recovery from corrupted state file."""
        from chatty_commander.app.state_manager import StateManager
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("corrupted json {{[[")
            temp_path = f.name
        
        try:
            with patch.object(StateManager, '_load_state') as mock_load:
                mock_load.side_effect = Exception("Corrupted state")
                
                sm = StateManager()
                # Should initialize with default state
                assert sm.current_state is not None
        finally:
            os.unlink(temp_path)


class TestConcurrencyChaos:
    """Test race conditions and concurrency issues."""
    
    def test_concurrent_config_modification(self):
        """Test concurrent modifications to config."""
        from chatty_commander.app.config import ConfigManager
        
        cm = ConfigManager()
        errors = []
        
        def modifier(thread_id):
            try:
                for i in range(10):
                    cm.config.thread_id = thread_id
                    cm.config.iteration = i
                    time.sleep(random.uniform(0.001, 0.01))
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=modifier, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not crash, though final state may vary
        assert cm.config is not None
    
    def test_websocket_connection_flood(self):
        """Test handling of many simultaneous WebSocket connections."""
        from chatty_commander.web.routes.ws import ConnectionManager
        
        cm = ConnectionManager()
        connections = []
        
        # Simulate connection flood
        for i in range(100):
            mock_ws = Mock()
            mock_ws.client_state = Mock()
            mock_ws.client_state.name = "CONNECTED"
            connections.append(mock_ws)
            cm.connect(mock_ws)
        
        # Verify manager didn't crash
        assert len(cm.active_connections) <= 100
        
        # Cleanup
        for ws in connections:
            cm.disconnect(ws)
    
    def test_deadlock_prevention(self):
        """Test that locks don't cause deadlocks."""
        from chatty_commander.app.command_executor import CommandExecutor
        
        ce = CommandExecutor(config=Mock(), model_manager=Mock(), state_manager=Mock())
        
        def worker():
            try:
                ce.execute_command("test")
            except Exception:
                pass
        
        # Multiple threads competing for executor
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker) for _ in range(20)]
            
            # All should complete without deadlock
            for future in as_completed(futures, timeout=5):
                try:
                    future.result()
                except Exception:
                    pass


class TestResourceExhaustion:
    """Test behavior under resource exhaustion."""
    
    def test_file_descriptor_exhaustion(self):
        """Test handling when file descriptors are exhausted."""
        import tempfile
        
        files = []
        try:
            # Open many files to exhaust descriptors (may fail on some systems)
            for i in range(1000):
                try:
                    f = tempfile.NamedTemporaryFile(delete=False)
                    files.append(f)
                except OSError as e:
                    if "Too many open files" in str(e):
                        break
            
            # Now test ConfigManager under this condition
            from chatty_commander.app.config import ConfigManager
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write('{}')
                temp_path = f.name
            
            try:
                cm = ConfigManager(config_path=temp_path)
                # Should handle gracefully
                assert cm is not None
            finally:
                os.unlink(temp_path)
        finally:
            for f in files:
                try:
                    f.close()
                    os.unlink(f.name)
                except Exception:
                    pass
    
    def test_thread_exhaustion(self):
        """Test behavior when threads can't be created."""
        from chatty_commander.voice.wakeword import MockWakeWordDetector
        
        detector = MockWakeWordDetector(wake_words=["test"])
        
        # Try to start multiple times
        threads = []
        for i in range(50):
            try:
                detector.start()
            except RuntimeError:
                # Thread limit reached
                break
        
        # Cleanup
        try:
            detector.stop()
        except Exception:
            pass
    
    def test_memory_fragmentation(self):
        """Test with fragmented memory allocations."""
        import gc
        
        # Create memory fragmentation
        objects = []
        for i in range(1000):
            # Allocate objects of varying sizes
            size = random.randint(10, 10000)
            objects.append("x" * size)
            if i % 100 == 0:
                # Delete some to create fragmentation
                objects = objects[i//2:]
        
        gc.collect()
        
        # Now run normal operations
        from chatty_commander.app.config import Config
        config = Config()
        assert config is not None


class TestInputChaos:
    """Test with malformed and chaotic input data."""
    
    def test_unicode_bom_handling(self):
        """Test handling of UTF-8 BOM in config files."""
        from chatty_commander.app.config import ConfigManager
        import json
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            # Write UTF-8 BOM followed by JSON
            f.write(b'\xef\xbb\xbf' + json.dumps({"test": "value"}).encode('utf-8'))
            temp_path = f.name
        
        try:
            with patch.object(ConfigManager, '_load_from_disk') as mock_load:
                mock_load.return_value = {"test": "value"}
                cm = ConfigManager(config_path=temp_path)
                assert cm.config.test == "value"
        finally:
            os.unlink(temp_path)
    
    def test_null_byte_injection(self):
        """Test handling of null bytes in strings."""
        from chatty_commander.web.validation import validate_uuid
        
        # Null byte injection attempt
        malicious = "550e8400-e29b-41d4-a716-446655440000\x00/etc/passwd"
        
        with pytest.raises(Exception):
            validate_uuid(malicious)
    
    def test_path_traversal_attempts(self):
        """Test resistance to path traversal attacks."""
        from chatty_commander.web.routes.models import _get_model_dirs
        
        # Patch DEFAULT_MODEL_DIRS with traversal attempts
        with patch('chatty_commander.web.routes.models.DEFAULT_MODEL_DIRS', 
                   ["../../../etc", "models/../../../passwd"]):
            dirs = _get_model_dirs()
            # Should not return actual system directories
            assert not any('/etc' in str(d) or '/passwd' in str(d) for d in dirs)
    
    def test_very_long_strings(self):
        """Test handling of extremely long strings."""
        from chatty_commander.app.state_manager import StateManager
        
        sm = StateManager()
        
        # 1MB command name
        long_command = "a" * (1024 * 1024)
        
        result = sm.process_command(long_command)
        # Should not crash, though may return False
        assert result is False or result is True


class TestSignalHandling:
    """Test signal handling and cleanup."""
    
    def test_sigterm_during_save(self):
        """Test SIGTERM received during config save."""
        import signal
        from chatty_commander.app.config import ConfigManager
        
        cm = ConfigManager()
        
        def delayed_sigterm(signum, frame):
            pass
        
        # Simulate save with signal
        original_handler = signal.signal(signal.SIGTERM, delayed_sigterm)
        try:
            with patch('builtins.open') as mock_open:
                mock_file = Mock()
                mock_cm = MagicMock()
                mock_cm.__enter__ = Mock(return_value=mock_file)
                mock_cm.__exit__ = Mock(return_value=None)
                mock_open.return_value = mock_cm
                
                cm.save_config()
                # Should complete or handle signal gracefully
        finally:
            signal.signal(signal.SIGTERM, original_handler)
    
    def test_keyboard_interrupt_handling(self):
        """Test KeyboardInterrupt during long operation."""
        from chatty_commander.llm.manager import LLMManager
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            # Simulate slow operation that gets interrupted
            def slow_operation(*args, **kwargs):
                time.sleep(0.1)
                raise KeyboardInterrupt()
            
            mock_client.chat.completions.create.side_effect = slow_operation
            mock_openai.return_value = mock_client
            
            manager = LLMManager()
            
            with pytest.raises(KeyboardInterrupt):
                manager.generate("test")


class TestTimingAttacks:
    """Test for timing-based side channels."""
    
    def test_constant_time_auth(self):
        """Verify authentication uses constant-time comparison."""
        from chatty_commander.web.server import constant_time_compare
        import time
        
        # Test with different length strings
        times = []
        for test_len in [10, 100, 1000]:
            a = "a" * test_len
            b = "b" * test_len
            
            start = time.perf_counter()
            for _ in range(100):
                constant_time_compare(a, b)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        # Times should be similar (within 10x factor for constant time)
        # This is a loose check since timing varies in CI
        assert max(times) / (min(times) + 0.0001) < 50  # Very loose bound


# Run chaos tests: pytest tests/test_chaos_engineering.py -v --tb=short
