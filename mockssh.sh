#!/bin/bash

APP_NAME="Mockssh"
PID_FILE="/tmp/${APP_NAME}.pid"
LOG_FILE="/tmp/${APP_NAME}.log"
PYTHON_SCRIPT="$(pwd)/mockssh.py"

check_pid() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

start() {
    echo "Starting $APP_NAME..."
    if check_pid; then
        echo "$APP_NAME is already running with PID $(cat $PID_FILE)"
        return 1
    fi
    
    # 启动 Python 脚本
    python3 $PYTHON_SCRIPT >> $LOG_FILE 2>&1 &
    PID=$!
    echo $PID > $PID_FILE
    echo "$APP_NAME started with PID $PID"
    echo "Logs are being written to $LOG_FILE"
}

stop() {
    echo "Stopping $APP_NAME..."
    if check_pid; then
        PID=$(cat $PID_FILE)
        kill $PID
        rm -f $PID_FILE
        echo "$APP_NAME stopped"
    else
        echo "$APP_NAME is not running"
        return 1
    fi
}

restart() {
    echo "Restarting $APP_NAME..."
    stop
    sleep 2
    start
}

status() {
    if check_pid; then
        echo "$APP_NAME is running with PID $(cat $PID_FILE)"
        echo "Log file: $LOG_FILE"
    else
        echo "$APP_NAME is not running"
    fi
}

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

exit 0
