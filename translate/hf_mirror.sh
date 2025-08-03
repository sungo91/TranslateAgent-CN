#!/usr/bin/env bash
# 给脚本添加执行权限
chmod +x hfd.sh
# 验证是否下载成功
ls -la hfd.sh
# 应该看到 -rwxr-xr-x 表示有执行权限

# 设置镜像环境变量（告诉它走国内镜像）
export HF_ENDPOINT=https://hf-mirror.com

# 创建模型存储目录
mkdir -p ./models/embeddings/multilingual-minilm

# 使用 hfd.sh 下载模型到指定目录
# 注意：使用完整的模型ID，并指定 --local-dir
./hfd.sh sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 --local-dir ./models/embeddings/multilingual-minilm --revision main