#!/usr/bin/env python3
"""
简单的Pin 22触发信号测试脚本
测试MasterPi5的Pin 22是否能触发SlavePi5相机硬件拍照
作者：Claude Code Assistant
"""

import time
from gpiozero import OutputDevice

class Pin22TriggerTest:
    def __init__(self):
        # GPIO设置 - Pin 22作为触发输出
        self.trigger_pin = OutputDevice(22)
        print("🔧 Pin 22触发器初始化完成")
    
    def send_trigger_pulse(self, duration_ms=100):
        """发送触发脉冲"""
        try:
            print(f"📡 发送触发信号 (持续{duration_ms}ms)...")
            
            # 发送高电平
            self.trigger_pin.on()
            start_time = time.time()
            print(f"   ⬆️  Pin 22 HIGH - 时间戳: {start_time:.6f}")
            
            # 保持指定时间
            time.sleep(duration_ms / 1000.0)
            
            # 回到低电平
            self.trigger_pin.off()
            end_time = time.time()
            print(f"   ⬇️  Pin 22 LOW  - 时间戳: {end_time:.6f}")
            print(f"   ⏱️  实际持续时间: {(end_time - start_time)*1000:.2f}ms")
            
            return True
            
        except Exception as e:
            print(f"❌ 发送触发信号失败: {e}")
            return False
    
    def continuous_trigger_test(self, count=5, interval=2):
        """连续触发测试"""
        print(f"🔄 开始连续触发测试 ({count}次, 间隔{interval}秒)")
        print("=" * 50)
        
        for i in range(count):
            print(f"\n🧪 第 {i+1}/{count} 次触发")
            
            if self.send_trigger_pulse():
                print("✅ 触发信号发送成功")
            else:
                print("❌ 触发信号发送失败")
            
            # 等待间隔（除了最后一次）
            if i < count - 1:
                print(f"⏳ 等待 {interval} 秒...")
                time.sleep(interval)
        
        print("\n" + "=" * 50)
        print("🎯 连续触发测试完成")
        print("💡 请检查SlavePi5相机是否有拍照动作")
    
    def interactive_trigger_test(self):
        """交互式触发测试"""
        print("🎮 交互式触发测试模式")
        print("=" * 50)
        print("💡 按Enter发送触发信号，输入'q'退出")
        
        while True:
            try:
                user_input = input("\n按Enter触发 (或输入'q'退出): ").strip().lower()
                
                if user_input == 'q':
                    print("👋 退出交互式测试")
                    break
                
                # 发送触发信号
                trigger_time = time.time()
                print(f"⚡ 用户触发 - 时间戳: {trigger_time:.6f}")
                
                if self.send_trigger_pulse():
                    print("✅ 触发信号发送完成")
                else:
                    print("❌ 触发信号发送失败")
                    
            except KeyboardInterrupt:
                print("\n⏹️  交互式测试被中断")
                break
            except Exception as e:
                print(f"❌ 交互式测试出错: {e}")
    
    def test_different_durations(self):
        """测试不同持续时间的触发信号"""
        durations = [10, 50, 100, 200, 500]  # 毫秒
        
        print("📏 测试不同持续时间的触发信号")
        print("=" * 50)
        
        for duration in durations:
            print(f"\n🕒 测试持续时间: {duration}ms")
            
            if self.send_trigger_pulse(duration):
                print(f"✅ {duration}ms触发信号发送成功")
            else:
                print(f"❌ {duration}ms触发信号发送失败")
            
            # 间隔2秒
            time.sleep(2)
        
        print("\n" + "=" * 50)
        print("📊 不同持续时间测试完成")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 确保引脚为低电平
            self.trigger_pin.off()
            self.trigger_pin.close()
            print("🧹 Pin 22触发器资源清理完成")
        except Exception as e:
            print(f"⚠️  清理资源时出错: {e}")

def main():
    print("🧪 Pin 22触发信号测试")
    print("=" * 60)
    print("🎯 目的: 测试MasterPi5 Pin 22能否触发SlavePi5相机拍照")
    print("📋 请在SlavePi5上观察相机是否有拍照动作")
    print("=" * 60)
    
    trigger_test = Pin22TriggerTest()
    
    try:
        # 显示测试选项
        while True:
            print("\n🎮 选择测试模式:")
            print("1️⃣  连续触发测试 (5次)")
            print("2️⃣  交互式触发测试")
            print("3️⃣  不同持续时间测试")
            print("4️⃣  单次触发测试")
            print("0️⃣  退出")
            
            choice = input("\n请选择 (0-4): ").strip()
            
            if choice == '1':
                trigger_test.continuous_trigger_test()
            elif choice == '2':
                trigger_test.interactive_trigger_test()
            elif choice == '3':
                trigger_test.test_different_durations()
            elif choice == '4':
                print("\n⚡ 单次触发测试")
                if trigger_test.send_trigger_pulse():
                    print("✅ 单次触发信号发送成功")
                else:
                    print("❌ 单次触发信号发送失败")
            elif choice == '0':
                print("👋 退出测试程序")
                break
            else:
                print("❌ 无效选择，请重新输入")
    
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
    finally:
        trigger_test.cleanup()

if __name__ == "__main__":
    main()