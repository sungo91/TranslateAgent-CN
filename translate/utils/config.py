# config.py
import os

"""
@File    : config.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/7/25 00:51
"""

class Config:


    # 日志持久化存储
    LOG_FILE = "output/app.log"
    MAX_BYTES=5*1024*1024,
    BACKUP_COUNT=3


    # openai:调用gpt模型,oneapi:调用oneapi方案支持的模型,ollama:调用本地开源大模型,qwen:调用阿里通义千问大模型
    LLM_TYPE = "ollama"

    # API服务地址和端口
    HOST = "0.0.0.0"
    PORT = 8012
    TRANSLATEAPI = "/v1/chat/translate"