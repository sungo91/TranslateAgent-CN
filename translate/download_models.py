import os
from modelscope import snapshot_download

def download_models():
    """
    从ModelScope下载所需的模型到指定目录
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 创建tts目录（如果不存在）
    # tts_dir = os.path.join(project_root, 'translate', 'models', 'tts')
    # os.makedirs(tts_dir, exist_ok=True)
    
    # embeddings目录应该已经存在
    embeddings_dir = os.path.join(project_root, 'translate', 'models', 'embeddings')
    os.makedirs(embeddings_dir, exist_ok=True)
    
    # print("开始下载myshell-ai/MeloTTS-Chinese模型到tts目录...")
    # try:
    #     model_dir = snapshot_download(
    #         'myshell-ai/MeloTTS-Chinese',
    #         local_dir=tts_dir
    #     )
    #     print(f"MeloTTS-Chinese模型已成功下载到: {model_dir}")
    # except Exception as e:
    #     print(f"下载myshell-ai/MeloTTS-Chinese模型时出错: {e}")
    
    print("开始下载sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2模型到embeddings目录...")
    try:
        model_dir = snapshot_download(
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            local_dir=embeddings_dir
        )
        print(f"sentence-transformers模型已成功下载到: {model_dir}")
    except Exception as e:
        print(f"下载sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2模型时出错: {e}")

if __name__ == "__main__":
    download_models()