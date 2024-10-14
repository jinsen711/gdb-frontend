import os
import signal
import subprocess
import asyncio
import aiohttp
import aiohttp.web
import uuid
from threading import Lock

# 模板
import aiohttp_jinja2
import jinja2

# 配置文件
import config

# 初始化 aiohttp 应用
app = aiohttp.web.Application()

# 设置 Jinja2 模板环境
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("./templates"))

# 初始端口
gf_ports = set()  # 使用集合来跟踪已使用的端口
# 存储会话 ID 到实例映射
user_id_map = {}
# 线程锁，用于保护对全局变量的访问
lock = Lock()


async def is_port_in_use(port):
    """检查端口是否被占用"""
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.close()
        await writer.wait_closed()
        return True
    except ConnectionRefusedError:
        return False


async def find_available_port(start_port, max_port):
    """查找一个未被使用的端口"""
    cur_port = start_port
    while cur_port in gf_ports or await is_port_in_use(cur_port):
        cur_port += 1
        if cur_port > max_port:
            return None
    return cur_port


async def create_gdb_instance(connect_host, connect_port):
    """启动一个新的gdb-frontend实例并返回实例地址和进程"""
    try:
        # 查找未使用的端口
        cur_port = await find_available_port(config.GDB_PORT, config.GDB_PORT_MAX)
        if cur_port is None:
            return None, None, None
        # 启动 gdb-frontend 实例
        process = subprocess.Popen(
            [
                "python3",
                config.GDB_FRONTEND_PATH,
                f"--host={config.GDB_HOST}",
                f"--port={cur_port}",
                f"--chost={connect_host}",
                f"--cport={connect_port}",
                "--listen=0.0.0.0",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # 等待一段时间，让 gdb-frontend 启动
        await asyncio.sleep(0.8)
        # 返回
        return f"http://{config.GDB_HOST}:{cur_port}", process, cur_port
    except Exception as e:
        return None, None, None


# 定义路由处理函数
async def create_instance(request):
    global gf_ports
    try:
        with lock:
            # 生成 user_id
            user_id = str(uuid.uuid4())
            # 得到 gdbserver的 host 和 port
            connect_host = request.query.get("chost", "127.0.0.1")
            connect_port = request.query.get("cport", 1234)
            # 如果会话ID没有绑定实例，则创建新的实例
            if user_id not in user_id_map:
                instance_url, cur_process, cur_port = await create_gdb_instance(
                    connect_host, connect_port
                )
                if instance_url:
                    user_id_map[user_id] = {
                        "instance_url": instance_url,
                        "process": cur_process,
                        "port": cur_port,
                    }
                    # 记录已使用的端口
                    gf_ports.add(cur_port)
                else:
                    return aiohttp.web.json_response(
                        {"error": "Failed to create gdb-frontend.", "success": False},
                        status=400,
                    )
            else:
                return aiohttp.web.json_response(
                    {"error": "This user_id already exists.", "success": False},
                    status=400,
                )

            # 返回
            return aiohttp.web.json_response(
                {
                    "user_id": user_id,
                    "access_url": f"http://{config.HOST}:{config.PORT}?user_id={user_id}",
                    "delete_url": f"http://{config.HOST}:{config.PORT}/delete?user_id={user_id}",
                    "success": True,
                },
                status=200,
            )
    except Exception as e:
        return aiohttp.web.json_response(
            {"error": str(e), "success": False}, status=500
        )


async def delete_instance(request):
    global gf_ports, user_id_map
    try:
        with lock:
            # 获取 user_id
            user_id = request.query.get("user_id")
            # 判断 user_id 是否存在
            if user_id and user_id in user_id_map:
                process = user_id_map[user_id]["process"]
                if process.poll() is None:  # 检查进程是否还在运行
                    os.kill(process.pid, signal.SIGINT)
                # 清除端口
                gf_ports.remove(user_id_map[user_id]["port"])
                # 清除会话数据
                del user_id_map[user_id]
                return aiohttp.web.json_response(
                    {"message": "Deleted successfully.", "success": True}, status=200
                )
            else:
                return aiohttp.web.json_response(
                    {"error": "No such user_id, deletion failed.", "success": False},
                    status=404,
                )
    except Exception as e:
        return aiohttp.web.json_response(
            {"error": str(e), "success": False}, status=500
        )


async def list_instances(request):
    """列出所有活动的 gdb-frontend 实例"""
    try:
        with lock:
            instances = [
                {
                    "user_id": user_id,
                    "access_url": f"http://{config.HOST}:{config.PORT}?user_id={user_id}",
                    "delete_url": f"http://{config.HOST}:{config.PORT}/delete?user_id={user_id}",
                }
                for user_id, info in user_id_map.items()
            ]
            return aiohttp.web.json_response(
                {"instances": instances, "success": True}, status=200
            )
    except Exception as e:
        return aiohttp.web.json_response(
            {"error": str(e), "success": False}, status=500
        )


async def delete_all_instances(request):
    """删除所有活动的 gdb-frontend 实例"""
    global gf_ports, user_id_map
    try:
        with lock:
            # 删除所有实例
            for user_id, info in list(user_id_map.items()):
                process = info["process"]
                if process.poll() is None:  # 检查进程是否还在运行
                    os.kill(process.pid, signal.SIGINT)
                # 清除端口
                gf_ports.remove(info["port"])
                # 清除会话数据
                del user_id_map[user_id]
            return aiohttp.web.json_response(
                {"message": "All instances deleted successfully.", "success": True},
                status=200,
            )
    except Exception as e:
        return aiohttp.web.json_response(
            {"error": str(e), "success": False}, status=500
        )


# 定义处理根路径的代理逻辑
async def proxy_root_request(request):
    with lock:
        # 判断当前浏览器是否已经有一个 gdb-frontend 实例
        # user_id = request.cookies.get("user_id")
        # if user_id and user_id in user_id_map:
        #     return aiohttp.web.json_response({"error": "You already have an instance running.", "success": False}, status=400)

        # 获取 user_id
        user_id = request.query.get("user_id")

        if not user_id:
            return aiohttp_jinja2.render_template(
                "error.html",
                request,
                {
                    "return_url": f"http://{config.HOST}:{config.PORT}/?user_id={user_id}"
                },
                status=403,
            )

        # 判断该 user_id 是否存在
        if user_id not in user_id_map:
            return aiohttp_jinja2.render_template(
                "error.html",
                request,
                {
                    "return_url": f"http://{config.HOST}:{config.PORT}/?user_id={user_id}"
                },
                status=403,
            )

        # 选择实例
        selected_instance = user_id_map[user_id]["instance_url"]

    # 构建目标URL
    target_url = f"{selected_instance}/"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=target_url,
                headers={
                    key: value
                    for (key, value) in request.headers.items()
                    if key.lower() != "host"
                },
                params=request.query,  # 使用获取的查询参数
                data=await request.read(),  # 读取请求体
                cookies=request.cookies,
                timeout=aiohttp.ClientTimeout(total=5),  # 设置超时时间
                allow_redirects=False,
            ) as resp:

                # 创建响应对象
                excluded_headers = [
                    "content-encoding",
                    "content-length",
                    "transfer-encoding",
                    "connection",
                ]
                headers = [
                    (name, value)
                    for (name, value) in resp.headers.items()
                    if name.lower() not in excluded_headers
                ]

                # 创建响应对象并设置 user_id 作为 Cookie
                response = aiohttp.web.Response(
                    body=await resp.read(), status=resp.status, headers=headers
                )
                response.set_cookie("user_id", user_id)

                return response
    except aiohttp.ClientError as e:
        return aiohttp.web.json_response(
            {"error": "Unknown error", "success": False}, status=502
        )


async def handle_websocket(request):
    """处理 WebSocket 连接"""
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    user_id = request.cookies.get("user_id")
    if not user_id or user_id not in user_id_map:
        await ws.send_json({"error": "Invalid user_id.", "success": False})
        await ws.close()
        return ws

    # 获取 gdb-frontend 实际端口
    instance_port = user_id_map[user_id]["port"]
    instance_ws_url = f"ws://{config.GDB_HOST}:{instance_port}/debug-server"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                instance_ws_url, timeout=aiohttp.ClientTimeout(total=10)
            ) as ws_target:

                async def forward_messages(ws_src, ws_dst):
                    """转发消息"""
                    async for msg in ws_src:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await ws_dst.send_str(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            await ws_dst.send_bytes(msg.data)
                        elif msg.type in {
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.CLOSING,
                            aiohttp.WSMsgType.ERROR,
                        }:
                            break

                async def receive_messages(ws_src):
                    """接收消息"""
                    while True:
                        try:
                            msg = await ws_src.receive()
                            if msg.type in {
                                aiohttp.WSMsgType.CLOSE,
                                aiohttp.WSMsgType.CLOSING,
                                aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR,
                            }:
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                await ws.send_str(msg.data)
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                await ws.send_bytes(msg.data)
                        except aiohttp.WSMsgType as e:
                            # 处理消息接收异常
                            break

                # 创建并运行转发任务
                forward_task = asyncio.create_task(forward_messages(ws, ws_target))
                receive_task = asyncio.create_task(receive_messages(ws_target))

                done, pending = await asyncio.wait(
                    [forward_task, receive_task], return_when=asyncio.FIRST_COMPLETED
                )

                # 取消仍在等待的任务
                for task in pending:
                    task.cancel()

                # 等待被取消的任务真正完成
                await asyncio.gather(*pending, return_exceptions=True)

    except aiohttp.ClientError as e:
        await ws.send_json(
            {"error": f"Failed to connect to {instance_ws_url}: {e}", "success": False}
        )
    except Exception as e:
        await ws.send_json(
            {"error": f"An unexpected error occurred: {e}", "success": False}
        )
    finally:
        # 确保所有WebSocket连接都被关闭
        if not ws.closed:
            await ws.close()
        if "ws_target" in locals() and not ws_target.closed:
            await ws_target.close()

    return ws


# 定义处理非根路径的代理逻辑
async def proxy_http_request(request):
    with lock:
        # 获取 user_id
        user_id = request.cookies.get("user_id")

        if not user_id:
            return aiohttp_jinja2.render_template(
                "error.html",
                request,
                {
                    "return_url": f"http://{config.HOST}:{config.PORT}/?user_id={user_id}"
                },
                status=403,
            )

        # 判断该 user_id 是否存在
        if user_id not in user_id_map:
            return aiohttp_jinja2.render_template(
                "error.html",
                request,
                {
                    "return_url": f"http://{config.HOST}:{config.PORT}/?user_id={user_id}"
                },
                status=403,
            )

        # 选择实例
        selected_instance = user_id_map[user_id]["instance_url"]

    # 构建目标URL
    target_url = f"{selected_instance}{request.path}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=target_url,
                headers={
                    key: value
                    for (key, value) in request.headers.items()
                    if key.lower() != "host"
                },
                params=request.query,  # 使用获取的查询参数
                data=await request.read(),  # 读取请求体
                cookies=request.cookies,
                timeout=aiohttp.ClientTimeout(total=5),  # 设置超时时间
                allow_redirects=False,
            ) as resp:

                # 如果该请求未处理，返回错误页面
                if resp.status >= 400:  # 如果响应状态码为 400 以上
                    return aiohttp_jinja2.render_template(
                        "error.html",
                        request,
                        {
                            "return_url": f"http://{config.HOST}:{config.PORT}/?user_id={user_id}"
                        },
                        status=resp.status,
                    )

                # 创建响应对象
                excluded_headers = [
                    "content-encoding",
                    "content-length",
                    "transfer-encoding",
                    "connection",
                ]
                headers = [
                    (name, value)
                    for (name, value) in resp.headers.items()
                    if name.lower() not in excluded_headers
                ]

                # 创建响应对象并设置 user_id 作为 Cookie
                response = aiohttp.web.Response(
                    body=await resp.read(), status=resp.status, headers=headers
                )

                return response
    except aiohttp.ClientError as e:
        return aiohttp_jinja2.render_template(
            "error.html",
            request,
            {"return_url": f"http://{config.HOST}:{config.PORT}/?user_id={user_id}"},
            status=403,
        )


# 添加路由
app.router.add_get("/create", create_instance)
app.router.add_get("/delete", delete_instance)
app.router.add_get("/list", list_instances)
app.router.add_get("/deleteall", delete_all_instances)
app.router.add_get("/", proxy_root_request, name="proxy_root")
app.router.add_get("/debug-server", handle_websocket)
app.router.add_route("*", "/{path:.*}", proxy_http_request)

# 运行 aiohttp 应用
if __name__ == "__main__":
    aiohttp.web.run_app(app, host=config.DOCKER_HOST, port=config.PORT)
