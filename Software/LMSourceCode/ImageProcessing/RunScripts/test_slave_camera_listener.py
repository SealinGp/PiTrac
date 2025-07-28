#!/usr/bin/env python3
"""
SlavePi5 相机触发监听脚本
功能：监听来自MasterPi5的触发信号，触发时立即拍照
根据接线图，SlavePi5通过Connect Board接收来自MasterPi5 Pin22的触发信号
作者：Claude Code Assistant
"""

import time
import threading
from datetime import datetime
from pathlib import Path
from gpiozero import Button
from picamera2 import Picamera2
import signal
import sys

class SlaveCameraListener:
    def __init__(self):
        # 根据接线图，Slave Pi通过Connect Board的XTrg信号接收触发
        # 这里需要根据实际的Slave Pi GPIO引脚来设置
        # 从接线图看，应该连接到Slave Camera的Xtrg引脚
        # 假设这个信号最终连接到Slave Pi的某个GPIO引脚，需要确认具体引脚号
        # 暂时使用GPIO 18作为触发输入引脚（请根据实际连接调整）
        self.trigger_input = Button(18, pull_up=True)
        
        # 相机设置
        self.camera = Picamera2()
        self.camera_ready = False
        
        # 图像保存路径
        self.save_dir = Path("/mnt/projects/PiTrac/test_images")
        self.save_dir.mkdir(exist_ok=True)
        
        # 运行状态
        self.running = True
        
        # 绑定触发事件
        self.trigger_input.when_pressed = self.on_trigger_received
        
        print("🎯 Slave Pi 相机监听器初始化完成")
        print(f"📍 监听GPIO引脚: {18}")
        print(f"💾 图像保存目录: {self.save_dir}")
    
    def setup_camera(self):
        """初始化Slave Pi相机"""
        try:
            # 配置相机 - 与Master Pi相同配置
            camera_config = self.camera.create_still_configuration(
                main={"size": (1920, 1080)},
                lores={"size": (640, 480)},
                display="lores"
            )
            self.camera.configure(camera_config)
            self.camera.start()
            
            # 相机预热
            time.sleep(2)
            self.camera_ready = True
            
            print("✅ Slave Pi 相机初始化完成")
            return True
            
        except Exception as e:
            print(f"❌ Slave Pi 相机初始化失败: {e}")
            return False
    
    def on_trigger_received(self):
        """收到触发信号时的回调函数"""
        if not self.camera_ready:
            print("⚠️  相机未就绪，忽略触发信号")
            return
        
        try:
            # 记录收到触发的时间
            trigger_received_time = time.time()
            print(f"📡 收到触发信号 - 时间戳: {trigger_received_time:.6f}")
            
            # 立即拍照
            capture_time = time.time()
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            
            # 生成测试ID（基于时间戳）
            test_id = f"{int(capture_time)}"
            slave_image_path = self.save_dir / f"slave_{test_id}_{timestamp_str}.jpg"
            
            # 拍照
            self.camera.capture_file(str(slave_image_path))
            capture_end_time = time.time()
            
            print(f"📸 Slave Pi 拍照完成: {slave_image_path.name}")
            print(f"⏱️  拍照耗时: {(capture_end_time - capture_time)*1000:.2f}ms")
            
            # 将结果写入文件，供Master Pi读取
            self.write_result_file(test_id, capture_end_time, slave_image_path.name)
            
        except Exception as e:
            print(f"❌ Slave Pi 拍照失败: {e}")
    
    def write_result_file(self, test_id, capture_time, image_name):
        """写入结果文件供Master Pi读取"""
        try:
            # 找到对应的测试ID文件名
            # Master Pi会寻找格式为 slave_result_{test_id}_xxx.txt 的文件
            # 这里使用简化的test_id匹配
            result_files = list(self.save_dir.glob("slave_result_*.txt"))
            
            # 使用时间戳作为匹配依据，找到最近的测试ID
            current_timestamp = int(capture_time)
            
            # 查找最近5秒内的Master测试请求
            for i in range(5):  # 检查最近5秒
                test_timestamp = current_timestamp - i
                for suffix in ["_001", "_002", "_003", "_004", "_005"]:  # 可能的测试序号
                    expected_test_id = f"{test_timestamp}{suffix}"
                    result_file = self.save_dir / f"slave_result_{expected_test_id}.txt"
                    
                    # 如果找到对应的结果文件请求，就写入
                    # 实际上这里应该是Master Pi创建空文件，Slave Pi填充内容
                    # 为了简化，我们创建结果文件
                    if not result_file.exists():
                        with open(result_file, 'w') as f:
                            f.write(f"{capture_time:.6f},{image_name}")
                        print(f"📝 结果文件已创建: {result_file.name}")
                        return
            
            # 如果没找到对应的测试ID，创建一个通用的结果文件
            fallback_result_file = self.save_dir / f"slave_result_{current_timestamp}_fallback.txt"
            with open(fallback_result_file, 'w') as f:
                f.write(f"{capture_time:.6f},{image_name}")
            print(f"📝 创建备用结果文件: {fallback_result_file.name}")
            
        except Exception as e:
            print(f"❌ 写入结果文件失败: {e}")
    
    def run_listener(self):
        """运行监听器"""
        print("🎧 开始监听触发信号...")
        print("=" * 50)
        
        if not self.setup_camera():
            return False
        
        print("✅ Slave Pi 监听器已就绪")
        print("⏳ 等待来自Master Pi的触发信号...")
        print("💡 按Ctrl+C停止监听")
        
        try:
            while self.running:
                time.sleep(0.1)  # 防止CPU占用过高
                
        except KeyboardInterrupt:
            print("\n⏹️  监听被用户中断")
            return True
        except Exception as e:
            print(f"❌ 监听过程中出错: {e}")
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            self.running = False
            
            if hasattr(self, 'camera') and self.camera_ready:
                self.camera.stop()
                self.camera.close()
            
            if hasattr(self, 'trigger_input'):
                self.trigger_input.close()
            
            print("🧹 Slave Pi 资源清理完成")
        except Exception as e:
            print(f"⚠️  清理资源时出错: {e}")

def signal_handler(sig, frame):
    """信号处理器"""
    print("\n🛑 收到退出信号，正在清理...")
    global listener
    if 'listener' in globals():
        listener.cleanup()
    sys.exit(0)

def main():
    global listener
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    listener = SlaveCameraListener()
    
    try:
        # 运行监听器
        listener.run_listener()
        
    except Exception as e:
        print(f"❌ 监听器运行出错: {e}")
    finally:
        listener.cleanup()

if __name__ == "__main__":
    main()