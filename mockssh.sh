#!/bin/bash
# 配置
SCRIPT_PATH="mockssh.py"  # Python 脚本路径
LOG_FILE="/tmp/mockssh.log"                # 日志文件路径

get_pid() {
    # 使用 ps 查找脚本的 PID
    echo $(ps aux | grep "$SCRIPT_PATH" | grep -v "grep" | awk '{print $2}')
}

start() {
    # 检查脚本是否已经运行
    PID=$(get_pid)
    if [ -n "$PID" ]; then
        echo "Script is already running with PID $PID."
        exit 1
    fi
    
    # 启动脚本
    echo "Starting script..."
    nohup python3 -u "$SCRIPT_PATH" > /dev/null 2>&1 < /dev/null &
    echo "Script started with PID $!."
    echo "Your can check the log with: tail -f mockssh.log"
    sleep 1  # 给程序一点时间来启动
}

stop() {
    # 获取运行中的脚本 PID
    PID=$(get_pid)
    if [ -z "$PID" ]; then
        echo "Script is not running."
        exit 1
    fi

    # 停止脚本
    echo "Stopping script with PID $PID..."
    kill "$PID"
    echo "Script stopped."
}

restart() {
    stop
    sleep 1
    start
}

status() {
    # 检查脚本状态
    PID=$(get_pid)
    if [ -n "$PID" ]; then
        echo "Script is running with PID $PID."
    else
        echo "Script is not running."
    fi
}

# 检查命令
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac