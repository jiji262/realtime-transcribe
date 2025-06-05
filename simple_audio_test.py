#!/usr/bin/env python3
"""
简单音频检测测试
Simple Audio Detection Test
"""

import pyaudio
import numpy as np
import time

def test_blackhole_audio():
    """测试BlackHole音频检测"""
    print("🔊 BlackHole音频检测测试")
    print("=" * 40)
    
    audio = pyaudio.PyAudio()
    
    # 使用设备3 (BlackHole 2ch)
    blackhole_index = 3
    
    print(f"使用设备 {blackhole_index}: BlackHole 2ch")
    print("配置: Float32, 16000Hz, 1ch, 512 chunk")
    
    # 与system_audio_transcribe.py完全相同的配置
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
        
        print("\n开始15秒音频检测...")
        print("请现在播放音频内容（YouTube、音乐等）")
        print("按 Ctrl+C 停止")
        print()
        
        max_values = []
        start_time = time.time()
        
        while time.time() - start_time < 15:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                max_val = np.max(np.abs(audio_data))
                max_values.append(max_val)
                
                # 实时显示
                bar_length = int(max_val * 50)
                bar = "█" * bar_length + "░" * (50 - bar_length)
                
                if max_val > 0.005:
                    status = f"🔊 有声 {max_val:.6f}"
                else:
                    status = f"🔇 静音 {max_val:.6f}"
                
                elapsed = time.time() - start_time
                print(f"\r[{elapsed:5.1f}s] [{bar}] {status}", end="", flush=True)
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n\n⏹️ 用户停止测试")
                break
        
        stream.stop_stream()
        stream.close()
        
        # 分析结果
        print(f"\n\n=== 检测结果 ===")
        if max_values:
            avg_max = np.mean(max_values)
            overall_max = np.max(max_values)
            non_zero_count = sum(1 for x in max_values if x > 0.005)
            total_frames = len(max_values)
            
            print(f"总检测时间: {len(max_values) * 0.1:.1f} 秒")
            print(f"平均音频强度: {avg_max:.6f}")
            print(f"最大音频强度: {overall_max:.6f}")
            print(f"有效音频帧: {non_zero_count}/{total_frames} ({non_zero_count/total_frames*100:.1f}%)")
            print(f"静音阈值: 0.005")
            
            if overall_max < 0.001:
                print("\n❌ 没有检测到任何音频信号")
                print("\n可能的解决方案:")
                print("1. 检查系统偏好设置 → 声音 → 输出")
                print("   确保选择了包含BlackHole的输出设备")
                print("2. 如果使用多输出设备:")
                print("   - 打开音频MIDI设置")
                print("   - 确认多输出设备包含BlackHole 2ch")
                print("3. 确保有音频正在播放")
                print("4. 检查系统音量设置")
                
            elif overall_max < 0.005:
                print("\n⚠️ 检测到微弱音频信号")
                print("建议:")
                print("1. 增加系统音量")
                print("2. 增加播放应用的音量")
                print("3. 或者降低转录程序的静音阈值")
                
            else:
                print("\n✅ 音频信号正常!")
                print("系统音频转录应该可以正常工作")
                print(f"检测到 {non_zero_count} 个有效音频帧")
        
    except Exception as e:
        print(f"\n❌ 音频流错误: {e}")
        print("\n可能的原因:")
        print("1. BlackHole设备不可用")
        print("2. 音频格式不支持")
        print("3. 设备被其他程序占用")
    
    audio.terminate()

def check_current_output_device():
    """检查当前系统输出设备"""
    print("\n=== 当前系统音频设置检查 ===")
    print("请手动检查以下设置:")
    print()
    print("1. 系统偏好设置 → 声音 → 输出")
    print("   当前选择的输出设备是:")
    print("   □ BlackHole 2ch")
    print("   □ 多输出设备")
    print("   □ MacBook Pro扬声器")
    print("   □ 其他设备")
    print()
    print("2. 如果选择了'多输出设备':")
    print("   - 打开应用程序 → 实用工具 → 音频MIDI设置")
    print("   - 选择'多输出设备'")
    print("   - 确认勾选了:")
    print("     ✓ BlackHole 2ch")
    print("     ✓ 您的扬声器/耳机")
    print()
    print("3. 测试音频播放:")
    print("   - 播放YouTube视频或音乐")
    print("   - 确认能听到声音")
    print("   - 然后运行此测试")

if __name__ == "__main__":
    check_current_output_device()
    
    print("\n" + "=" * 50)
    response = input("确认音频设置正确后，按回车开始测试 (或输入 n 取消): ").strip()
    
    if response.lower() not in ['n', 'no', '否']:
        test_blackhole_audio()
    else:
        print("测试取消")
    
    print("\n🎯 测试完成!")
    print("如果检测到音频信号，转录程序应该可以工作")
    print("如果没有检测到，请检查音频路由配置")
