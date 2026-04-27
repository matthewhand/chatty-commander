"""
GPU Acceleration Support for OpenCV Body Detection.

Detects and configures ROCm (AMD), CUDA (NVIDIA), Vulkan, and OpenCL backends.
Falls back gracefully to CPU if GPU unavailable.
"""

import cv2
import numpy as np
import logging
import subprocess
from typing import Optional, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class GPUBackend(Enum):
    """Available GPU acceleration backends."""
    NONE = "none"
    CUDA = "cuda"           # NVIDIA
    ROCM = "rocm"           # AMD
    OPENCL = "opencl"       # Cross-platform
    VULKAN = "vulkan"       # Experimental


class GPUAccelerationDetector:
    """Detect available GPU acceleration options."""
    
    def __init__(self):
        self.backend = GPUBackend.NONE
        self.device_info: Dict[str, Any] = {}
        self._detect_gpu()
    
    def _detect_gpu(self) -> None:
        """Detect available GPU and optimal backend."""
        
        # Check for CUDA (NVIDIA)
        if self._check_cuda():
            self.backend = GPUBackend.CUDA
            logger.info(f"CUDA detected: {self.device_info.get('name', 'Unknown')}")
            return
        
        # Check for ROCm (AMD)
        if self._check_rocm():
            self.backend = GPUBackend.ROCM
            logger.info(f"ROCm detected: {self.device_info.get('name', 'Unknown')}")
            return
        
        # Check for OpenCL (Generic GPU)
        if self._check_opencl():
            self.backend = GPUBackend.OPENCL
            logger.info(f"OpenCL detected: {self.device_info.get('name', 'Unknown')}")
            return
        
        # Check for Vulkan (Experimental)
        if self._check_vulkan():
            self.backend = GPUBackend.VULKAN
            logger.info(f"Vulkan detected: {self.device_info.get('name', 'Unknown')}")
            return
        
        logger.info("No GPU acceleration available, using CPU")
    
    def _check_cuda(self) -> bool:
        """Check for NVIDIA CUDA support."""
        try:
            # Check OpenCV CUDA support
            if hasattr(cv2, 'cuda') and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                cv2.cuda.setDevice(0)
                device = cv2.cuda.DeviceInfo()
                self.device_info = {
                    'name': 'NVIDIA GPU (CUDA)',
                    'total_memory': device.totalMemory(),
                    'free_memory': device.freeMemory(),
                    'compute_capability': device.majorVersion() + '.' + str(device.minorVersion())
                }
                return True
        except Exception as e:
            logger.debug(f"CUDA check failed: {e}")
        return False
    
    def _check_rocm(self) -> bool:
        """Check for AMD ROCm support."""
        try:
            # Check for ROCm via rocminfo
            result = subprocess.run(
                ['rocminfo'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0 and 'AMD' in result.stdout:
                # ROCm available, check if OpenCV supports it
                # OpenCV doesn't directly support ROCm, but can use OpenCL on AMD
                if self._check_opencl_amd():
                    self.backend = GPUBackend.ROCM
                    self.device_info['backend'] = 'ROCm via OpenCL'
                    return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        except Exception as e:
            logger.debug(f"ROCm check failed: {e}")
        return False
    
    def _check_opencl(self) -> bool:
        """Check for OpenCL support."""
        try:
            if hasattr(cv2, 'ocl') and cv2.ocl.haveOpenCL():
                cv2.ocl.setUseOpenCL(True)
                if cv2.ocl.useOpenCL():
                    device = cv2.ocl.Device_getDefault()
                    self.device_info = {
                        'name': device.name() if hasattr(device, 'name') else 'OpenCL Device',
                        'vendor': device.vendor() if hasattr(device, 'vendor') else 'Unknown',
                        'version': device.version() if hasattr(device, 'version') else 'Unknown'
                    }
                    return True
        except Exception as e:
            logger.debug(f"OpenCL check failed: {e}")
        return False
    
    def _check_opencl_amd(self) -> bool:
        """Check for AMD GPU via OpenCL."""
        try:
            if hasattr(cv2, 'ocl') and cv2.ocl.haveOpenCL():
                cv2.ocl.setUseOpenCL(True)
                device = cv2.ocl.Device_getDefault()
                vendor = device.vendor() if hasattr(device, 'vendor') else ''
                if 'AMD' in vendor or 'Advanced Micro Devices' in vendor:
                    self.device_info = {
                        'name': device.name() if hasattr(device, 'name') else 'AMD GPU',
                        'vendor': 'AMD',
                        'backend': 'OpenCL'
                    }
                    return True
        except Exception:
            pass
        return False
    
    def _check_vulkan(self) -> bool:
        """Check for Vulkan support (experimental)."""
        try:
            # Vulkan support in OpenCV is very limited
            # Mainly for future use with cv::vk::VulkanBackend
            result = subprocess.run(
                ['vulkaninfo'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                self.device_info = {
                    'name': 'Vulkan Device',
                    'backend': 'Vulkan (experimental)'
                }
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False
    
    def get_backend(self) -> GPUBackend:
        """Get detected GPU backend."""
        return self.backend
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get GPU device information."""
        return self.device_info
    
    def is_accelerated(self) -> bool:
        """Check if GPU acceleration is available."""
        return self.backend != GPUBackend.NONE
    
    def print_summary(self) -> None:
        """Print GPU acceleration status."""
        print("\n" + "="*60)
        print("GPU ACCELERATION STATUS")
        print("="*60)
        print(f"Backend: {self.backend.value.upper()}")
        
        if self.device_info:
            for key, value in self.device_info.items():
                print(f"{key}: {value}")
        else:
            print("No GPU acceleration available")
            print("Using CPU-only OpenCV")
        
        print("="*60)


class AcceleratedBodyDetector:
    """
    Body detector with GPU acceleration support.
    
    Automatically selects best available backend:
    1. CUDA (NVIDIA) - Best performance
    2. ROCm/OpenCL (AMD) - Good performance
    3. OpenCL (Intel/Other) - Moderate
    4. CPU - Fallback
    """
    
    def __init__(self, prefer_gpu: bool = True):
        """Initialize with GPU acceleration if available."""
        self.gpu_detector = GPUAccelerationDetector()
        self.backend = self.gpu_detector.get_backend()
        self.prefer_gpu = prefer_gpu
        
        # GPU matrices for CUDA
        self.gpu_frame: Optional[Any] = None
        
        if self.is_gpu_available():
            logger.info(f"GPU acceleration enabled: {self.backend.value}")
        else:
            logger.info("Using CPU processing")
    
    def is_gpu_available(self) -> bool:
        """Check if GPU acceleration is active."""
        return self.prefer_gpu and self.gpu_detector.is_accelerated()
    
    def upload_frame(self, frame: np.ndarray) -> Any:
        """Upload frame to GPU memory."""
        if self.backend == GPUBackend.CUDA:
            try:
                return cv2.cuda_GpuMat(frame)
            except Exception as e:
                logger.warning(f"Failed to upload to GPU: {e}")
                return frame
        return frame
    
    def download_frame(self, gpu_frame: Any) -> np.ndarray:
        """Download frame from GPU memory."""
        if self.backend == GPUBackend.CUDA and hasattr(gpu_frame, 'download'):
            return gpu_frame.download()
        return gpu_frame
    
    def process_frame_gpu(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with GPU acceleration if available.
        
        For body detection, the actual MediaPipe inference
        happens on CPU, but we can use GPU for:
        - Color space conversion (BGR→RGB)
        - Resizing
        - Normalization
        """
        if not self.is_gpu_available():
            return frame
        
        try:
            if self.backend == GPUBackend.CUDA:
                # Use CUDA for preprocessing
                gpu_mat = self.upload_frame(frame)
                
                # Resize on GPU if needed
                target_size = (640, 480)
                if frame.shape[:2] != target_size[::-1]:
                    gpu_mat = cv2.cuda.resize(gpu_mat, target_size)
                
                # Color conversion on GPU
                if len(frame.shape) == 3:
                    gpu_mat = cv2.cuda.cvtColor(gpu_mat, cv2.COLOR_BGR2RGB)
                
                # Download for MediaPipe (CPU inference)
                return self.download_frame(gpu_mat)
            
            elif self.backend in (GPUBackend.ROCM, GPUBackend.OPENCL):
                # Use OpenCL for preprocessing
                # Enable OpenCL in OpenCV
                cv2.ocl.setUseOpenCL(True)
                
                # These operations will use OpenCL automatically
                if len(frame.shape) == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                return frame
        
        except Exception as e:
            logger.warning(f"GPU processing failed: {e}, falling back to CPU")
        
        return frame
    
    def get_performance_tips(self) -> list:
        """Get performance optimization tips based on hardware."""
        tips = []
        
        if self.backend == GPUBackend.NONE:
            tips.extend([
                "No GPU detected. For better performance:",
                "  - Use a system with NVIDIA GPU (CUDA)",
                "  - Or AMD GPU with ROCm drivers",
                "  - Reduce camera resolution to 640x480",
                "  - Use MediaPipe's 'light' model complexity",
                "  - Skip every other frame for detection"
            ])
        elif self.backend == GPUBackend.CUDA:
            tips.extend([
                "CUDA GPU detected! Optimizations enabled:",
                "  - GPU preprocessing (color conversion, resize)",
                "  - MediaPipe still runs on CPU (normal)",
                "  - Consider using TensorRT for even faster inference"
            ])
        elif self.backend == GPUBackend.ROCM:
            tips.extend([
                "AMD GPU with ROCm detected:",
                "  - Using OpenCL for preprocessing",
                "  - MediaPipe runs on CPU (no ROCm backend yet)",
                "  - For best performance, consider NVIDIA GPU"
            ])
        elif self.backend == GPUBackend.OPENCL:
            tips.extend([
                "OpenCL GPU detected:",
                "  - Using generic GPU acceleration",
                "  - Performance varies by hardware",
                "  - Intel integrated graphics: expect moderate speedup"
            ])
        
        return tips


def check_acceleration_status() -> Dict[str, Any]:
    """Check and report GPU acceleration status."""
    detector = GPUAccelerationDetector()
    
    return {
        'backend': detector.get_backend().value,
        'available': detector.is_accelerated(),
        'device_info': detector.get_device_info(),
        'tips': detector.get_backend() == GPUBackend.NONE and [
            "No GPU acceleration available",
            "OpenCV will use CPU for all operations",
            "MediaPose inference is CPU-only by design",
            "Consider upgrading GPU for better performance"
        ] or []
    }


def print_acceleration_report():
    """Print comprehensive acceleration report."""
    detector = GPUAccelerationDetector()
    detector.print_summary()
    
    print("\nOpenCV Build Information:")
    print("-" * 40)
    
    build_info = cv2.getBuildInformation()
    
    # Check for CUDA
    if 'CUDA' in build_info:
        print("✓ CUDA support compiled in")
    else:
        print("✗ CUDA not in build")
    
    # Check for OpenCL
    if cv2.ocl.haveOpenCL():
        print("✓ OpenCL available")
        print(f"  Using OpenCL: {cv2.ocl.useOpenCL()}")
    else:
        print("✗ OpenCL not available")
    
    # Check for Intel IPP
    if 'IPP' in build_info:
        print("✓ Intel IPP optimizations")
    
    # Check for OpenVINO
    if 'OpenVINO' in build_info:
        print("✓ OpenVINO inference engine")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if detector.get_backend() == GPUBackend.NONE:
        print("""
To enable GPU acceleration:

1. NVIDIA GPU (Best):
   - Install CUDA toolkit: https://developer.nvidia.com/cuda-downloads
   - Use opencv-python-cuda: pip install opencv-python-cuda
   
2. AMD GPU (Good):
   - Install ROCm: https://rocmdocs.amd.com
   - OpenCV will use OpenCL automatically
   
3. Intel GPU (Moderate):
   - OpenCL support is usually built-in
   - Ensure OpenCL drivers installed

For MediaPipe specifically:
- Currently CPU-only for pose detection
- GPU acceleration is limited to preprocessing
- Future versions may add GPU inference
        """)
    else:
        print(f"✓ GPU acceleration active: {detector.get_backend().value.upper()}")
        print("  Preprocessing operations will use GPU")
        print("  MediaPipe inference remains on CPU (by design)")


if __name__ == "__main__":
    print_acceleration_report()
