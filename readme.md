# 1 运行

    ./run.sh

# 2 停止

    ./stop.sh

# 3 接口相关

    config.HOST 和 config.PORT 是 ./web/config 中的配置.

## 3.1 创建 gdb-frontend 实例

    config.HOST:config.PORT/create

    返回值
    access_url: 访问实例地址
    delete_url: 删除实例地址
    user_id: 区分用户
    success：判断是否创建成功，true 为成功 false 为失败

## 3.2 创建 gdb-frontend 实例时可预先传入要连接 gdbserver 的 host 和 port

    config.HOST:config.PORT/create?chost=127.0.0.1&cport=1234

    返回值
    access_url: 访问实例地址
    delete_url: 删除实例地址
    user_id: 区分用户
    success：判断是否创建成功，true 为成功 false 为失败

## 3.3 访问 gdb-frontend 实例

    输入 access_url 即可访问

    access_url 的组成：config.HOST:config.PORT?user_id=XXXXXXXXXXXXX

## 3.4 删除 gdb-frontend 实例

    config.HOST:config.PORT/delete?user_id=XXXXXXXXXXXXX

    返回值
    success：判断是否删除成功，true 为成功 false 为失败

## 3.5 输出当前正在运行的 gdb-frontend 实例信息

    config.HOST:config.PORT/list

    返回值
    instances: gdb-frontend 实例列表
    success：判断是否删除成功，true 为成功 false 为失败

## 3.6 删除所有 gdb-frontend 实例

    config.HOST:config.PORT/deleteall

    返回值
    success：判断是否删除成功，true 为成功 false 为失败

# 注意

    当前配置中,最多只能同时运行 100 个 gdb-frontend 实例.如需修改,在 config.py 中修改 GDB_PORT 和 GDB_PORT_MAX 即可.
