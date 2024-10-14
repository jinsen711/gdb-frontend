# 1 制作 docker 镜像

## 1.1 制作环境镜像(需要映射代码文件)

    sudo docker build -t hub.sr.inc/firmware/gdb_frontend:1.2 .

# 2 运行前准备

    1. 修改 ./web/config.py 中的配置.
        config.HOST: 服务器地址，这个必须修改，不能用 0.0.0.0 代替.
    2. 开放 8001 端口
        sudo ufw allow 8001
    3(可选). 自定义端口. 需要修改服务器向外暴露的端口以及 ./web/config.py 和 ./docker-compose.yml 中的配置.
        sudo ufw allow xx，这个 xx 是自定义的端口.
        config.py: 修改 PORT 为 xx.
        docker-compose.yml: 修改 ports: xx:xx.

# 3 运行容器

    sudo docker compose up -d

# 4 接口相关

    config.HOST 和 config.PORT 是 ./web/config 中的配置.

## 4.1 创建 gdb-frontend 实例

    config.HOST:config.PORT/create

    返回值
    access_url: 访问实例地址
    delete_url: 删除实例地址
    user_id: 区分用户
    success：判断是否创建成功，true 为成功 false 为失败

## 4.2 创建 gdb-frontend 实例时可预先传入要连接 gdbserver 的 host 和 port

    config.HOST:config.PORT/create?chost=127.0.0.1&cport=1234

    返回值
    access_url: 访问实例地址
    delete_url: 删除实例地址
    user_id: 区分用户
    success：判断是否创建成功，true 为成功 false 为失败

## 4.3 访问 gdb-frontend 实例

    输入 access_url 即可访问

    access_url 的组成：config.HOST:config.PORT?user_id=XXXXXXXXXXXXX

## 4.4 删除 gdb-frontend 实例

    config.HOST:config.PORT/delete?user_id=XXXXXXXXXXXXX

    返回值
    success：判断是否删除成功，true 为成功 false 为失败

## 4.5 输出当前正在运行的 gdb-frontend 实例信息

    config.HOST:config.PORT/list

    返回值
    instances: gdb-frontend 实例列表
    success：判断是否删除成功，true 为成功 false 为失败

## 4.6 删除所有 gdb-frontend 实例

    config.HOST:config.PORT/deleteall

    返回值
    success：判断是否删除成功，true 为成功 false 为失败

# 注意

    当前配置中,最多只能同时运行 100 个 gdb-frontend 实例.如需修改,在 config.py 中修改 GDB_PORT 和 GDB_PORT_MAX 即可.
