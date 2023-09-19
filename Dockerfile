# 使用一个官方的 Python 运行时作为父镜像
FROM python:3.10

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# 安装系统依赖

RUN apt-get clean && apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    default-libmysqlclient-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 将当前目录下的内容复制到容器的工作目录内
COPY . /app/

# 安装项目所需的依赖
RUN pip install --no-cache-dir -r requirements.txt
