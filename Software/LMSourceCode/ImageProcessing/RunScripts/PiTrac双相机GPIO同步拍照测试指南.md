# PiTrac双相机GPIO同步拍照测试指南

## 概述

本文档提供了PiTrac系统中双相机GPIO同步拍照功能的详细测试指南。该系统使用Master Pi5通过GPIO Pin 22控制Connect Board，进而触发Slave Pi5的相机进行同步拍照。

## 硬件连接确认

### 连接图示
根据项目文档和PCB设计，正确的硬件连接如下：

```
Master Pi5 Pin 22 (BCM GPIO25) → Connect Board Shr引脚 (Sys1_Conn1 Pin 2)
                                        ↓
                              Connect Board内部处理
                                        ↓
Connect Board XTrg引脚 (Sys2_Conn1 Pin 2) → Slave Pi5相机模块 XTR引脚
```

### 引脚功能说明
- **Shr引脚**: 快门触发信号输入，控制相机外部快门 (XTRG)
- **XTrg引脚**: 快门触发信号输出，连接到从相机的外部触发引脚
- **Pin 22**: Master Pi5的BCM GPIO25，用于输出触发脉冲

## 同步机制原理

### 触发流程
1. Master Pi5检测到球的运动
2. 调用`SendExternalTrigger()`函数
3. GPIO25 (Pin 22)输出高电平脉冲信号到Connect Board的Shr引脚
4. 同时通过SPI发送LED闪光灯脉冲序列
5. Connect Board将Shr信号处理后输出到XTrg引脚
6. Slave Pi5相机接收XTrg触发信号立即拍照
7. GPIO25恢复低电平，完成一次同步拍照

### 关键代码位置
- **GPIO控制**: `pulse_strobe.cpp` - `SendExternalTrigger()`函数
- **运动检测触发**: `motion_detect_stage.cpp`
- **相机配置**: `libcamera_interface.cpp`

## 测试准备

### 1. 环境变量设置
```bash
# 必需的环境变量
export PITRAC_ROOT="/home/pi/PiTrac"
export PITRAC_MSG_BROKER_FULL_ADDRESS="tcp://localhost:61616"
export PITRAC_WEBSERVER_SHARE_DIR="/tmp/pitrac_share"
export PITRAC_BASE_IMAGE_LOGGING_DIR="/tmp/pitrac_logs"

# 创建必要目录
mkdir -p /tmp/pitrac_share
mkdir -p /tmp/pitrac_logs
```

### 2. 权限设置
```bash
# 确保GPIO访问权限
sudo usermod -a -G gpio $USER
sudo usermod -a -G spi $USER

# 重新登录以生效权限
```

### 3. 相机模块检查
```bash
# 检查相机模块是否被识别
libcamera-hello --list-cameras

# 应该看到两个相机设备
```

## 测试方法
### 方法2: 手动GPIO触发测试

#### 使用libcamera直接测试
```bash
# 在Slave Pi5上，启动相机等待外部触发
libcamera-still --timeout 0 --output /tmp/slave_triggered_image.jpg &

# 在Master Pi5上，手动触发GPIO进行测试
echo 25 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio25/direction
echo 1 > /sys/class/gpio/gpio25/value
sleep 0.1
echo 0 > /sys/class/gpio/gpio25/value

# 清理GPIO
echo 25 > /sys/class/gpio/unexport
```

#### 使用脉冲测试脚本
```bash
# 运行脉冲测试（如果存在）
./runPulseTest.sh
```

## 验证同步效果

### 1. 检查图像时间戳
```bash
# 查看两张照片的拍摄时间戳
stat /tmp/cam1_image.jpg | grep Modify
stat /tmp/cam2_image.jpg | grep Modify

# 时间戳差异应该在几毫秒内
```

### 2. 检查GPIO状态
```bash
# 实时监控GPIO25状态（需要在触发时运行）
watch -n 0.1 "gpio readall | grep -E '(GPIO|25)'"
```

### 3. 检查日志输出
```bash
# 查看PiTrac运行日志
tail -f /tmp/pitrac_logs/pitrac.log

# 应该看到类似输出:
# [INFO] ---> SendExternalTrigger
# [INFO] Motion detected, triggering external camera
```

### 4. 验证相机触发模式
```bash
# 在Slave Pi上检查
cat /sys/module/imx296/parameters/trigger_mode
# 0 = 内部触发, 1 = 外部触发
```


### 方法1: 分步手动测试

#### 步骤1: 设置Master Pi5（相机1）
```bash
cd RunScripts

# 确保环境变量已设置
source runPiTracCommon.sh

# 运行相机1，初始化GPIO控制系统
./runCam1.sh
```

#### 步骤2: 设置Slave Pi5（相机2）为外部触发模式
```bash
# 在Slave Pi5上执行
cd ../CameraTools

# 设置相机2为外部触发模式
sudo ./setCameraTriggerExternal.sh

# 验证触发模式设置
cat /sys/module/imx296/parameters/trigger_mode
# 应该显示: 1 (外部触发模式)

# 运行相机2，等待外部触发
cd ../RunScripts
./runCam2.sh
```

#### 步骤3: 测试同步功能
```bash
# 使用运动检测测试完整同步
./runAutomatedTesting.sh
```


## 预期结果

### 成功指标
- ✅ 两个相机都能正常拍照
- ✅ 图像时间戳差异 < 10ms
- ✅ Slave相机在外部触发模式下能被成功触发
- ✅ GPIO25能正确输出脉冲信号
- ✅ 日志显示"SendExternalTrigger"消息
- ✅ 运动检测能自动触发同步拍照

### 图像质量检查
- **相机1 (Master)**: 分辨率1456x1088, 正常色彩
- **相机2 (Slave)**: 分辨率1456x1088, 红外成像
- 两张图像应清晰无模糊
- 曝光时间和增益设置合理

## 故障排除

### 常见问题

#### 1. GPIO权限问题
```bash
# 解决方案
sudo usermod -a -G gpio $USER
# 重新登录
```

#### 2. 相机无法触发
```bash
# 检查触发模式
cat /sys/module/imx296/parameters/trigger_mode

# 重新设置外部触发
sudo ./setCameraTriggerExternal.sh
```

#### 3. 时间同步问题
```bash
# 同步系统时间
sudo ntpdate -s time.nist.gov
```

#### 4. 连接问题检查
```bash
# 检查Connect Board连接
# 用万用表测量:
# - Master Pi Pin 22 到 Connect Board Shr引脚的导通性
# - Connect Board XTrg引脚 到 Slave相机XTR引脚的导通性
```

### 调试命令

#### GPIO状态监控
```bash
# 监控GPIO25状态变化
gpionotify 25
```

#### 实时日志监控
```bash
# 监控多个日志文件
tail -f /tmp/pitrac_logs/* /var/log/syslog | grep -i camera
```

#### 系统资源监控
```bash
# 监控CPU和内存使用
htop

# 监控相机进程
ps aux | grep -E "(libcamera|pitrac)"
```

## 高级测试

### 性能测试
```bash
# 测试连续触发性能
for i in {1..10}; do
    echo "触发测试 $i"
    # 执行触发命令
    ./runPulseTest.sh
    sleep 1
done
```

### 精确时序测试
```bash
# 使用高精度时间戳记录
date +%s.%N > /tmp/trigger_time.log
# 执行触发
# 记录完成时间
date +%s.%N >> /tmp/trigger_time.log
```

## 配置文件参考

### 相关配置参数 (golf_sim_config.json)
```json
{
    "strobing": {
        "kStrobePulseVectorDriver": ["0.175", "0.7", "1.4", ...],
        "kBaudRateForFastPulses": "115200"
    },
    "cameras": {
        "kNumInitialCamera2PrimingPulses": "12",
        "kPauseBeforeCamera2PrimingPulsesMs": "2000"
    }
}
```

## 维护建议

1. **定期校准**: 每月运行一次完整的同步测试
2. **连接检查**: 定期检查硬件连接的稳定性
3. **日志清理**: 定期清理测试日志文件
4. **备份配置**: 保存工作正常时的配置文件

## 联系支持

如果遇到无法解决的问题，请：
1. 收集完整的日志文件
2. 记录硬件连接情况
3. 提供测试结果截图
4. 在PiTrac Discord社区寻求帮助

---
*文档版本: v1.0*
*最后更新: 2025-01*
*适用版本: PiTrac v0.1+*
