#!/usr/bin/env python3
"""
MasterPi5 双相机同步拍照测试脚本
功能：通过Pin 22触发SlavePi5同步拍照，测试延迟
作者：Claude Code Assistant
"""

import time
from datetime import datetime
from pathlib import Path
from gpiozero import OutputDevice
from picamera2 import Picamera2
import numpy as np

class DualCameraSyncTest:
    def __init__(self):
        # GPIO设置 - Pin 22作为触发输出
        self.trigger_pin = OutputDevice(22)

        # 相机设置
        self.camera = Picamera2()

        # 图像保存路径
        self.save_dir = Path("/mnt/projects/PiTrac/test_images")
        self.save_dir.mkdir(exist_ok=True)

        # 时间戳记录
        self.master_capture_time = None
        self.sync_results = []

    def setup_camera(self):
        """初始化Master Pi相机"""
        try:
            # 配置相机 - 高分辨率用于测试
            camera_config = self.camera.create_still_configuration(
                main={"size": (1920, 1080)},
                lores={"size": (640, 480)},
                display="lores"
            )
            self.camera.configure(camera_config)
            self.camera.start()

            # 相机预热
            time.sleep(2)
            print("✅ Master Pi 相机初始化完成")
            return True

        except Exception as e:
            print(f"❌ Master Pi 相机初始化失败: {e}")
            return False

    def trigger_slave_capture(self):
        """发送触发信号给Slave Pi"""
        try:
            # 发送高电平触发信号
            self.trigger_pin.on()
            trigger_time = time.time()

            # 保持信号100ms
            time.sleep(0.1)
            self.trigger_pin.off()

            print(f"📡 触发信号已发送 - 时间戳: {trigger_time:.6f}")
            return trigger_time

        except Exception as e:
            print(f"❌ 触发信号发送失败: {e}")
            return None

    def capture_master_image(self, test_id):
        """Master Pi拍照"""
        try:
            # 记录拍照开始时间
            capture_start = time.time()

            # 拍照
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            master_image_path = self.save_dir / f"master_{test_id}_{timestamp_str}.jpg"

            # 使用capture_file确保立即保存
            self.camera.capture_file(str(master_image_path))

            # 记录拍照完成时间
            capture_end = time.time()
            self.master_capture_time = capture_end

            print(f"📸 Master Pi 拍照完成: {master_image_path.name}")
            print(f"⏱️  Master Pi 拍照耗时: {(capture_end - capture_start)*1000:.2f}ms")

            return master_image_path, capture_end

        except Exception as e:
            print(f"❌ Master Pi 拍照失败: {e}")
            return None, None

    def wait_for_slave_result(self, test_id, timeout=5):
        """等待Slave Pi的结果文件"""
        slave_result_file = self.save_dir / f"slave_result_{test_id}.txt"

        print(f"⏳ 等待Slave Pi结果文件: {slave_result_file.name}")

        start_wait = time.time()
        while time.time() - start_wait < timeout:
            if slave_result_file.exists():
                try:
                    with open(slave_result_file, 'r') as f:
                        slave_data = f.read().strip().split(',')
                        slave_capture_time = float(slave_data[0])
                        slave_image_name = slave_data[1]

                    # 清理结果文件
                    slave_result_file.unlink()

                    return slave_capture_time, slave_image_name

                except Exception as e:
                    print(f"⚠️  读取Slave结果文件失败: {e}")
                    time.sleep(0.1)
                    continue

            time.sleep(0.1)

        print(f"⏰ 等待Slave Pi结果超时 ({timeout}s)")
        return None, None

    def calculate_sync_delay(self, master_time, slave_time):
        """计算同步延迟"""
        if master_time and slave_time:
            delay_ms = (slave_time - master_time) * 1000
            return delay_ms
        return None

    def run_sync_test(self, test_count=5):
        """运行同步测试"""
        print("🚀 开始双相机同步测试")
        print("=" * 60)

        if not self.setup_camera():
            return False

        print(f"📊 将进行 {test_count} 次同步测试")
        print("⚠️  请确保Slave Pi已运行监听脚本!")

        input("按Enter键开始测试...")

        delays = []

        for i in range(test_count):
            test_id = f"{int(time.time())}_{i+1:03d}"
            print(f"\n🧪 测试 {i+1}/{test_count} (ID: {test_id})")

            # 同时触发Slave Pi和Master Pi拍照
            trigger_time = self.trigger_slave_capture()
            if not trigger_time:
                continue

            # Master Pi拍照
            master_path, master_time = self.capture_master_image(test_id)
            if not master_time:
                continue

            # 等待Slave Pi结果
            slave_time, slave_image = self.wait_for_slave_result(test_id)

            if slave_time:
                delay = self.calculate_sync_delay(master_time, slave_time)
                delays.append(delay)

                print(f"✅ 同步成功!")
                print(f"   Master拍照时间: {master_time:.6f}")
                print(f"   Slave拍照时间:  {slave_time:.6f}")
                print(f"   同步延迟: {delay:.2f}ms")
                print(f"   Slave图像: {slave_image}")
            else:
                print(f"❌ 未收到Slave Pi响应")

            # 测试间隔
            if i < test_count - 1:
                time.sleep(2)

        # 统计结果
        self.print_statistics(delays)

        return True

    def print_statistics(self, delays):
        """打印统计结果"""
        print("\n" + "=" * 60)
        print("📈 同步测试统计结果")
        print("=" * 60)

        if not delays:
            print("❌ 没有成功的同步测试")
            return

        valid_delays = [d for d in delays if d is not None]

        if valid_delays:
            avg_delay = np.mean(valid_delays)
            std_delay = np.std(valid_delays)
            min_delay = np.min(valid_delays)
            max_delay = np.max(valid_delays)

            print(f"✅ 成功测试次数: {len(valid_delays)}")
            print(f"📊 平均延迟: {avg_delay:.2f}ms")
            print(f"📊 延迟标准差: {std_delay:.2f}ms")
            print(f"📊 最小延迟: {min_delay:.2f}ms")
            print(f"📊 最大延迟: {max_delay:.2f}ms")

            # 延迟质量评估
            if avg_delay < 50:
                print("🎉 同步性能: 优秀 (<50ms)")
            elif avg_delay < 100:
                print("👍 同步性能: 良好 (<100ms)")
            elif avg_delay < 200:
                print("⚠️  同步性能: 一般 (<200ms)")
            else:
                print("❌ 同步性能: 需要优化 (>200ms)")

        print("=" * 60)

    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'camera'):
                self.camera.stop()
                self.camera.close()

            if hasattr(self, 'trigger_pin'):
                self.trigger_pin.close()

            print("🧹 资源清理完成")
        except Exception as e:
            print(f"⚠️  清理资源时出错: {e}")

def main():
    test = DualCameraSyncTest()

    try:
        # 运行测试
        test.run_sync_test(test_count=5)

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
    finally:
        test.cleanup()

if __name__ == "__main__":
    main()
