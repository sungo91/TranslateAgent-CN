import os
import re
from typing import List, Tuple
import logging
from utils.config import Config

"""
@File    : book_processor.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/8/18
"""

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BookProcessor:
    """
    书籍处理器，用于处理文本文件的读取、分割和重组
    """
    
    def __init__(self, max_chunk_length: int = 7000):
        """
        初始化书籍处理器
        
        Args:
            max_chunk_length: 每个文本块的最大长度
        """
        self.max_chunk_length = max_chunk_length
    
    def read_txt_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        读取TXT文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码，默认为utf-8
            
        Returns:
            文件内容字符串
        """
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            logger.info(f"成功读取文件: {file_path}")
            return content
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
            raise
    
    def split_text(self, text: str) -> List[str]:
        """
        将文本按照段落或完整句子进行分割，并确保每个片段不超过最大长度
        
        Args:
            text: 要分割的文本
            
        Returns:
            分割后的文本片段列表
        """
        # 首先按段落分割（两个或更多换行符）
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        
        for paragraph in paragraphs:
            # 清理段落前后空白
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 如果段落长度小于等于最大长度，直接添加
            if len(paragraph) <= self.max_chunk_length:
                chunks.append(paragraph)
            else:
                # 如果段落超过最大长度，按句子分割
                sentences = self._split_into_sentences(paragraph)
                current_chunk = ""
                
                for sentence in sentences:
                    # 如果加上当前句子会超过最大长度
                    if len(current_chunk) + len(sentence) > self.max_chunk_length:
                        # 如果当前块不为空，保存它
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            # 如果单个句子就超过最大长度，强制分割
                            chunks.extend(self._force_split_long_sentence(sentence))
                    else:
                        # 添加句子到当前块
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
                
                # 添加最后一个块
                if current_chunk:
                    chunks.append(current_chunk.strip())
        
        logger.info(f"文本分割完成，共生成 {len(chunks)} 个片段")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子
        
        Args:
            text: 要分割的文本
            
        Returns:
            句子列表
        """
        # 使用正则表达式分割句子（中文和英文句号、问号、感叹号）
        sentences = re.split(r'[。！？.!?]+', text)
        # 过滤空句子并添加回标点符号
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _force_split_long_sentence(self, sentence: str) -> List[str]:
        """
        强制分割超长句子
        
        Args:
            sentence: 要分割的句子
            
        Returns:
            分割后的句子列表
        """
        chunks = []
        start = 0
        
        while start < len(sentence):
            end = min(start + self.max_chunk_length, len(sentence))
            chunks.append(sentence[start:end])
            start = end
            
        return chunks
    
    def reconstruct_text(self, translated_chunks: List[str]) -> str:
        """
        将翻译后的文本片段重新组合成完整文本
        
        Args:
            translated_chunks: 翻译后的文本片段列表
            
        Returns:
            重组后的完整文本
        """
        # 使用两个换行符连接段落
        reconstructed_text = "\n\n".join(translated_chunks)
        logger.info(f"文本重组完成，共 {len(translated_chunks)} 个片段")
        return reconstructed_text
    
    def save_translated_book(self, translated_text: str, output_path: str, encoding: str = 'utf-8') -> None:
        """
        保存翻译后的书籍
        
        Args:
            translated_text: 翻译后的完整文本
            output_path: 输出文件路径
            encoding: 文件编码，默认为utf-8
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding=encoding) as file:
                file.write(translated_text)
            logger.info(f"翻译后的书籍已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存翻译文件失败: {output_path}, 错误: {str(e)}")
            raise


# 使用示例
if __name__ == "__main__":
    # 创建处理器实例
    processor = BookProcessor(max_chunk_length=7000)
    
    # 示例：读取文件
    content = processor.read_txt_file("example.txt")
    
    # 示例：分割文本
    chunks = processor.split_text(content)
    
    # 示例：重组文本
    reconstructed = processor.reconstruct_text(chunks)
    
    # 示例：保存文件
    output_path = os.path.join(Config.LOG_DIR, "translated_example.txt")
    processor.save_translated_book(reconstructed, output_path)
    
    print("BookProcessor 模块已创建完成")