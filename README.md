# Qwen3 Translation Agent / 基于 Qwen3 的翻译 Agent

A local AI-powered translation agent based on the Qwen3 model, built for high-quality Chinese-English and English-Chinese translation.  
Supports text and file translation, and allows extension with domain-specific knowledge bases to enhance professional translation accuracy.

Support for Docker deployment.

这是一个基于 Qwen3 本地大模型的中英文翻译系统，支持文字与文件翻译，并可扩展翻译知识库，用于提升专业领域（如技术、医学、法律等）的翻译精准度。

支持docker部署。

---

## 🚀 Features | 功能亮点

- ✅ **High-quality Chinese-English and English-Chinese translation**
- ✅ **Supports both text input and file upload (.txt/.docx/.pdf)**
- ✅ **Extendable domain knowledge base for professional accuracy**
- ✅ **Runs fully locally via Ollama + Qwen3**
- ✅ **Simple API/CLI ready for integration**

- ✅ **中英文互译，高质量语言输出**
- ✅ **支持文字输入和文件上传翻译（.txt/.docx/.pdf）**
- ✅ **可扩展领域知识库，提升专业翻译效果**
- ✅ **完全本地运行，无需联网，支持 Ollama 部署的 Qwen3**
- ✅ **提供简洁 API 和命令行接口，方便集成**

---

## 📦 Requirements | 环境依赖

- [Ollama](https://ollama.com) with `qwen3` model installed
- Python 3.9+
- `fastapi`, `pydantic`, `uvicorn`, `langchain`, `llama-cpp-python`, etc.

```bash
pip install -r requirements.txt
