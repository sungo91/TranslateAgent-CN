#!/bin/bash
# start.sh - 同时启动 FastAPI 和 Gradio 服务

set -e

# 在后台启动 FastAPI 服务
python translate/translateAgent.py &

# 给 FastAPI 一点时间启动（可选）
sleep 2

# 前台启动 Gradio（主进程，保持容器不退出）
python translate/webUI.py

# wait 会等待所有后台进程，但由于 webUI 是前台，其实可以不用
wait