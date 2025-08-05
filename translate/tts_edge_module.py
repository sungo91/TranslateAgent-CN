"""
@File    : tts_edge_module.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/08/05 09:54
"""

import os
import logging
import asyncio
import time

import edge_tts

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置
OUTPUT_DIR = "./models/tts_output"

# 音色映射表
VOICE_PROFILES = {
    "zh": "zh-CN-XiaoxiaoNeural",  # 中文女声，清晰自然
    "en": "en-US-EricNeural"      # 英文男声
}

class EdgeTTSManager:
    def __init__(self):
        self.voice_zh = VOICE_PROFILES["zh"]
        self.voice_en = VOICE_PROFILES["en"]

    async def _text_to_speech_async(self, text: str, voice: str) -> str:
        """
        异步执行 TTS 转换。
        """
        if not text.strip():
            logger.warning("输入文本为空，跳过 TTS。")
            return None

        try:
            # 清空音频目录
            if os.path.exists(OUTPUT_DIR):
                for filename in os.listdir(OUTPUT_DIR):
                    file_path = os.path.join(OUTPUT_DIR, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"清理旧音频失败: {e}")
            else:
                os.makedirs(OUTPUT_DIR, exist_ok=True)

            communicate = edge_tts.Communicate(text, voice)
            timestamp = int(time.time() * 1000)
            output_path = os.path.join(OUTPUT_DIR, f"edge_tts_{timestamp}.mp3")
            await communicate.save(output_path)
            logger.info(f"TTS 播报 ({voice}): {text}")
            return output_path
        except Exception as e:
            logger.error(f"Edge TTS 转换失败: {e}")
            return None

    def text_to_speech(self, text: str) -> str:
        """
        同步接口，供 Gradio 调用。内部使用 asyncio.run 启动异步任务。
        Args:
            text (str): 要转换的文本。
        Returns:
            str: 生成的音频文件路径。如果失败，返回 None。
        """
        try:
            # 使用 asyncio.run 在同步函数中运行异步代码
            return asyncio.run(self._text_to_speech_async(text, self._detect_voice(text)))
        except Exception as e:
            logger.error(f"启动 TTS 任务失败: {e}")
            return None

    def _detect_voice(self, text: str) -> str:
        """
        简单的语言检测，选择合适的音色。
        """
        import re
        # 检测是否包含中文字符
        if re.search(r'[\u4e00-\u9fa5]', text):
            return self.voice_zh
        else:
            return self.voice_en

# 创建全局实例
tts_manager = EdgeTTSManager()