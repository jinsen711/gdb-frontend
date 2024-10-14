# 使用官方的 Ubuntu 22.04 镜像作为基础
FROM hub.sr.inc/share/ubuntu:22.04

# 设置时区
ARG TZ="Asia/Shanghai"
RUN ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && echo ${TZ} > /etc/timezone

# 设置工作目录
WORKDIR /data/gdb-frontend/web

# 源
ARG UBUNTU_MIRROR=mirrors.tuna.tsinghua.edu.cn
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 python、tmux 和 gdb-multiarch，清理缓存以减小镜像体积
RUN sed -i "s/archive.ubuntu.com/${UBUNTU_MIRROR}/g" /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y python3 python3-pip tmux gdb-multiarch && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip3 install -i ${PIP_INDEX_URL} aiohttp aiohttp_jinja2 jinja2

# 设置容器启动命令
ENTRYPOINT ["python3", "/data/gdb-frontend/web/main.py"]
