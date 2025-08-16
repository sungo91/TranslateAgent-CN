#!/usr/bin/env python3
"""
启动文件，用于下载模型并同时启动translateAgent和webUI服务
"""

import subprocess
import sys
import time
import socket

from utils.config import Config


def is_port_open(host, port):
    """检查指定主机和端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def wait_for_fastapi_startup(host='localhost', port=8000, timeout=30):
    """等待FastAPI服务启动完成"""
    print(f"等待FastAPI服务在 {host}:{port} 上启动...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if is_port_open(host, port):
            print("FastAPI服务已启动并可访问")
            return True
        time.sleep(1)
    
    print(f"等待FastAPI服务启动超时 ({timeout}秒)")
    return False


def start_services():
    """启动translateAgent和webUI服务"""
    print("启动translateAgent和webUI服务...")
    
    # 在后台启动 FastAPI 服务
    fastapi_process = subprocess.Popen([sys.executable, 'translateAgent.py'])
    print("FastAPI正在启动")
    
    # 等待FastAPI服务完全启动
    if wait_for_fastapi_startup(port=Config.PORT):
        # 前台启动 Gradio（主进程，保持容器不退出）
        gradio_process = subprocess.Popen([sys.executable, 'webUI.py'])
        print("Gradio服务启动")
    else:
        print("FastAPI服务启动失败，无法启动Gradio服务")
        fastapi_process.terminate()
        fastapi_process.wait()
        return
    
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