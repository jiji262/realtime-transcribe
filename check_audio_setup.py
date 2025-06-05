#!/usr/bin/env python3
"""
音频设置检查工具
Audio Setup Check Tool
"""

import subprocess
import sys

def check_current_output_device():
    """检查当前系统输出设备"""
    print("=== 当前系统音频输出设备检查 ===")
    
    try:
        # 使用osascript获取当前输出设备
        result = subprocess.run([
            'osascript', '-e', 
            'tell application "System Preferences" to return (output device of (get current output device))'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            current_device = result.stdout.strip()
            print(f"当前系统输出设备: {current_device}")
            
            if "BlackHole" in current_device:
                print("✅ 当前使用BlackHole设备")
                return "blackhole"
            elif "多输出" in current_device or "Multi-Output" in current_device:
                print("✅ 当前使用多输出设备")
                return "multi-output"
            else:
                print("❌ 当前没有使用BlackHole相关设备")
                print(f"   当前设备: {current_device}")
                return "other"
        else:
            print("无法获取当前输出设备信息")
            return "unknown"
            
    except Exception as e:
        print(f"检查输出设备时出错: {e}")
        return "error"

def get_audio_devices_info():
    """获取音频设备详细信息"""
    print("\n=== 系统音频设备信息 ===")
    
    try:
        # 使用system_profiler获取音频设备信息
        result = subprocess.run([
            'system_profiler', 'SPAudioDataType'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            in_audio_section = False
            current_device = ""
            
            for line in lines:
                line = line.strip()
                
                if 'Audio:' in line or 'Audio (Built In):' in line:
                    in_audio_section = True
                    continue
                
                if in_audio_section:
                    if line.startswith('Default Output Device:'):
                        device_name = line.split(':', 1)[1].strip()
                        print(f"默认输出设备: {device_name}")
                        
                        if "BlackHole" in device_name:
                            print("  ✅ 默认输出是BlackHole")
                        elif "Multi-Output" in device_name or "多输出" in device_name:
                            print("  ✅ 默认输出是多输出设备")
                        else:
                            print("  ❌ 默认输出不是BlackHole相关设备")
                    
                    elif line.startswith('Default Input Device:'):
                        device_name = line.split(':', 1)[1].strip()
                        print(f"默认输入设备: {device_name}")
                    
                    elif 'BlackHole' in line:
                        print(f"发现BlackHole设备: {line}")
                    
                    elif 'Multi-Output' in line or '多输出' in line:
                        print(f"发现多输出设备: {line}")
        
    except Exception as e:
        print(f"获取音频设备信息时出错: {e}")

def check_audio_midi_setup():
    """检查音频MIDI设置"""
    print("\n=== 音频MIDI设置检查指南 ===")
    print("请手动检查以下设置:")
    print()
    print("1. 打开 应用程序 → 实用工具 → 音频MIDI设置")
    print()
    print("2. 在左侧设备列表中查找:")
    print("   □ BlackHole 2ch")
    print("   □ 多输出设备 (Multi-Output Device)")
    print()
    print("3. 如果有多输出设备，点击选择它，然后在右侧检查:")
    print("   □ BlackHole 2ch 是否被勾选？")
    print("   □ MacBook Pro扬声器 是否被勾选？")
    print("   □ 两个设备都应该有勾选标记")
    print()
    print("4. 如果没有多输出设备:")
    print("   - 点击左下角的 + 按钮")
    print("   - 选择 '创建多输出设备'")
    print("   - 勾选 BlackHole 2ch 和您的扬声器")

def test_audio_playback():
    """测试音频播放"""
    print("\n=== 音频播放测试 ===")
    print("请进行以下测试:")
    print()
    print("1. 播放测试音频:")
    print("   - 打开YouTube视频")
    print("   - 或播放音乐")
    print("   - 或使用系统声音测试")
    print()
    print("2. 检查是否能听到声音:")
    print("   - 如果使用多输出设备，应该能听到声音")
    print("   - 如果直接使用BlackHole，可能听不到声音（这是正常的）")
    print()
    print("3. 检查音量设置:")
    print("   - 系统音量是否静音？")
    print("   - 应用程序音量是否静音？")
    print("   - 音量是否足够大？")

def provide_step_by_step_solution():
    """提供分步解决方案"""
    print("\n=== 分步解决方案 ===")
    print()
    print("如果仍然检测不到音频，请按以下步骤操作:")
    print()
    print("步骤1: 重新配置多输出设备")
    print("  1. 打开 音频MIDI设置")
    print("  2. 删除现有的多输出设备（如果有）")
    print("  3. 重新创建多输出设备:")
    print("     - 点击 + → 创建多输出设备")
    print("     - 勾选 BlackHole 2ch")
    print("     - 勾选 MacBook Pro扬声器")
    print("     - 确保两个都有勾选标记")
    print()
    print("步骤2: 设置系统输出")
    print("  1. 打开 系统偏好设置 → 声音 → 输出")
    print("  2. 选择刚创建的多输出设备")
    print()
    print("步骤3: 测试音频")
    print("  1. 播放YouTube视频")
    print("  2. 确认能听到声音")
    print("  3. 运行音频检测测试")
    print()
    print("步骤4: 如果还是不行，尝试:")
    print("  1. 重启音频服务: sudo killall coreaudiod")
    print("  2. 重新启动计算机")
    print("  3. 重新安装BlackHole")

if __name__ == "__main__":
    print("🔊 音频设置检查工具")
    print("=" * 50)
    
    # 检查当前输出设备
    current_output = check_current_output_device()
    
    # 获取音频设备信息
    get_audio_devices_info()
    
    # 检查音频MIDI设置
    check_audio_midi_setup()
    
    # 测试音频播放
    test_audio_playback()
    
    # 提供解决方案
    provide_step_by_step_solution()
    
    print("\n" + "=" * 50)
    print("🎯 检查完成!")
    print()
    print("关键检查点:")
    print("1. 系统输出设备是否选择了多输出设备？")
    print("2. 多输出设备是否包含BlackHole 2ch？")
    print("3. 是否有音频正在播放？")
    print("4. 能否听到播放的音频？")
    print()
    print("如果以上都正确，音频检测应该可以工作。")
    print("如果仍有问题，请重新配置多输出设备。")
