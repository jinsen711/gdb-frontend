# 1 运行

    ./run.sh

# 2 停止

    ./stop.sh

# 3 接口相关

## 3.1 创建 gdb-frontend 实例

    10.0.0.99:8000/create

    返回值
    access_url: 访问实例地址
    delete_url: 删除实例地址
    user_id: 区分用户
    success：判断是否创建成功，true 为成功 false 为失败

## 3.2 创建 gdb-frontend 实例时可预先传入要连接 gdbserver 的 host 和 port

    10.0.0.99:8000/create?chost=127.0.0.1&cport=1234

    返回值
    access_url: 访问实例地址
    delete_url: 删除实例地址
    user_id: 区分用户
    success：判断是否创建成功，true 为成功 false 为失败

## 3.3 访问 gdb-frontend 实例

    输入 access_url 即可访问

    access_url 的组成：config.HOST:config.PORT?user_id=XXXXXXXXXXXXX

## 3.4 删除 gdb-frontend 实例

    10.0.0.99:8000/delete?user_id=XXXXXXXXXXXXX

    返回值
    success：判断是否删除成功，true 为成功 false 为失败

## 3.5 输出当前正在运行的 gdb-frontend 实例信息

    10.0.0.99:8000/list

    返回值
    instances: gdb-frontend 实例列表
    success：判断是否删除成功，true 为成功 false 为失败

## 3.6 删除所有 gdb-frontend 实例

    10.0.0.99:8000/deleteall

    返回值
    success：判断是否删除成功，true 为成功 false 为失败

# 4 使用案例

    选择自己要添加的二进制文件, 例如 hello.out
    使用 gdbserver 创建远程调试, gdbserver 10.0.0.99:8001 ./hello.out
    浏览器 访问 10.0.0.99:8000/create?chost=10.0.0.99&cport=8001
    返回值中的 access_url 复制到浏览器地址栏中, 即可进入 gdb-frontend 调试界面.

# 注意

    当前配置中,最多只能同时运行 100 个 gdb-frontend 实例.如需修改,在 config.py 中修改 GDB_PORT 和 GDB_PORT_MAX 即可.
