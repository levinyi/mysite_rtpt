FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 设置国内源
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb http://mirrors.aliyun.com/debian bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    default-mysql-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ⭐ 优化：先只复制 requirements.txt（只有依赖变化时才重新构建此层）
COPY requirements.txt /app/

# ⭐ 优化：安装项目所需的依赖（此层会被缓存，除非 requirements.txt 变化）
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# ⭐ 优化：最后才复制应用代码（代码变化不会触发依赖重装）
COPY . /app/
