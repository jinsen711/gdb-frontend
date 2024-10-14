#!/bin/bash

# 定义要检查的镜像名称和标签
WORK_DIR=$(pwd)
IMAGE_NAME="hub.sr.inc/gdb_frontend"
IMAGE_TAG="1.2"
IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
IMAGE_FILE="${WORK_DIR}/dependence/gdb_frontend.docker" # Docker 镜像的 tar 文件路径

# 检查是否传递了参数
if [ $# -eq 1 ]; then
    SERVER_IP=$1 # 使用传递的参数作为服务器 IP
    echo "使用传递的 IP 地址: ${SERVER_IP}"
else
    # 如果没有传递参数，则自动获取服务器 IP
    SERVER_IP=$(hostname -I | awk '{print $1}') # 使用 hostname -I 获取 IP
    echo "自动获取的服务器 IP 地址: ${SERVER_IP}"
fi

# 替换 ./web/config 中的 SERVER_HOST
CONFIG_FILE="${WORK_DIR}/web/config.py"
if [ -f "$CONFIG_FILE" ]; then
    sed -i "s/SERVER_HOST = .*/SERVER_HOST = \"${SERVER_IP}\"/g" "$CONFIG_FILE"
    echo "已将 HOST 设置为 ${SERVER_IP}."
else
    echo "Error: 配置文件 ${CONFIG_FILE} 未找到."
    exit 1
fi

# 判断是否有 IMAGE_FILE 文件
if [ ! -f "$IMAGE_FILE" ]; then
    cat "${WORK_DIR}/dependence/deploy.tar.gz.part"* >"${WORK_DIR}/dependence/deploy.tar.gz"
    tar -zxvf "${WORK_DIR}/dependence/deploy.tar.gz" -C "${WORK_DIR}/dependence/"
fi

# 检查镜像是否存在
if ! sudo docker images | grep -q "gdb_frontend\s*1.2"; then
    # 检查镜像文件是否存在
    if [ -f "$IMAGE_FILE" ]; then
        sudo docker load -i "$IMAGE_FILE"
        echo "Docker 镜像 ${IMAGE} 安装成功."
    else
        echo "Error: Docker image file ${IMAGE_FILE} not found."
        exit 1
    fi
else
    echo "Docker 镜像 ${IMAGE} 已存在."
fi

# 检查 gdb_frontend 容器是否在运行
sudo docker compose up -d

echo "访问 http://${SERVER_IP}:8081/create?chost=XXXX&cport=XX 来创建 gdb-frontend 实例."
echo "访问 http://${SERVER_IP}:8081/list 查看已创建的实例."
echo "访问 http://${SERVER_IP}:8081/delete?user_id=XXXXXXXXX 来删除 gdb-frontend 实例."
