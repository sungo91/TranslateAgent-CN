# Translation Agent / 多模型支持的中英翻译 Agent

A flexible, AI-powered translation agent supporting both local and cloud LLMs — built for high-quality Chinese-English translation.

A unified translation system that supports local Ollama models (Qwen, DeepSeek, Llama, Gemma, etc.) and OpenAI-compatible APIs (OpenAI, Azure, vLLM, Together, etc.).
Supports text, file translation, and RAG-enhanced domain-specific knowledge bases for professional accuracy.

Supports Docker deployment and provides clean API integration.

一个灵活、可扩展的中英互译系统，支持 本地大模型（Ollama） 与 OpenAI 兼容 API，专为高质量翻译设计。
支持文本与文件翻译，并可通过知识库增强（RAG）提升技术、医学、法律等专业领域的术语准确性。
支持 Docker 部署，提供简洁 API，便于集成到现有系统。

---

## 🚀 Features | 功能亮点
- 🔧 **核心功能 / Core Features**

- - ✅ 高质量中英互译：语义准确，支持口语、书面语、专业术语
- - ✅ High-quality Chinese-English translation: Semantically accurate, supports colloquial, formal, and domain-specific language.
- - ✅ 多模型支持：
- - - 本地模型：通过 Ollama 运行 qwen3, deepseek-r1, llama3, gemma3 等
- - - 远程模型：兼容 OpenAI 格式 API（如 GPT-4, Claude via API, vLLM, Together.ai）
- - ✅ Multi-model support:
- - - Local models: Run qwen3, deepseek-r1, llama3, gemma3, etc. via Ollama.
- - - Remote models: Compatible with OpenAI-style APIs (e.g., GPT-4, Claude via API, vLLM, Together.ai).
- - ✅ 灵活部署：支持本地运行、Docker 容器化、云服务集成
- - ✅ Flexible deployment: Supports local execution, Docker containerization, and cloud integration.
- - ✅ RAG 增强翻译：支持上传术语库，自动匹配并强制使用指定译法，确保术语一致性
- - ✅ RAG-enhanced translation: Upload domain-specific knowledge bases; system automatically retrieves and enforces term usage for consistency.
- 📁 **文件与输入支持 / File & Input Support**
- - ✅ 文本翻译：直接输入文本，实时翻译
- - ✅ Text translation: Input text directly for real-time translation.
- - ✅ 文件翻译：支持 .txt, .docx, .pdf 文件上传与解析
- - ✅ File translation: Supports upload and parsing of .txt, .docx, .pdf files.
- - ✅ 批量处理：可扩展为支持批量文件翻译任务
- - ✅ Batch processing: Can be extended to support batch translation of multiple files.
- 🔌 **开发者友好 / Developer Friendly**
- - ✅ 标准 API 接口：基于 FastAPI，提供 /translate 接口，兼容 OpenAI 请求格式
- - ✅ Standard API interface: Built with FastAPI, provides /translate endpoint compatible with OpenAI-style requests.
- - ✅ 命令行工具：支持 CLI 调用，便于自动化脚本集成
- - ✅ Command-line interface (CLI): Supports CLI invocation, ideal for automation and scripting.
- - ✅ 模块化设计：LLM 接入、RAG 检索、后处理等模块解耦，易于扩展
- - ✅ Modular architecture: LLM integration, RAG retrieval, and post-processing are decoupled for easy extension and maintenance.

---

## 📦 Requirements | 环境依赖

- [Ollama](https://ollama.com) with `qwen3` model installed
- Python 3.10+
- `fastapi`, `pydantic`, `uvicorn`, `langchain`, `llama-cpp-python`, etc.

```bash
./translate/hf_mirror.sh
pip install -r requirements.txt
