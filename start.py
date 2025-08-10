#!/usr/bin/env python3
"""
启动文件，用于下载模型并同时启动translateAgent和webUI服务
"""

import subprocess
import sys
import os

def download_models():
    """下载模型文件"""
    print("开始下载模型...")
    try:
        # 执行下载模型的脚本
        result = subprocess.run([sys.executable, 'download_models.py'], 
                              check=True, capture_output=True, text=True)
        print("模型下载完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"模型下载失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except FileNotFoundError:
        print("未找到download_models.py文件，跳过模型下载步骤")
        return True

def start_services():
    """启动translateAgent和webUI服务"""
    print("启动translateAgent和webUI服务...")
    
    # 在后台启动 FastAPI 服务
    fastapi_process = subprocess.Popen([sys.executable, 'translate/translateAgent.py'])
    print("FastAPI服务已启动")
    
    # 给 FastAPI 一点时间启动（可选）
    import time
    time.sleep(2)
    
    # 前台启动 Gradio（主进程，保持容器不退出）
    gradio_process = subprocess.Popen([sys.executable, 'translate/webUI.py'])
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
    # 首先下载模型
    if download_models():
        # 然后启动服务
        start_services()
    else:
        print("模型下载失败，无法启动服务")
        sys.exit(1)