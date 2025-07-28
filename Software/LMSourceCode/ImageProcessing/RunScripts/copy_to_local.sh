#!/bin/bash
# 将测试脚本复制到本地目录进行测试

MASTER_LOCAL_DIR="/home/pi/pitrac_test"
SLAVE_LOCAL_DIR="/home/pi/pitrac_test"

echo "📁 创建MasterPi5本地测试目录..."
mkdir -p $MASTER_LOCAL_DIR

echo "📋 复制MasterPi5测试脚本到本地..."
cp test_pin22_trigger.py $MASTER_LOCAL_DIR/
cp test_pin22_simple.py $MASTER_LOCAL_DIR/

echo "📋 复制SlavePi5测试脚本到本地..."
cp test_slave_external_trigger.py $MASTER_LOCAL_DIR/

echo "📋 复制说明文档..."
cp 外部触发测试说明.md $MASTER_LOCAL_DIR/

echo "✅ 脚本已复制到 $MASTER_LOCAL_DIR"
echo ""
echo "🎯 使用步骤:"
echo "1️⃣  在MasterPi5上:"
echo "   cd $MASTER_LOCAL_DIR"
echo "   python3 test_pin22_trigger.py"
echo ""
echo "2️⃣  将SlavePi5的脚本也复制到本地:"
echo "   scp $MASTER_LOCAL_DIR/test_slave_external_trigger.py pi@192.168.31.126:/home/pi/"
echo ""
echo "3️⃣  在SlavePi5上:"
echo "   cd /home/pi"
echo "   sudo python3 test_slave_external_trigger.py"