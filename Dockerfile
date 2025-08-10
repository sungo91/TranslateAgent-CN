# 使用官方 Python 运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目
COPY . .

# 设置日志目录权限
RUN mkdir -p translate/output && chmod -R 777 translate/output

# 暴露端口
EXPOSE 8012 7860

# 直接运行Python启动文件
CMD ["python", "start.py"]