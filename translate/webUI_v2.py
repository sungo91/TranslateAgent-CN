# 导入 Gradio 库，用于构建交互式前端界面
import gradio as gr
# 导入 requests 库，用于发送 HTTP 请求
import requests
# 导入 json 库，用于处理 JSON 数据
import json
import time
import threading
import queue
from typing import List, Dict
# 导入统一的 Config 类
from utils.config import Config
# 导入 logging 库，用于记录日志
import logging

from tts_edge_module import tts_manager

"""
@File    : webUI_v2.py
@Project : TranslateAgent-CN
@Author  : SunGo
@Date    : 2025/8/17
"""

# 设置日志的基本配置，指定日志级别为 INFO，并定义日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 创建一个名为当前模块的日志记录器
logger = logging.getLogger(__name__)

# 定义后端服务接口的 URL 地址
url = f"http://127.0.0.1:{Config.PORT}{Config.TRANSLATEAPI}"
rag_url = f"http://127.0.0.1:{Config.PORT}/api/rag"  # RAG管理接口
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
                    format_result = result[0].split('<tool_call>\n\n')[-1]
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

def play_translation(text):
    """
    调用 TTS 模块播报翻译结果。
    """
    if not text or text == "翻译失败":
        return None
    return tts_manager.text_to_speech(text)

# >>>>>>>>>>>> RAG 管理相关函数 <<<<<<<<<<<<
def get_collections_list():
    """
    从后端服务获取所有知识库列表
    """
    try:
        response = requests.get(f"{rag_url}/collections", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"获取知识库列表失败: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"获取知识库列表异常: {e}")
        return []

def build_knowledge_base(file_path, current_kbs):
    """
    上传文件并构建知识库
    """
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{rag_url}/collections", files=files, timeout=30)
            
        if response.status_code == 200:
            result = response.json()
            updated_list = get_collections_list()  # 重新获取列表
            return updated_list, result.get("message", "操作完成")
        else:
            logger.error(f"构建知识库失败: {response.status_code}")
            return current_kbs, f"构建失败: HTTP {response.status_code}"
    except Exception as e:
        logger.error(f"构建知识库异常: {e}")
        return current_kbs, f"构建失败: {str(e)}"

def delete_collections(selected_names, current_kbs):
    """
    删除指定的知识库
    """
    if not selected_names or not isinstance(selected_names, list):
        return current_kbs, "没有选择要删除的知识库。"
    
    try:
        data = {"names": selected_names}
        response = requests.delete(f"{rag_url}/collections", headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            updated_list = get_collections_list()  # 重新获取列表
            return updated_list, result.get("message", "操作完成")
        else:
            logger.error(f"删除知识库失败: {response.status_code}")
            return current_kbs, f"删除失败: HTTP {response.status_code}"
    except Exception as e:
        logger.error(f"删除知识库异常: {e}")
        return current_kbs, f"删除失败: {str(e)}"

with gr.Blocks() as demo:
    gr.Markdown("# TranslateAgent-CN 智能翻译系统")

    # 注入 CSS 样式
    demo.load(
        None,
        None,
        None,
        js="""
    () => {
        const style = document.createElement('style');
        style.innerHTML = `
            #input-area textarea {
                height: 35vh !important;
                resize: vertical;
                margin-top: 0.25em !important;
            }
            #output-area textarea {
                height: 35vh !important;
                resize: vertical;
                margin-top: 0.25em !important;
            }
            #tts-play-btn {
                width: 24px !important;
                height: 24px !important;
                min-width: 24px !important;
                padding: 0 !important;
                margin-left: 0.25em !important;
                font-size: 12px !important;
            }
            #tts-play-btn:hover {
                background-color: #f0f0f0 !important;
                border-color: #999999 !important;
            }
            #translate-btn {
                font-weight: bold;
                margin-top: 0.5em;
            }
            #output-label {
                margin-bottom: 0;
                font-weight: bold;
            }
            #audio-player {
                display: none;
            }
            .nav-button {
                font-size: 16px !important;
                padding: 10px !important;
                margin: 5px !important;
                border-radius: 8px !important;
                width: 100%;
                display: block !important;
                transition: all 0.3s ease !important;
            }
            .nav-button-primary {
                background: linear-gradient(45deg, #4CAF50, #45a049) !important;
                color: white !important;
                border: none !important;
            }
            .nav-button-secondary {
                background: linear-gradient(45deg, #2196F3, #1976D2) !important;
                color: white !important;
                border: none !important;
            }
            .nav-button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            }
            div.nav-column {
                background-color: white;
                border-radius: 6px;
                padding: 6px 2px;
                height: fit-content;
                width: 150px !important;
                min-width: 150px !important;
                max-width: 150px !important;
            }
            div.kb-file-input div.wrap {
                min-height: 125px !important;
                height: 125px !important;
            }
        `;
        document.head.appendChild(style);
    }
    """
    )

    with gr.Row():
        # 左侧导航栏
        with gr.Column(scale=0, elem_classes=["nav-column"], min_width=50):
            translate_btn = gr.Button("📝 翻译", elem_classes=["nav-button", "nav-button-primary"], variant="primary")
            kb_btn = gr.Button("📚 知识库", elem_classes=["nav-button", "nav-button-secondary"], variant="secondary")
        
        # 右侧内容区域
        with gr.Column(scale=1):
            # 翻译界面
            with gr.Column(visible=True) as translate_panel:
                gr.Markdown("## 📝 翻译")
                
                with gr.Row():
                    direction = gr.Radio(
                        choices=[("英译中", "en2cn"), ("中译英", "cn2en")],
                        value="en2cn",
                        show_label=False
                    )
                    time_text = gr.Textbox(
                        placeholder="耗时",
                        show_label=False
                    )

                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            gr.Markdown("**输入文本**", elem_id="output-label")  # 模拟 Label
                            # 小型播放按钮
                            input_tts_btn = gr.Button("🔊", elem_id="tts-play-btn", variant="secondary")

                        input_text = gr.TextArea(
                            placeholder="请输入要翻译的内容",
                            elem_id="input-area",
                            show_label=False
                        )

                    with gr.Column():
                        with gr.Row():
                            gr.Markdown("**翻译结果**", elem_id="output-label")  # 模拟 Label
                            # 小型播放按钮
                            output_tts_btn = gr.Button("🔊", elem_id="tts-play-btn", variant="secondary")

                        output_text = gr.Textbox(
                            show_copy_button=True,
                            elem_id="output-area",
                            show_label=False
                        )

                translate_action_btn = gr.Button("🚀 翻译", elem_id="translate-btn")
                translate_action_btn.click(
                    fn=send_message,
                    inputs=[input_text, direction],
                    outputs=[output_text, time_text]
                )

                audio_output = gr.Audio(
                    autoplay=True,
                    visible=True,
                    interactive=False,
                    show_label=False,
                    elem_id="audio-player"
                )

                input_tts_btn.click(
                    fn=play_translation,
                    inputs=[input_text],
                    outputs=[audio_output]
                )

                output_tts_btn.click(
                    fn=play_translation,
                    inputs=[output_text],
                    outputs=[audio_output]
                )
            
            # 知识库管理界面
            with gr.Column(visible=False) as kb_panel:
                gr.Markdown("## 📚 知识库管理")
                gr.Markdown("上传您的双语语料库（需.CSV格式），以启用检索增强翻译功能。")
                
                # 上传区
                with gr.Row():
                    kb_file_input = gr.File(
                        label="上传知识库文件,请使用英文文件名",
                        file_types=[".csv"],  # 限制文件类型
                        file_count="single",  # 只允许单个文件
                        elem_classes=["kb-file-input"]  # 添加CSS类以控制高度
                    )
                kb_load_btn = gr.Button("🧠 构建向量数据库")
                kb_status_output = gr.Textbox(label="操作状态")

                # 知识库列表区
                gr.Markdown("### 已加载的知识库")
                # 使用 State 来存储当前的知识库列表
                kb_list_state = gr.State(value=get_collections_list())  # 初始化状态

                # Dropdown 用于选择要删除的知识库（支持多选）
                kb_dropdown = gr.Dropdown(
                    label="选择要删除的知识库",
                    choices=[],  # 初始为空，稍后填充
                    value=[],  # 初始为空
                    multiselect=True,
                    interactive=True
                )

                # 操作按钮
                with gr.Row():
                    refresh_list_btn = gr.Button("🔄 刷新列表")
                    delete_selected_btn = gr.Button("🗑️ 删除选中", variant="secondary")

                # >>>>>>>>>>>> 事件处理 <<<<<<<<<<<<
                # 加载知识库
                kb_load_btn.click(
                    fn=build_knowledge_base,
                    inputs=[kb_file_input, kb_list_state],
                    outputs=[kb_list_state, kb_status_output]
                ).then(
                    # 加载完成后刷新列表显示
                    fn=lambda kb_list: gr.update(choices=[kb["Name"] for kb in kb_list]),
                    inputs=[kb_list_state],
                    outputs=[kb_dropdown]
                ).then(
                    fn=lambda: gr.update(value=[]),
                    inputs=[],
                    outputs=[kb_dropdown]
                )

                # 刷新列表
                refresh_list_btn.click(
                    fn=get_collections_list,
                    inputs=[],
                    outputs=[kb_list_state]
                ).then(
                    fn=lambda kb_list: gr.update(choices=[kb["Name"] for kb in kb_list]),
                    inputs=[kb_list_state],
                    outputs=[kb_dropdown]
                ).then(
                    fn=lambda: gr.update(value=[]),
                    inputs=[],
                    outputs=[kb_dropdown]
                )

                # 删除选中
                delete_selected_btn.click(
                    fn=delete_collections,
                    inputs=[kb_dropdown, kb_list_state],
                    outputs=[kb_list_state, kb_status_output]
                ).then(
                    fn=lambda kb_list: gr.update(choices=[kb["Name"] for kb in kb_list]),
                    inputs=[kb_list_state],
                    outputs=[kb_dropdown]
                ).then(
                    fn=lambda: gr.update(value=[]),
                    inputs=[],
                    outputs=[kb_dropdown]
                )

                # 页面首次加载时，生成初始列表
                demo.load(
                    fn=lambda kb_list: gr.update(choices=[kb["Name"] for kb in kb_list]),
                    inputs=[kb_list_state],
                    outputs=[kb_dropdown]
                )
        
        # 切换按钮事件处理
        translate_btn.click(
            fn=lambda: (gr.update(visible=True), gr.update(visible=False), 
                       gr.update(variant="primary", elem_classes=["nav-button", "nav-button-primary"]), 
                       gr.update(variant="secondary", elem_classes=["nav-button", "nav-button-secondary"])),
            inputs=[],
            outputs=[translate_panel, kb_panel, translate_btn, kb_btn]
        )
        
        kb_btn.click(
            fn=lambda: (gr.update(visible=False), gr.update(visible=True),
                       gr.update(variant="secondary", elem_classes=["nav-button", "nav-button-secondary"]), 
                       gr.update(variant="primary", elem_classes=["nav-button", "nav-button-primary"])),
            inputs=[],
            outputs=[translate_panel, kb_panel, translate_btn, kb_btn]
        )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, show_api=False)