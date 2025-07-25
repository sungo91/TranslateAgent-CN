# 导入操作系统接口模块，用于处理文件路径和环境变量
import os
# 用于正则表达式匹配和处理字符串
import re
# 用于JSON数据的序列化和反序列化
import json
# 用于定义异步上下文管理器
from contextlib import asynccontextmanager
# 用于类型提示，定义列表和可选参数
from typing import List, Tuple
# 用于创建Web应用和处理HTTP异常
from fastapi import FastAPI, HTTPException, Depends
# 用于返回JSON和流式响应
from fastapi.responses import JSONResponse, StreamingResponse
# 用于运行FastAPI应用
import uvicorn
# 导入日志模块，用于记录程序运行时的信息
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
# 导入系统模块，用于处理系统相关的操作，如退出程序
import sys
import time
# 导入UUID模块，用于生成唯一标识符
import uuid
# 导入自定义的get_llm函数，用于获取LLM模型
from utils.llms import get_llm
# 导入统一的 Config 类
from utils.config import Config


"""
@File    : translateAgent.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/7/25 10:19
"""


# # 设置日志基本配置，级别为DEBUG或INFO
logger = logging.getLogger(__name__)
# 设置日志器级别为DEBUG
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.INFO)
logger.handlers = []  # 清空默认处理器
# 使用ConcurrentRotatingFileHandler
handler = ConcurrentRotatingFileHandler(
    # 日志文件
    Config.LOG_FILE,
    # 日志文件最大允许大小为5MB，达到上限后触发轮转
    maxBytes = Config.MAX_BYTES,
    # 在轮转时，最多保留3个历史日志文件
    backupCount = Config.BACKUP_COUNT
)
# 设置处理器级别为DEBUG
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)

if __name__ == "__main__":
    logger.info(f"Start the server on port {Config.PORT}")
    # uvicorn是一个用于运行ASGI应用的轻量级、超快速的ASGI服务器实现
    # 用于部署基于FastAPI框架的异步PythonWeb应用程序
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)