import os
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_huggingface import HuggingFacePipeline
import logging
from dotenv import load_dotenv
import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

"""
@File    : llms.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/7/25 00:51
"""

# 加载.env文件
load_dotenv()

# 设置日志模版
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# 模型配置字典从环境变量读取
MODEL_CONFIGS = {
    "ollama": {
        "base_url": os.getenv("OLLAMA_BASE_URL", f"{OLLAMA_HOST}/v1"),
        "api_key": os.getenv("OLLAMA_API_KEY", "ollama"),
        "chat_model": os.getenv("OLLAMA_CHAT_MODEL", "qwen3:8b")
    },
    "chatglm": {
        "base_url": os.getenv("CHATGLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
        "api_key": os.getenv("CHATGLM_API_KEY", "api_key"),
        "chat_model": os.getenv("CHATGLM_CHAT_MODEL", "glm-4-flash")
    },
    "huggingface": {
        "model_name": os.getenv("HF_MODEL_NAME", "Qwen/Qwen3-4B-Instruct"),
        "device": os.getenv("HF_DEVICE", "cuda" if torch.cuda.is_available() else "cpu"),
        "torch_dtype": os.getenv("HF_TORCH_DTYPE", "float16" if torch.cuda.is_available() else "float32")
    }
}


# 默认配置
DEFAULT_LLM_TYPE = "ollama"
DEFAULT_TEMPERATURE = 0.6


class LLMInitializationError(Exception):
    """自定义异常类用于LLM初始化错误"""
    pass


def initialize_huggingface_llm(config):
    """
    初始化HuggingFace模型实例

    Args:
        config (dict): HuggingFace模型配置

    Returns:
        HuggingFacePipeline: 初始化后的HuggingFace模型实例
    """
    try:
        model_name = config["model_name"]
        device = config["device"]

        # 处理torch_dtype
        if config["torch_dtype"] == "float16":
            torch_dtype = torch.float16
        elif config["torch_dtype"] == "float32":
            torch_dtype = torch.float32
        elif config["torch_dtype"] == "bfloat16":
            torch_dtype = torch.bfloat16
        else:
            torch_dtype = "auto"

        # 加载tokenizer和model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        # 传统方式加载模型
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True
        )
        # 移动模型到指定设备
        if device == "cuda" and torch.cuda.is_available():
            model = model.to("cuda")
        else:
            model = model.to("cpu")

        # 创建pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=DEFAULT_TEMPERATURE,
            do_sample=True,
            device=0 if device == "cuda" and torch.cuda.is_available() else -1
        )

        # 创建HuggingFacePipeline实例
        llm = HuggingFacePipeline(pipeline=pipe)

        logger.info(f"成功初始化HuggingFace模型: {model_name}")
        return llm

    except Exception as e:
        logger.error(f"初始化HuggingFace模型失败: {str(e)}")
        raise LLMInitializationError(f"初始化HuggingFace模型失败: {str(e)}")

def initialize_llm(llm_type: str = DEFAULT_LLM_TYPE) -> tuple[ChatOpenAI]:
    """
    初始化LLM实例

    Args:
        llm_type (str): LLM类型，可选值为 'chatglm', 'huggingface', 'ollama'

  Returns:
        Union[ChatOpenAI, HuggingFacePipeline]: LLM实例

    Raises:
        LLMInitializationError: 当LLM初始化失败时抛出
    """
    try:
        # 检查llm_type是否有效
        if llm_type not in MODEL_CONFIGS:
            raise ValueError(f"不支持的LLM类型: {llm_type}. 可用的类型: {list(MODEL_CONFIGS.keys())}")

        config = MODEL_CONFIGS[llm_type]

        # 特殊处理huggingface类型
        if llm_type == "huggingface":
            return initialize_huggingface_llm(config)

        # 特殊处理ollama类型
        if llm_type == "ollama":
            os.environ["OPENAI_API_KEY"] = "NA"

        # 创建LLM实例
        llm_chat = ChatOpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"],
            model=config["chat_model"],
            temperature=DEFAULT_TEMPERATURE,
            timeout=30,  # 添加超时配置（秒）
            max_retries=2  # 添加重试次数
        )

        # llm_embedding = OpenAIEmbeddings(
        #     base_url=config["base_url"],
        #     api_key=config["api_key"],
        #     model=config["embedding_model"],
        #     deployment=config["embedding_model"]
        # )

        logger.info(f"成功初始化 {llm_type} LLM")
        return llm_chat

    except ValueError as ve:
        logger.error(f"LLM配置错误: {str(ve)}")
        raise LLMInitializationError(f"LLM配置错误: {str(ve)}")
    except Exception as e:
        logger.error(f"初始化LLM失败: {str(e)}")
        raise LLMInitializationError(f"初始化LLM失败: {str(e)}")


def get_llm(llm_type: str = DEFAULT_LLM_TYPE) -> ChatOpenAI:
    """
    获取LLM实例的封装函数，提供默认值和错误处理

    Args:
        llm_type (str): LLM类型

  Returns:
        Union[ChatOpenAI, HuggingFacePipeline]: LLM实例
    """
    try:
        return initialize_llm(llm_type)
    except LLMInitializationError as e:
        logger.warning(f"使用默认配置重试: {str(e)}")
        if llm_type != DEFAULT_LLM_TYPE:
            return initialize_llm(DEFAULT_LLM_TYPE)
        raise  # 如果默认配置也失败，则抛出异常


# 示例使用
if __name__ == "__main__":
    try:
        # 测试不同类型的LLM初始化
        # llm_openai = get_llm("openai")
        llm_ollama = get_llm("ollama")

        # 测试无效类型
        llm_invalid = get_llm("invalid_type")
    except LLMInitializationError as e:
        logger.error(f"程序终止: {str(e)}")