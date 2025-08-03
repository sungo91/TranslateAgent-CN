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
import logging
import pandas as pd
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 在导入 SentenceTransformer 之前设置环境变量
# 1. 设置 Hugging Face 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'  # 关闭遥测

# >>>>>>>>>>>> 配置 <<<<<<<<<<<<
CHROMA_DB_DIR = "./chroma_db"
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# 初始化组件
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DB_DIR,
    settings=Settings(anonymized_telemetry=False)
)

# 模型路径
LOCAL_MODEL_PATH = "./models/embeddings/multilingual-minilm"

if not os.path.exists(LOCAL_MODEL_PATH):
    raise FileNotFoundError(f"模型未找到: {LOCAL_MODEL_PATH}。请先使用 hfd 下载。")

# 加载本地模型（离线）
embedding_model = SentenceTransformer(
    LOCAL_MODEL_PATH,
    trust_remote_code=True
)

def get_collections_list() -> List[Dict]:
    """
    从 ChromaDB 获取所有 collection，返回可用于 Gradio Dataframe 的列表。
    """
    try:
        collection_names = chroma_client.list_collections()
        kb_list = []

        for name in collection_names:
            try:
                collection = chroma_client.get_collection(name=name)
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

def build_knowledge_base(file_path: str, current_kbs: List[Dict] = None) -> tuple:
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
        collection_names = chroma_client.list_collections()
        if collection_name in collection_names:
            msg = f"知识库 '{collection_name}' 已存在，请上传其他文件。"
            logger.warning(msg)
            return current_kbs, msg

        # 4. 创建 collection 并添加数据
        collection = chroma_client.create_collection(name=collection_name)

        # 生成嵌入
        embeddings = embedding_model.encode(sentences).tolist()

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
        updated_list = get_collections_list()
        return updated_list, msg

    except Exception as e:
        logger.error(f"构建知识库失败: {e}")
        return current_kbs, f"❌ 构建失败: {str(e)}"

def delete_collections(selected_names: List[str], current_kbs: List[Dict] = None) -> tuple:
    """
    删除指定名称的 collections。
    Args:
        selected_names: 要删除的 collection 名称列表
    Returns:
        tuple: (updated_list, status_message)
    """
    if not selected_names or not isinstance(selected_names, list):
        return current_kbs or get_collections_list(), "没有选择要删除的知识库。"

    deleted = []
    failed = []

    for name in selected_names:
        try:
            chroma_client.delete_collection(name=name)
            deleted.append(name)
            logger.info(f"已删除知识库: {name}")
        except Exception as e:
            failed.append(f"{name}: {str(e)}")

    msg_parts = []
    if deleted:
        msg_parts.append(f"✅ 成功删除 {len(deleted)} 个知识库: {', '.join(deleted)}")
    if failed:
        msg_parts.append(f"❌ 删除失败 {len(failed)} 个: {'; '.join(failed)}")

    updated_list = get_collections_list()
    return updated_list, "\n".join(msg_parts) if msg_parts else "操作完成。"

# >>>>>>>>>>>> 检索功能（供翻译时调用） <<<<<<<<<<<<
def retrieve_similar_pairs(query: str, collection_name: str = None, n_results: int = 3):
    """
    检索最相似的双语句对。
    Args:
        query: 查询句子
        collection_name: 指定 collection，None 表示搜索所有
        n_results: 返回数量
    Returns:
        List[Dict]: [{"source": "...", "target": "...", "distance": 0.x}, ...]
    """
    try:
        collections = [chroma_client.get_collection(name=collection_name)] if collection_name else \
            [chroma_client.get_collection(name=c.name) for c in chroma_client.list_collections()]

        query_embedding = embedding_model.encode([query]).tolist()
        results = []

        for coll in collections:
            res = coll.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=["metadatas", "distances"]
            )
            for i in range(len(res['ids'][0])):
                results.append({
                    "source": res['metadatas'][0][i]['source'],
                    "target": res['metadatas'][0][i]['target'],
                    "distance": res['distances'][0][i],
                    "collection": coll.name
                })

        # 按距离排序，取最相似的 n_results 个
        results.sort(key=lambda x: x['distance'])
        return results[:n_results]

    except Exception as e:
        logger.error(f"检索失败: {e}")
        return []