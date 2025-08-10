"""
@File    : check_gpu_support.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/08/10 11:37
"""

def check_gpu_support():
    """
    检查系统GPU支持情况
    """
    print("检查系统GPU支持情况...")
    print("=" * 50)
    
    # 检查CUDA GPU支持
    try:
        import torch
        print(f"PyTorch 版本: {torch.__version__}")
        if torch.cuda.is_available():
            print("✅ CUDA 可用")
            device_count = torch.cuda.device_count()
            print(f"检测到 {device_count} 个GPU设备:")
            for i in range(device_count):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"CUDA 版本: {torch.version.cuda}")
            
            # 显存信息
            for i in range(device_count):
                total_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                print(f"  GPU {i} 显存: {total_memory:.2f} GB")
        else:
            print("❌ CUDA 不可用")
    except ImportError:
        print("❌ 未安装PyTorch")
    except Exception as e:
        print(f"检查CUDA支持时出错: {e}")
    
    print()
    
    # 检查DirectML支持 (Windows)
    try:
        import torch_directml
        print(f"✅ DirectML 可用")
        device_count = torch_directml.device_count()
        print(f"检测到 {device_count} 个DirectML设备:")
        for i in range(device_count):
            print(f"  Device {i}: {torch_directml.device_name(i)}")
    except ImportError:
        print("❌ 未安装torch_directml")
    except Exception as e:
        print(f"检查DirectML支持时出错: {e}")
    
    print()
    
    # 检查MPS支持 (MacOS)
    try:
        import torch
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("✅ MPS (MacOS GPU加速) 可用")
        else:
            print("❌ MPS 不可用")
    except Exception as e:
        print(f"检查MPS支持时出错: {e}")
    
    print()
    print("如何启用GPU加速:")
    print("1. 确保安装了支持CUDA的PyTorch版本")
    print("2. 安装正确的CUDA驱动程序")
    print("3. 在MeloTTSManager初始化时设置use_gpu=True")
    print("   例如: melo_tts_manager = MeloTTSManager(use_gpu=True)")

if __name__ == "__main__":
    check_gpu_support()