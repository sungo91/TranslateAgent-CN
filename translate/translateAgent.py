# 导入操作系统接口模块，用于处理文件路径和环境变量
import os
# 用于正则表达式匹配和处理字符串
import re
# 用于JSON数据的序列化和反序列化
import json
# 用于定义异步上下文管理器
from contextlib import asynccontextmanager
# 用于类型提示，定义列表和可选参数
from typing import List, Tuple, Literal
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
# 从typing模块导入类型提示工具
from typing import Optional
# 导入Pydantic的基类和字段定义工具
from pydantic import BaseModel
# 导入自定义的get_llm函数，用于获取LLM模型
from utils.llms import get_llm
# 导入统一的 Config 类
from utils.config import Config

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver


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
    backupCount = Config.BACKUP_COUNT,
    encoding='utf-8'
)
# 设置处理器级别为DEBUG
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)


# 定义消息类，用于封装API接口返回数据
# 定义Message类
class Message(BaseModel):
    role: str
    content: str

# 定义ChatCompletionRequest类
class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = False
    translateType: Optional[Literal['en2cn', 'cn2en']] = 'en2cn'
    userId: Optional[str] = None
    conversationId: Optional[str] = None


# 管理 FastAPI 应用生命周期的异步上下文管理器，负责启动和关闭时的初始化与清理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理 FastAPI 应用生命周期的异步上下文管理器，负责启动和关闭时的初始化与清理。

    Args:
        app (FastAPI): FastAPI 应用实例。

    Yields:
        None: 在 yield 前完成初始化，yield 后执行清理。

    Raises:
        Exception: 其他未预期的异常。
    """
    # 声明全局变量 agent
    global agent

    try:
        # 调用 get_llm 初始化聊天模型
        llm_chat = get_llm(Config.LLM_TYPE)

        # 定义系统消息，指导如何使用工具
        system_message = SystemMessage(content=(
            "你是一个专业的中英翻译员,注意保持专业术语准确和语义准确,翻译速度要快,翻译速度要快,翻译速度要快"
        ))

        # 这里使用内存存储 也可以持久化到数据库
        memory = MemorySaver()

        # 创建ReAct风格的agent
        agent = create_react_agent(
            model=llm_chat,
            tools=[],
            prompt=system_message,
            # checkpointer=memory,
        )

        # 保存状态图的可视化表示
        # save_graph_visualization(agent)

    except Exception as e:
        # 捕获并记录其他未预期的异常
        logger.error(f"Unexpected error: {e}")
        # 退出程序，返回状态码 1
        sys.exit(1)

    # yield 表示应用运行期间，初始化完成后进入运行状态
    yield
    # 记录服务关闭的日志
    logger.info("The service has been shut down")

# 创建FastAPI实例 lifespan参数用于在应用程序生命周期的开始和结束时执行一些初始化或清理工作
app = FastAPI(lifespan=lifespan)

# 依赖注入函数，用于获取 graph 和 tool_config
async def get_dependencies() -> Tuple[any]:
    """
    依赖注入函数，用于获取 agent。

    Returns:
        Tuple: 包含 (agent) 的元组。

    Raises:
        HTTPException: 如果 agent 未初始化，则抛出 500 错误。
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return agent

@app.post(Config.TRANSLATEAPI)
async def chat_translate(request: ChatCompletionRequest, dependencies: Tuple[any] = Depends(get_dependencies)):
    """接收来自前端的请求数据进行业务的处理。

    Args:
        request: 请求参数。

    Returns:
        标准的Python字典。
    """
    try:
        agent = dependencies
        # 检查request是否有效
        if not request.messages or not request.messages[-1].content:
            logger.error("Invalid request: Empty or invalid messages")
            raise HTTPException(status_code=400, detail="Messages cannot be empty or invalid")
        user_input = request.messages[-1].content
        logger.info(f"The user's user_input is: {user_input}")

        # 定义运行时配置，包含线程ID和用户ID，使用默认值防止未定义
        config = {
            "configurable": {
                "thread_id": f"{getattr(request, 'userId', 'unknown')}@@{getattr(request, 'conversationId', 'default')}",
                "user_id": getattr(request, 'userId', 'unknown')
            }
        }

        # 在 messages 中拼接一条“控制性” HumanMessage，指定翻译方向
        if request.translateType == "cn2en":
            direction_tip = "请将下面这段话翻译成英文："
        elif request.translateType == "en2cn":
            direction_tip = "Please translate the following text into Chinese:"
        else:
            raise HTTPException(status_code=400, detail="Unsupported translate_type: should be 'cn2en' or 'en2cn'")

        input_message = HumanMessage(content=direction_tip + user_input)

        # 调用非流式输出
        output_message = await agent.ainvoke({"messages": [input_message]}, config)
        logger.info(f"The output_message is: {output_message}")
        return output_message

    except Exception as e:
        logger.error(f"Error handling chat completion:\n\n {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"Start the server on port {Config.PORT}")
    # uvicorn是一个用于运行ASGI应用的轻量级、超快速的ASGI服务器实现
    # 用于部署基于FastAPI框架的异步PythonWeb应用程序
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)