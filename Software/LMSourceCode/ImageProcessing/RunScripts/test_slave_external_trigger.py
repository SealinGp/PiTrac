#!/usr/bin/env python3
"""
SlavePi5外部触发模式测试脚本
功能：设置IMX296相机为外部触发模式，监听硬件触发信号
作者：Claude Code Assistant
"""

import time
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from picamera2 import Picamera2
import signal
import sys

class SlaveExternalTriggerTest:
    def __init__(self):
        # 相机设置
        self.camera = Picamera2()
        self.camera_ready = False

        # 图像保存路径
        self.save_dir = Path("/home/pi/pitrac_test/test_images")
        self.save_dir.mkdir(exist_ok=True)

        # 运行状态
        self.running = True
        self.capture_count = 0

        print("🎯 Slave Pi 外部触发测试器初始化完成")
        print(f"💾 图像保存目录: {self.save_dir}")

    def set_external_trigger_mode(self):
        """设置IMX296为外部触发模式"""
        try:
            print("🔧 设置IMX296为外部触发模式...")

            # 使用PiTrac项目中的脚本设置外部触发
            script_path = "/mnt/projects/PiTrac/Software/LMSourceCode/ImageProcessing/CameraTools/setCameraTriggerExternal.sh"

            if Path(script_path).exists():
                # 执行设置外部触发的脚本
                result = subprocess.run(['sudo', 'bash', script_path],
                                      capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    print("✅ IMX296外部触发模式设置成功")

                    # 验证设置
                    try:
                        with open('/sys/module/imx296/parameters/trigger_mode', 'r') as f:
                            trigger_mode = f.read().strip()
                            if trigger_mode == '1':
                                print("✅ 触发模式验证成功: 外部触发模式已启用")
                                return True
                            else:
                                print(f"⚠️  触发模式验证失败: 当前值为 {trigger_mode}")
                                return False
                    except Exception as e:
                        print(f"⚠️  无法验证触发模式: {e}")
                        return True  # 假设设置成功
                else:
                    print(f"❌ 设置外部触发模式失败: {result.stderr}")
                    return False
            else:
                # 直接设置触发模式
                print("📁 脚本不存在，直接设置触发模式...")
                with open('/sys/module/imx296/parameters/trigger_mode', 'w') as f:
                    f.write('1')
                print("✅ IMX296外部触发模式设置成功")
                return True

        except subprocess.TimeoutExpired:
            print("❌ 设置外部触发模式超时")
            return False
        except PermissionError:
            print("❌ 权限不足，请使用sudo运行此脚本")
            return False
        except Exception as e:
            print(f"❌ 设置外部触发模式失败: {e}")
            return False

    def set_internal_trigger_mode(self):
        """恢复为内部触发模式"""
        try:
            print("🔧 恢复IMX296为内部触发模式...")

            script_path = "/mnt/projects/PiTrac/Software/LMSourceCode/ImageProcessing/CameraTools/setCameraTriggerInternal.sh"

            if Path(script_path).exists():
                result = subprocess.run(['sudo', 'bash', script_path],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("✅ IMX296内部触发模式恢复成功")
                else:
                    print(f"⚠️  恢复内部触发模式失败: {result.stderr}")
            else:
                with open('/sys/module/imx296/parameters/trigger_mode', 'w') as f:
                    f.write('0')
                print("✅ IMX296内部触发模式恢复成功")

        except Exception as e:
            print(f"⚠️  恢复内部触发模式失败: {e}")

    def setup_camera_external_trigger(self):
        """配置相机用于外部触发"""
        try:
            print("📷 配置相机用于外部触发...")

            # 根据PiTrac的配置，为外部触发设置相机
            # 基于libcamera_interface.cpp中的外部触发配置
            camera_config = self.camera.create_still_configuration(
                main={"size": (1456, 1088)},  # 使用PiTrac标准分辨率
                lores={"size": (640, 480)},
                display="lores"
            )

            self.camera.configure(camera_config)

            # 设置相机控制参数（基于PiTrac的libcamera_interface.cpp）
            controls = {
                "ExposureTime": 11111,  # 11.111ms (基于PiTrac设置)
                "AnalogueGain": 3.0,
            }

            self.camera.set_controls(controls)

            # 启动相机但不立即拍照 - 等待外部触发
            self.camera.start()

            # 相机预热
            time.sleep(2)
            self.camera_ready = True

            print("✅ 外部触发相机配置完成")
            print("⏳ 相机等待外部触发信号...")
            return True

        except Exception as e:
            print(f"❌ 外部触发相机配置失败: {e}")
            return False

    def wait_for_external_triggers(self, max_captures=10):
        """等待外部触发并拍照"""
        print(f"🎧 开始监听外部触发 (最多{max_captures}张照片)...")
        print("=" * 60)
        print("💡 在MasterPi5上运行 test_pin22_trigger.py 来发送触发信号")
        print("⏹️  按Ctrl+C停止监听")

        try:
            while self.running and self.capture_count < max_captures:
                try:
                    # 等待外部触发并拍照
                    # 注意：这里使用capture_file，它会等待外部触发信号
                    trigger_start = time.time()

                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    image_path = self.save_dir / f"slave_external_{self.capture_count+1:03d}_{timestamp_str}.jpg"

                    print(f"⏳ 等待第 {self.capture_count+1} 个外部触发信号...")

                    # 使用capture_request方法并设置更长的超时时间
                    # 基于PiTrac的做法，外部触发应该无限等待
                    request = self.camera.capture_request()

                    # 保存图像
                    request.save("main", str(image_path))

                    # 释放请求
                    request.release()

                    capture_time = time.time()
                    self.capture_count += 1

                    print(f"📸 外部触发拍照成功! 照片 #{self.capture_count}")
                    print(f"   📁 文件: {image_path.name}")
                    print(f"   ⏱️  时间戳: {capture_time:.6f}")
                    print(f"   🎯 等待时间: {(capture_time - trigger_start)*1000:.2f}ms")

                    # 写入结果文件供Master Pi读取（如果需要）
                    self.write_capture_result(capture_time, image_path.name)

                except Exception as e:
                    print(f"❌ 外部触发拍照失败: {e}")
                    time.sleep(1)  # 短暂等待后继续

        except KeyboardInterrupt:
            print(f"\n⏹️  外部触发监听被用户中断")
            print(f"📊 总共拍摄了 {self.capture_count} 张照片")
        except Exception as e:
            print(f"❌ 外部触发监听出错: {e}")

    def write_capture_result(self, capture_time, image_name):
        """写入拍照结果"""
        try:
            result_file = self.save_dir / f"slave_external_result_{int(capture_time)}.txt"
            with open(result_file, 'w') as f:
                f.write(f"{capture_time:.6f},{image_name}")
            print(f"   📝 结果文件: {result_file.name}")
        except Exception as e:
            print(f"⚠️  写入结果文件失败: {e}")

    def run_external_trigger_test(self):
        """运行外部触发测试"""
        print("🚀 开始外部触发测试")
        print("=" * 60)

        # 设置外部触发模式
        if not self.set_external_trigger_mode():
            print("❌ 无法设置外部触发模式，测试终止")
            return False

        # 配置相机
        if not self.setup_camera_external_trigger():
            print("❌ 无法配置外部触发相机，测试终止")
            return False

        # 等待外部触发
        self.wait_for_external_triggers(max_captures=10)

        return True

    def cleanup(self):
        """清理资源"""
        try:
            self.running = False

            if hasattr(self, 'camera') and self.camera_ready:
                self.camera.stop()
                self.camera.close()

            # 恢复内部触发模式
            self.set_internal_trigger_mode()

            print("🧹 Slave Pi 外部触发测试器资源清理完成")
        except Exception as e:
            print(f"⚠️  清理资源时出错: {e}")

def signal_handler(sig, frame):
    """信号处理器"""
    print("\n🛑 收到退出信号，正在清理...")
    global test_instance
    if 'test_instance' in globals():
        test_instance.cleanup()
    sys.exit(0)

def main():
    global test_instance

    # 检查是否以sudo运行
    if os.geteuid() != 0:
        print("❌ 此脚本需要sudo权限来设置IMX296触发模式")
        print("💡 请使用: sudo python3 test_slave_external_trigger.py")
        sys.exit(1)

    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    test_instance = SlaveExternalTriggerTest()

    try:
        # 运行外部触发测试
        test_instance.run_external_trigger_test()

    except Exception as e:
        print(f"❌ 外部触发测试出错: {e}")
    finally:
        test_instance.cleanup()

if __name__ == "__main__":
    main()
