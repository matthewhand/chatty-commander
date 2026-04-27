"""
Mock tests for GPU acceleration detection.

Tests GPU backend detection without requiring actual hardware.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys


class TestGPUAccelerationDetector:
    """Test GPU acceleration detection with mocks."""
    
    @pytest.fixture
    def detector(self):
        """Create detector with mocked environment."""
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            with patch('chatty_commander.vision.gpu_acceleration.cv2') as mock_cv2:
                from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector
                return GPUAccelerationDetector()
    
    def test_detector_initialization(self):
        """Test detector can be initialized."""
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector
            detector = GPUAccelerationDetector()
            assert detector is not None
    
    @patch('chatty_commander.vision.gpu_acceleration.subprocess.run')
    @patch('chatty_commander.vision.gpu_acceleration.cv2')
    def test_cuda_detection(self, mock_cv2, mock_subprocess):
        """Test CUDA detection when available."""
        # Mock CUDA availability
        mock_cv2.cuda.getCudaEnabledDeviceCount.return_value = 1
        mock_device = MagicMock()
        mock_device.totalMemory.return_value = 8 * 1024 * 1024 * 1024  # 8GB
        mock_device.freeMemory.return_value = 6 * 1024 * 1024 * 1024
        mock_device.majorVersion.return_value = 7
        mock_device.minorVersion.return_value = 5
        mock_cv2.cuda.DeviceInfo.return_value = mock_device
        mock_cv2.cuda.setDevice.return_value = None
        
        from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector, GPUBackend
        
        detector = GPUAccelerationDetector()
        
        assert detector.get_backend() == GPUBackend.CUDA
        assert detector.is_accelerated() is True
        assert 'total_memory' in detector.get_device_info()
    
    @patch('chatty_commander.vision.gpu_acceleration.subprocess.run')
    def test_rocm_detection(self, mock_subprocess):
        """Test ROCm detection via rocminfo."""
        # Mock rocminfo output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'AMD Device\nName: AMD Radeon RX 6800'
        mock_subprocess.return_value = mock_result
        
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            mock_cv2 = MagicMock()
            mock_cv2.ocl.haveOpenCL.return_value = True
            mock_cv2.ocl.useOpenCL.return_value = True
            mock_device = MagicMock()
            mock_device.vendor.return_value = 'AMD'
            mock_device.name.return_value = 'AMD Radeon'
            mock_cv2.ocl.Device_getDefault.return_value = mock_device
            
            with patch('chatty_commander.vision.gpu_acceleration.cv2', mock_cv2):
                from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector, GPUBackend
                
                detector = GPUAccelerationDetector()
                
                assert detector.get_backend() == GPUBackend.ROCM
    
    @patch('chatty_commander.vision.gpu_acceleration.subprocess.run')
    def test_opencl_detection(self, mock_subprocess):
        """Test generic OpenCL detection."""
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            mock_cv2 = MagicMock()
            mock_cv2.ocl.haveOpenCL.return_value = True
            mock_cv2.ocl.useOpenCL.return_value = True
            mock_device = MagicMock()
            mock_device.vendor.return_value = 'Intel'
            mock_device.name.return_value = 'Intel HD Graphics'
            mock_device.version.return_value = 'OpenCL 2.0'
            mock_cv2.ocl.Device_getDefault.return_value = mock_device
            
            with patch('chatty_commander.vision.gpu_acceleration.cv2', mock_cv2):
                from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector, GPUBackend
                
                detector = GPUAccelerationDetector()
                
                assert detector.get_backend() == GPUBackend.OPENCL
                assert 'vendor' in detector.get_device_info()
    
    @patch('chatty_commander.vision.gpu_acceleration.subprocess.run')
    def test_vulkan_detection(self, mock_subprocess):
        """Test Vulkan detection."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector, GPUBackend
            
            detector = GPUAccelerationDetector()
            
            # Should detect Vulkan or fallback to NONE
            assert detector.get_backend() in [GPUBackend.VULKAN, GPUBackend.NONE]
    
    def test_no_gpu_fallback(self):
        """Test fallback to CPU when no GPU available."""
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            mock_cv2 = MagicMock()
            mock_cv2.cuda.getCudaEnabledDeviceCount.return_value = 0
            mock_cv2.ocl.haveOpenCL.return_value = False
            
            with patch('chatty_commander.vision.gpu_acceleration.cv2', mock_cv2):
                from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector, GPUBackend
                
                detector = GPUAccelerationDetector()
                
                assert detector.get_backend() == GPUBackend.NONE
                assert detector.is_accelerated() is False
    
    def test_print_summary_no_errors(self):
        """Test that print_summary runs without errors."""
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            mock_cv2 = MagicMock()
            mock_cv2.cuda.getCudaEnabledDeviceCount.return_value = 0
            mock_cv2.ocl.haveOpenCL.return_value = False
            
            with patch('chatty_commander.vision.gpu_acceleration.cv2', mock_cv2):
                from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector
                
                detector = GPUAccelerationDetector()
                
                # Should not raise
                detector.print_summary()
    
    def test_get_device_info_structure(self):
        """Test device info structure."""
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            mock_cv2 = MagicMock()
            mock_cv2.cuda.getCudaEnabledDeviceCount.return_value = 1
            mock_device = MagicMock()
            mock_device.totalMemory.return_value = 8 * 1024 * 1024 * 1024
            mock_cv2.cuda.DeviceInfo.return_value = mock_device
            
            with patch('chatty_commander.vision.gpu_acceleration.cv2', mock_cv2):
                from chatty_commander.vision.gpu_acceleration import GPUAccelerationDetector
                
                detector = GPUAccelerationDetector()
                info = detector.get_device_info()
                
                assert isinstance(info, dict)


class TestAcceleratedBodyDetector:
    """Test accelerated body detector with mocks."""
    
    @pytest.fixture
    def detector(self):
        """Create detector with mocked GPU."""
        with patch.dict('sys.modules', {'cv2': MagicMock(), 'numpy': MagicMock()}):
            with patch('chatty_commander.vision.gpu_acceleration.GPUAccelerationDetector') as mock_gpu:
                mock_gpu_instance = MagicMock()
                mock_gpu_instance.get_backend.return_value = MagicMock()
                mock_gpu_instance.get_backend.return_value.value = 'cuda'
                mock_gpu_instance.is_accelerated.return_value = True
                mock_gpu.return_value = mock_gpu_instance
                
                from chatty_commander.vision.gpu_acceleration import AcceleratedBodyDetector
                return AcceleratedBodyDetector()
    
    def test_accelerated_detector_initialization(self):
        """Test accelerated detector initialization."""
        with patch.dict('sys.modules', {'cv2': MagicMock(), 'numpy': MagicMock()}):
            with patch('chatty_commander.vision.gpu_acceleration.GPUAccelerationDetector') as mock_gpu:
                mock_gpu_instance = MagicMock()
                mock_gpu_instance.get_backend.return_value = MagicMock()
                mock_gpu_instance.get_backend.return_value.value = 'cuda'
                mock_gpu_instance.is_accelerated.return_value = True
                mock_gpu.return_value = mock_gpu_instance
                
                from chatty_commander.vision.gpu_acceleration import AcceleratedBodyDetector
                detector = AcceleratedBodyDetector()
                
                assert detector is not None
                assert detector.is_gpu_available() is True
    
    def test_process_frame_gpu(self):
        """Test GPU frame processing."""
        import numpy as np
        
        with patch.dict('sys.modules', {'cv2': MagicMock(), 'numpy': np}):
            with patch('chatty_commander.vision.gpu_acceleration.GPUAccelerationDetector') as mock_gpu:
                mock_gpu_instance = MagicMock()
                mock_backend = MagicMock()
                mock_backend.value = 'cuda'
                mock_gpu_instance.get_backend.return_value = mock_backend
                mock_gpu_instance.is_accelerated.return_value = True
                mock_gpu.return_value = mock_gpu_instance
                
                mock_cv2 = MagicMock()
                mock_gpu_mat = MagicMock()
                mock_cv2.cuda_GpuMat.return_value = mock_gpu_mat
                mock_cv2.cuda.resize.return_value = mock_gpu_mat
                mock_cv2.cuda.cvtColor.return_value = mock_gpu_mat
                mock_gpu_mat.download.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
                
                with patch('chatty_commander.vision.gpu_acceleration.cv2', mock_cv2):
                    from chatty_commander.vision.gpu_acceleration import AcceleratedBodyDetector, GPUBackend
                    
                    detector = AcceleratedBodyDetector()
                    detector.backend = GPUBackend.CUDA
                    
                    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
                    result = detector.process_frame_gpu(frame)
                    
                    assert result is not None
    
    def test_process_frame_cpu_fallback(self):
        """Test CPU fallback when GPU unavailable."""
        import numpy as np
        
        with patch.dict('sys.modules', {'cv2': MagicMock(), 'numpy': np}):
            with patch('chatty_commander.vision.gpu_acceleration.GPUAccelerationDetector') as mock_gpu:
                mock_gpu_instance = MagicMock()
                mock_backend = MagicMock()
                mock_backend.value = 'none'
                mock_gpu_instance.get_backend.return_value = mock_backend
                mock_gpu_instance.is_accelerated.return_value = False
                mock_gpu.return_value = mock_gpu_instance
                
                from chatty_commander.vision.gpu_acceleration import AcceleratedBodyDetector
                
                detector = AcceleratedBodyDetector()
                detector.backend = MagicMock()
                detector.backend.value = 'none'
                
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                result = detector.process_frame_gpu(frame)
                
                # Should return frame unchanged when no GPU
                assert result is frame
    
    def test_get_performance_tips(self):
        """Test performance tips generation."""
        with patch.dict('sys.modules', {'cv2': MagicMock(), 'numpy': MagicMock()}):
            with patch('chatty_commander.vision.gpu_acceleration.GPUAccelerationDetector') as mock_gpu:
                mock_gpu_instance = MagicMock()
                mock_gpu_instance.get_backend.return_value = MagicMock()
                mock_gpu_instance.get_backend.return_value.value = 'none'
                mock_gpu_instance.is_accelerated.return_value = False
                mock_gpu.return_value = mock_gpu_instance
                
                from chatty_commander.vision.gpu_acceleration import AcceleratedBodyDetector
                
                detector = AcceleratedBodyDetector()
                tips = detector.get_performance_tips()
                
                assert isinstance(tips, list)
                assert len(tips) > 0


class TestGPUFunctions:
    """Test utility functions."""
    
    def test_check_acceleration_status(self):
        """Test acceleration status check."""
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            with patch('chatty_commander.vision.gpu_acceleration.GPUAccelerationDetector') as mock_detector:
                mock_instance = MagicMock()
                mock_instance.get_backend.return_value = MagicMock()
                mock_instance.get_backend.return_value.value = 'opencl'
                mock_instance.is_accelerated.return_value = True
                mock_instance.get_device_info.return_value = {'name': 'Intel GPU'}
                mock_detector.return_value = mock_instance
                
                from chatty_commander.vision.gpu_acceleration import check_acceleration_status
                
                status = check_acceleration_status()
                
                assert isinstance(status, dict)
                assert 'backend' in status
                assert 'available' in status
    
    def test_print_acceleration_report(self):
        """Test that report prints without errors."""
        with patch.dict('sys.modules', {'cv2': MagicMock()}):
            mock_cv2 = MagicMock()
            mock_cv2.getBuildInformation.return_value = 'OpenCV 4.5.0'
            mock_cv2.ocl.haveOpenCL.return_value = True
            mock_cv2.ocl.useOpenCL.return_value = False
            
            with patch('chatty_commander.vision.gpu_acceleration.cv2', mock_cv2):
                with patch('chatty_commander.vision.gpu_acceleration.GPUAccelerationDetector') as mock_detector:
                    mock_instance = MagicMock()
                    mock_instance.get_backend.return_value = MagicMock()
                    mock_instance.get_backend.return_value.value = 'cuda'
                    mock_instance.get_device_info.return_value = {'name': 'NVIDIA'}
                    mock_instance.print_summary = MagicMock()
                    mock_detector.return_value = mock_instance
                    
                    from chatty_commander.vision.gpu_acceleration import print_acceleration_report
                    
                    # Should not raise
                    print_acceleration_report()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
