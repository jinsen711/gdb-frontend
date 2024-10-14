import os

HOST = "10.0.0.99" # 部署服务器 IP(需修改)
DOCKER_HOST = "0.0.0.0" # 在 docker 中运行时的 IP(不用修改)
PORT = 8001 # 访问端口，需要和 docker-compose.yml 中的映射端口一致(看自己需求)
GDB_HOST = "127.0.0.1" # (不用修改)
GDB_PORT = 5550 # gdb-frontend 初始端口，每次启动 gdb-frontend 都会自动加 1(看自己需求，可改可不改)
GDB_PORT_MAX = 5650 # 最大端口 gdb-frontend 端口范围(看自己需求，可改可不改)
GDB_FRONTEND_PATH = os.path.abspath('../src/run.py') # gdb-frontend 路径(不用修改)

def init():
    global GDB_FRONTEND_PATH
    global HOST
    global PORT
    global GDB_HOST
    global GDB_PORT
    global DOCKER_HOST
    global GDB_PORT_MAX