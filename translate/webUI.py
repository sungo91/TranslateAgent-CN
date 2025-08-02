# 导入 Gradio 库，用于构建交互式前端界面
import gradio as gr
# 导入 requests 库，用于发送 HTTP 请求
import requests
# 导入 json 库，用于处理 JSON 数据
import json

import time
import threading
import queue
# 导入统一的 Config 类
from utils.config import Config
# 导入 logging 库，用于记录日志
import logging

"""
@File    : webUI.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/7/25 00:53
"""

# 设置日志的基本配置，指定日志级别为 INFO，并定义日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 创建一个名为当前模块的日志记录器
logger = logging.getLogger(__name__)

# 定义后端服务接口的 URL 地址
url = f"http://127.0.0.1:{Config.PORT}{Config.TRANSLATEAPI}"
# 定义 HTTP 请求头，指定内容类型为 JSON
headers = {"Content-Type": "application/json"}

def send_message(user_message, translate_type):
    start_time = time.time()
    status_queue = queue.Queue()
    stop_event = threading.Event()

    # 启动计时器线程
    def update_timer():
        while not stop_event.is_set():
            elapsed = time.time() - start_time
            status_queue.put({
                "content": "翻译中... ",
                "elapsed": f"已耗时: {elapsed:.3f}s"
            })
            time.sleep(0.2)  # 刷新间隔

    timer_thread = threading.Thread(target=update_timer)
    timer_thread.start()

    # 主线程循环 yield queue 中的状态
    while not stop_event.is_set():
        try:
            msg = status_queue.get(timeout=0.1)
            yield msg["content"], msg["elapsed"]
        except queue.Empty:
            continue

        # 注意：此处不能直接执行网络请求，否则 UI 阻塞
        # 我们先启动请求线程
        if 'response_thread' not in locals():
            def fetch_result():
                try:
                    data = {
                        "messages": [{"role": "user", "content": user_message}],
                        "stream": False,
                        "translateType": translate_type,
                        "userId": "111",
                        "conversationId": "1111"
                    }
                    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
                    response_json = response.json()
                    result = [item['content'] for item in response_json['messages'] if item.get('type') == 'ai']
                    format_result = result[0].split('</think>\n\n')[-1]
                    elapsed = time.time() - start_time
                    status_queue.put({
                        "content": format_result,
                        "elapsed": f"总耗时: {elapsed:.3f}s"
                    })
                except Exception as e:
                    elapsed = time.time() - start_time
                    status_queue.put({
                        "content": "翻译失败",
                        "elapsed": f"总耗时: {elapsed:.3f}s"
                    })
                finally:
                    stop_event.set()

            response_thread = threading.Thread(target=fetch_result)
            response_thread.start()

    timer_thread.join()
    response_thread.join()

    # 输出最终结果
    while not status_queue.empty():
        msg = status_queue.get()
        yield msg["content"], msg["elapsed"]


# >>>>>>>>>>>> 新增的 RAG 知识库功能 <<<<<<<<<<<<
def load_knowledge_base(file):
    """
    处理上传的知识库文件。
    这是一个占位函数。在实现 RAG 时，你需要在这里：
    1. 读取文件内容（CSV, TXT, JSON等）。
    2. 清洗和处理双语数据。
    3. 使用 Sentence-BERT 等模型生成向量。
    4. 构建 FAISS 等向量数据库索引。
    5. 保存索引文件以供翻译时检索。
    """
    if not file or not hasattr(file, "name"):
        return "请先上传知识库文件。"

    # 在这里实现你的 RAG 索引构建逻辑
    # 例如：
    # knowledge_base_path = file.name
    # build_vector_index(knowledge_base_path)  # 假设你有这个函数

    # 目前仅返回一个提示
    return f"知识库文件 '{file.name}' 已上传。后续将在此处实现RAG索引构建逻辑。"

with gr.Blocks() as demo:
    gr.Markdown("## 中英翻译器")

    # 注入 CSS 样式控制高度
    gr.HTML("""
     <style>
         #input-area textarea {
             height: 60vh !important;
             resize: vertical;
         }
         #output-area textarea {
             height: 60vh !important;
             resize: vertical;
         }
     </style>
     """)

    # >>>>>>>>>>>> 新增的 Accordion 区域 <<<<<<<<<<<<
    with gr.Accordion("RAG 知识库管理 (用于增强翻译)", open=False):
        gr.Markdown("上传您的双语语料库（如 CSV, TXT），以启用检索增强翻译功能。")
        with gr.Row():
            kb_file_input = gr.File(
                label="上传知识库文件",
                file_types=[".csv", ".txt", ".json"],  # 限制文件类型
                file_count="single"  # 只允许单个文件
            )
        kb_load_btn = gr.Button("加载并构建知识库索引")
        kb_status_output = gr.Textbox(label="状态信息")

        # 将上传的文件和加载按钮连接到处理函数
        kb_load_btn.click(
            fn=load_knowledge_base,
            inputs=[kb_file_input],
            outputs=[kb_status_output]
        )


    with gr.Row():
        direction = gr.Radio(
            choices=[("英译中", "en2cn"), ("中译英", "cn2en")],
            label="翻译方向",
            value="en2cn"
        )
        time_text = gr.Textbox(
            label="耗时"
        )

    with gr.Row():
        input_text = gr.TextArea(
            label="输入文本",
            placeholder="请输入要翻译的内容",
            elem_id="input-area"
        )
        output_text = gr.Textbox(
            label="翻译结果",
            show_copy_button=True,
            elem_id="output-area"
        )

    translate_btn = gr.Button("翻译")
    translate_btn.click(
        fn=send_message,
        inputs=[input_text, direction],
        outputs=[output_text, time_text]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, show_api=False)
