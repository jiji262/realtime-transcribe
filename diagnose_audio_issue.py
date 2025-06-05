#!/usr/bin/env python3
"""
音频检测问题诊断工具
Audio Detection Issue Diagnostic Tool
"""

import pyaudio
import numpy as np
import time
import subprocess
import sys

def check_system_audio_output():
    """检查系统音频输出设置"""
    print("=== 系统音频输出检查 / System Audio Output Check ===")
    
    try:
        # 检查当前音频输出设备
        result = subprocess.run(['system_profiler', 'SPAudioDataType'], 
                              capture_output=True, text=True, timeout=10)
        
        print("当前音频设备信息:")
        lines = result.stdout.split('\n')
        for line in lines:
            if 'BlackHole' in line or 'Multi-Output' in line or 'Built-in' in line:
                print(f"  {line.strip()}")
    except Exception as e:
        print(f"无法获取系统音频信息: {e}")
    
    print("\n请手动检查:")
    print("1. 系统偏好设置 → 声音 → 输出")
    print("2. 当前选择的输出设备是什么？")
    print("3. 是否选择了 BlackHole 2ch 或多输出设备？")

def list_all_audio_devices():
    """列出所有音频设备的详细信息"""
    print("\n=== 详细音频设备列表 / Detailed Audio Device List ===")
    
    audio = pyaudio.PyAudio()
    
    print(f"总共发现 {audio.get_device_count()} 个音频设备:")
    
    for i in range(audio.get_device_count()):
        try:
            info = audio.get_device_info_by_index(i)
            device_type = []
            
            if info.get('maxInputChannels', 0) > 0:
                device_type.append(f"输入({info['maxInputChannels']}ch)")
            if info.get('maxOutputChannels', 0) > 0:
                device_type.append(f"输出({info['maxOutputChannels']}ch)")
            
            type_str = " + ".join(device_type) if device_type else "无"
            
            print(f"\n设备 {i}: {info['name']}")
            print(f"  类型: {type_str}")
            print(f"  默认采样率: {info['defaultSampleRate']}")
            print(f"  主机API: {info['hostApi']}")
            
            if 'BlackHole' in info['name']:
                print(f"  ✅ 这是BlackHole设备!")
                
        except Exception as e:
            print(f"设备 {i}: 错误 - {e}")
    
    audio.terminate()

def test_blackhole_with_different_formats():
    """测试BlackHole设备的不同音频格式"""
    print("\n=== BlackHole格式兼容性测试 / BlackHole Format Compatibility Test ===")
    
    audio = pyaudio.PyAudio()
    
    # 找到BlackHole设备
    blackhole_index = None
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if 'BlackHole' in info['name'] and info.get('maxInputChannels', 0) > 0:
            blackhole_index = i
            break
    
    if blackhole_index is None:
        print("❌ 未找到BlackHole输入设备")
        audio.terminate()
        return
    
    print(f"✅ 找到BlackHole设备: {blackhole_index}")
    
    # 测试不同的音频格式
    formats_to_test = [
        (pyaudio.paFloat32, "Float32"),
        (pyaudio.paInt16, "Int16"),
        (pyaudio.paInt24, "Int24"),
        (pyaudio.paInt32, "Int32")
    ]
    
    sample_rates = [16000, 44100, 48000]
    channels = [1, 2]
    
    working_configs = []
    
    for format_val, format_name in formats_to_test:
        for rate in sample_rates:
            for ch in channels:
                try:
                    # 尝试打开音频流
                    stream = audio.open(
                        format=format_val,
                        channels=ch,
                        rate=rate,
                        input=True,
                        input_device_index=blackhole_index,
                        frames_per_buffer=1024
                    )
                    
                    # 尝试读取一些数据
                    data = stream.read(1024, exception_on_overflow=False)
                    
                    stream.stop_stream()
                    stream.close()
                    
                    config = f"{format_name}, {rate}Hz, {ch}ch"
                    working_configs.append(config)
                    print(f"✅ 支持: {config}")
                    
                except Exception as e:
                    config = f"{format_name}, {rate}Hz, {ch}ch"
                    print(f"❌ 不支持: {config} - {str(e)[:50]}")
    
    print(f"\n总共 {len(working_configs)} 种配置可用")
    audio.terminate()
    return working_configs

def test_live_audio_detection():
    """实时音频检测测试"""
    print("\n=== 实时音频检测测试 / Live Audio Detection Test ===")
    
    audio = pyaudio.PyAudio()
    
    # 找到BlackHole设备
    blackhole_index = None
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if 'BlackHole' in info['name'] and info.get('maxInputChannels', 0) > 0:
            blackhole_index = i
            break
    
    if blackhole_index is None:
        print("❌ 未找到BlackHole设备")
        audio.terminate()
        return
    
    print(f"使用BlackHole设备: {blackhole_index}")
    print("开始10秒实时音频检测...")
    print("请现在播放音频内容（YouTube、音乐等）")
    print("按 Ctrl+C 提前停止")
    
    # 使用与system_audio_transcribe.py相同的配置
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 16000
    CHUNK = 512
    
    try:
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=blackhole_index,
            frames_per_buffer=CHUNK
        )
        
        max_values = []
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                max_val = np.max(np.abs(audio_data))
                max_values.append(max_val)
                
                # 实时显示
                bar_length = int(max_val * 50)
                bar = "█" * bar_length + "░" * (50 - bar_length)
                status = "🔊 有声" if max_val > 0.005 else "🔇 静音"
                print(f"\r[{bar}] {max_val:.6f} {status}", end="", flush=True)
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n\n⏹️ 用户停止测试")
                break
        
        stream.stop_stream()
        stream.close()
        
        # 分析结果
        print(f"\n\n=== 检测结果分析 ===")
        if max_values:
            avg_max = np.mean(max_values)
            overall_max = np.max(max_values)
            non_zero_count = sum(1 for x in max_values if x > 0.005)
            
            print(f"平均音频强度: {avg_max:.6f}")
            print(f"最大音频强度: {overall_max:.6f}")
            print(f"有效音频帧: {non_zero_count}/{len(max_values)}")
            print(f"静音阈值: 0.005")
            
            if overall_max < 0.001:
                print("\n❌ 完全没有音频信号")
                print("可能原因:")
                print("1. BlackHole没有设置为系统输出")
                print("2. 多输出设备配置错误")
                print("3. 没有音频在播放")
            elif overall_max < 0.005:
                print("\n⚠️ 音频信号很弱")
                print("可能需要:")
                print("1. 增加系统音量")
                print("2. 检查音频源音量")
                print("3. 降低静音阈值")
            else:
                print("\n✅ 音频信号正常!")
                print("系统音频转录应该可以工作")
        
    except Exception as e:
        print(f"\n❌ 音频流错误: {e}")
    
    audio.terminate()

def check_audio_routing():
    """检查音频路由配置"""
    print("\n=== 音频路由配置检查 / Audio Routing Configuration Check ===")
    
    print("请检查以下配置:")
    print("\n1. 系统偏好设置 → 声音 → 输出")
    print("   当前选择的输出设备是什么？")
    
    print("\n2. 如果使用多输出设备:")
    print("   - 打开 音频MIDI设置")
    print("   - 检查多输出设备是否包含:")
    print("     ✓ 您的扬声器/耳机")
    print("     ✓ BlackHole 2ch")
    print("   - 两个设备都应该被勾选")
    
    print("\n3. 测试音频播放:")
    print("   - 播放YouTube视频")
    print("   - 播放音乐")
    print("   - 确保能听到声音（如果使用多输出设备）")
    
    print("\n4. 常见问题:")
    print("   - 如果听不到声音：检查多输出设备配置")
    print("   - 如果检测不到音频：确认BlackHole在输出设备中")
    print("   - 如果音频很弱：增加系统音量")

if __name__ == "__main__":
    print("🔊 音频检测问题诊断工具")
    print("=" * 60)
    
    # 1. 检查系统音频输出
    check_system_audio_output()
    
    # 2. 列出所有音频设备
    list_all_audio_devices()
    
    # 3. 测试BlackHole格式兼容性
    working_configs = test_blackhole_with_different_formats()
    
    # 4. 检查音频路由配置
    check_audio_routing()
    
    # 5. 实时音频检测测试
    print("\n" + "=" * 60)
    response = input("是否进行实时音频检测测试? (y/n): ").lower().strip()
    if response in ['y', 'yes', '是', '']:
        test_live_audio_detection()
    
    print("\n🎯 诊断完成!")
    print("如果实时检测显示音频强度为0，问题在于音频路由配置")
    print("如果实时检测正常，问题可能在于转录程序的其他部分")
