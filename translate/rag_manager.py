"""
@File    : rag_manager.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/08/02 17:15
"""

"""
RAG 知识库管理模块：负责与 ChromaDB 交互，实现知识库的增、删、查。
"""

import os
os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'  # 关闭遥测

import logging
import pandas as pd
import re
from typing import List, Dict, Set
import jieba
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# >>>>>>>>>>>> 配置 <<<<<<<<<<<<
CHROMA_DB_DIR = "./chroma_db"
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# 模型路径
LOCAL_MODEL_PATH = "./models/embeddings"

class RAGManager:
    def __init__(self):
        self.chroma_client = None
        self.embedding_model = None
        self._load_models()

    def _load_models(self):
        # 初始化组件
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_DB_DIR,
            settings=Settings(anonymized_telemetry=False)
        )

        if not os.path.exists(LOCAL_MODEL_PATH):
            raise FileNotFoundError(f"模型未找到: {LOCAL_MODEL_PATH}，请先运行download_models.py下载模型。")

        # 加载本地模型（离线）
        self.embedding_model = SentenceTransformer(
            LOCAL_MODEL_PATH,
            trust_remote_code=True
        )

    def get_collections_list(self) -> List[Dict]:
        """
        从 ChromaDB 获取所有 collection，返回可用于 Gradio Dataframe 的列表。
        """
        try:
            collection_names = self.chroma_client.list_collections()
            kb_list = []

            for name in collection_names:
                try:
                    collection = self.chroma_client.get_collection(name=name)
                    kb_list.append({
                        "Selected": False,
                        "Name": collection.name,
                        "Status": "Loaded",
                        "Count": collection.count()
                    })
                except Exception as e:
                    # 如果某个 collection 无法加载（可能已损坏），仍将其列出
                    kb_list.append({
                        "Selected": False,
                        "Name": name,
                        "Status": "Error",
                        "Count": "N/A"
                    })
                    logger.warning(f"无法加载 collection '{name}': {e}")

            logger.info(f"从 ChromaDB 加载了 {len(kb_list)} 个知识库")
            return kb_list
        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            return []

    def build_knowledge_base(self, file_path: str, current_kbs: List[Dict] = None) -> tuple:
        """
        核心函数：将上传的文件构建为 ChromaDB collection。
        Args:
            file_path (str): 上传文件的临时路径
        Returns:
            tuple: (updated_list, status_message)
        """
        try:
            # 1. 读取 CSV 文件
            df = pd.read_csv(file_path)
            required_columns = {'source', 'target'}
            if not required_columns.issubset(df.columns):
                msg = f"文件缺少必要列，需要 {required_columns}，但只有 {list(df.columns)}"
                logger.error(msg)
                return current_kbs, msg

            sentences = df['source'].astype(str).tolist()
            translations = df['target'].astype(str).tolist()
            ids = [f"pair_{i}" for i in range(len(sentences))]

            # 2. 提取 collection 名称
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            collection_name = f"kb_{base_name}"

            # 3. 检查是否已存在
            collection_names = self.chroma_client.list_collections()
            if collection_name in collection_names:
                msg = f"知识库 '{collection_name}' 已存在，请上传其他文件。"
                logger.warning(msg)
                return current_kbs, msg

            # 4. 创建 collection 并添加数据
            collection = self.chroma_client.create_collection(name=collection_name)

            # 生成嵌入
            embeddings = self.embedding_model.encode(sentences).tolist()

            # 添加到数据库
            collection.add(
                embeddings=embeddings,
                metadatas=[{"source": s, "target": t} for s, t in zip(sentences, translations)],
                documents=sentences,
                ids=ids
            )

            msg = f"✅ 知识库 '{collection_name}' 构建成功，包含 {len(sentences)} 个句对。"
            logger.info(msg)

            # 5. 返回更新后的列表
            updated_list = self.get_collections_list()
            return updated_list, msg

        except Exception as e:
            logger.error(f"构建知识库失败: {e}")
            return current_kbs, f"❌ 构建失败: {str(e)}"

    def delete_collections(self, selected_names: List[str], current_kbs: List[Dict] = None) -> tuple:
        """
        删除指定名称的 collections。
        Args:
            selected_names: 要删除的 collection 名称列表
        Returns:
            tuple: (updated_list, status_message)
        """
        if not selected_names or not isinstance(selected_names, list):
            return current_kbs or self.get_collections_list(), "没有选择要删除的知识库。"

        deleted = []
        failed = []

        for name in selected_names:
            try:
                self.chroma_client.delete_collection(name=name)
                deleted.append(name)
                logger.info(f"已删除知识库: {name}")
            except Exception as e:
                failed.append(f"{name}: {str(e)}")

        msg_parts = []
        if deleted:
            msg_parts.append(f"✅ 成功删除 {len(deleted)} 个知识库: {', '.join(deleted)}")
        if failed:
            msg_parts.append(f"❌ 删除失败 {len(failed)} 个: {'; '.join(failed)}")

        updated_list = self.get_collections_list()
        return updated_list, "\n".join(msg_parts) if msg_parts else "操作完成。"

    def extract_english_terms(self, text: str) -> Set[str]:
        """
        提取文本中的英文术语，包括：
        - 短缩写 (xmy, abc)
        - 长单词 (hello, translate)
        - 带数字的组合 (user123, model_v2)
        """
        # 放宽限制，匹配 2-20 个字符的英文单词/缩写
        pattern = r'\b[a-zA-Z]{2,20}\d*\b'
        return set(re.findall(pattern, text, re.IGNORECASE))

    def extract_chinese_entities(self, text: str) -> Set[str]:
        """
        提取文本中的中文实体（如人名、专有名词）。
        使用简单规则 + jieba 分词。
        """
        # 简单规则：连续2-5个中文字符（可能是人名、术语）
        basic_entities = set(re.findall(r'[\u4e00-\u9fa5]{2,5}', text))

        # 使用 jieba 分词（如果安装了 jieba）
        try:
            words = jieba.lcut(text)
            # 过滤出可能是实体的词（长度2-5的中文词）
            jieba_entities = {w for w in words if 2 <= len(w) <= 5 and re.fullmatch(r'[\u4e00-\u9fa5]+', w)}
            return basic_entities.union(jieba_entities)
        except ImportError:
            return basic_entities

    def retrieve_similar_pairs(
            self,
            query: str,
            collection_name: str = None,
            n_results: int = 3,
            similarity_threshold: float = 0.3
    ) -> List[Dict]:
        try:
            if collection_name:
                collections = [self.chroma_client.get_collection(name=collection_name)]
            else:
                collections = [self.chroma_client.get_collection(name=c) for c in self.chroma_client.list_collections()]

            if not collections:
                logger.info("No collections found in ChromaDB.")
                return []

            query_embedding = self.embedding_model.encode([query]).tolist()
            results = []

            # >>>>>>>>>>>> 提取英文术语（支持长单词） <<<<<<<<<<<<
            english_terms = self.extract_english_terms(query)
            logger.info(f"从查询中提取到英文术语: {english_terms}")

            # >>>>>>>>>>>> 提取中文实体 <<<<<<<<<<<<
            chinese_entities = self.extract_chinese_entities(query)
            logger.info(f"从查询中提取到中文实体: {chinese_entities}")

            # 合并所有要精确匹配的关键词
            exact_keywords = english_terms.union(chinese_entities)
            logger.info(f"综合关键词: {exact_keywords}")

            for coll in collections:
                # 1. 精确匹配：检查 source 是否在关键词中（正向匹配）
                for keyword in exact_keywords:
                    try:
                        res = coll.get(
                            where={"source": keyword.lower() if keyword.isascii() else keyword},
                            include=["metadatas", "documents"]
                        )
                        if res['ids']:
                            for i in range(len(res['ids'])):
                                results.append({
                                    "source": res['metadatas'][i]['source'],
                                    "target": res['metadatas'][i]['target'],
                                    "distance": 0.0,
                                    "collection": coll.name,
                                    "match_type": "exact_keyword"
                                })
                    except Exception as e:
                        logger.debug(f"精确匹配 {keyword} 时出错: {e}")
                        continue

                # 2. 子串匹配：如果 query 包含 source，且 source 是短字符串（可能是实体）
                try:
                    # 获取 collection 中的所有 source
                    all_items = coll.get(include=["metadatas"])
                    for meta in all_items['metadatas']:
                        source = meta['source']
                        # 如果 source 是短字符串（如人名、术语），且出现在 query 中
                        if len(source) <= 10 and (source in query or source.lower() in query.lower()):
                            results.append({
                                "source": source,
                                "target": meta['target'],
                                "distance": 0.1,  # 比完全匹配稍低
                                "collection": coll.name,
                                "match_type": "substring_match"
                            })
                except Exception as e:
                    logger.debug(f"子串匹配出错: {e}")

                # 3. 语义相似度检索
                try:
                    semantic_res = coll.query(
                        query_embeddings=query_embedding,
                        n_results=n_results,
                        include=["metadatas", "distances"]
                    )
                    for i in range(len(semantic_res['ids'][0])):
                        distance = semantic_res['distances'][0][i]
                        if distance < similarity_threshold:
                            metadata = semantic_res['metadatas'][0][i]
                            results.append({
                                "source": metadata.get("source", metadata.get("document")),
                                "target": metadata["target"],
                                "distance": distance,
                                "collection": coll.name,
                                "match_type": "semantic"
                            })
                except Exception as e:
                    logger.debug(f"语义检索出错: {e}")

            # 去重：基于 (source, target)
            seen = set()
            unique_results = []
            for item in results:
                key = (item['source'], item['target'])
                if key not in seen:
                    seen.add(key)
                    unique_results.append(item)

            # 按 distance 排序
            unique_results.sort(key=lambda x: x['distance'])
            return unique_results[:n_results]

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

# 创建全局实例
ragManager = RAGManager()