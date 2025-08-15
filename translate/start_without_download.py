#!/usr/bin/env python3
"""
启动文件，用于下载模型并同时启动translateAgent和webUI服务
"""

import subprocess
import sys


def start_services():
    """启动translateAgent和webUI服务"""
    print("启动translateAgent和webUI服务...")
    
    # 在后台启动 FastAPI 服务
    fastapi_process = subprocess.Popen([sys.executable, 'translateAgent.py'])
    print("FastAPI服务已启动")
    
    # 给 FastAPI 一点时间启动（可选）
    import time
    time.sleep(2)
    
    # 前台启动 Gradio（主进程，保持容器不退出）
    gradio_process = subprocess.Popen([sys.executable, 'webUI.py'])
    print("Gradio服务已启动")
    
    try:
        # 等待任意一个进程结束
        while True:
            fastapi_code = fastapi_process.poll()
            gradio_code = gradio_process.poll()
            
            if fastapi_code is not None:
                print(f"FastAPI进程已退出，退出码: {fastapi_code}")
                break
                
            if gradio_code is not None:
                print(f"Gradio进程已退出，退出码: {gradio_code}")
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("收到终止信号，正在关闭服务...")
        fastapi_process.terminate()
        gradio_process.terminate()
        
        # 等待进程完全退出
        fastapi_process.wait()
        gradio_process.wait()
        print("服务已关闭")

if __name__ == "__main__":
    start_services()