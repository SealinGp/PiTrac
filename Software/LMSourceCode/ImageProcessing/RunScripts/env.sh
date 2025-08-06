#!/bin/bash
# Usage: source .env [master|slave] [slave_ip]
# Default: source .env master 192.168.31.126

MODE=${1:-master}
SLAVE_IP=${2:-192.168.31.126}

export PITRAC_ROOT=/root/Dev/PiTrac/Software/LMSourceCode
export PITRAC_WEBSERVER_SHARE_DIR="/home/golf/share/LM_Shares/WebShare"
export PITRAC_BASE_IMAGE_LOGGING_DIR="/home/golf/share/LM_Shares/Images"

if [ "$MODE" = "master" ]; then
    export PITRAC_MSG_BROKER_FULL_ADDRESS="tcp://${SLAVE_IP}:61616"
    echo "配置为Master模式 - ActiveMQ地址: tcp://${SLAVE_IP}:61616"
elif [ "$MODE" = "slave" ]; then
    export PITRAC_MSG_BROKER_FULL_ADDRESS="tcp://localhost:61616"
    echo "配置为Slave模式 - ActiveMQ地址: tcp://localhost:61616"
else
    echo "错误: 模式必须是 'master' 或 'slave'"
    echo "用法: source .env [master|slave] [slave_ip]"
    return 1
fi
