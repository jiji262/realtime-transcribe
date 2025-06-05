#!/usr/bin/env python3
"""
测试所有音频设备 - 找出哪个设备能检测到音频
Test All Audio Devices - Find which device can detect audio
"""

import pyaudio
import numpy as np
import time

def test_all_input_devices():
    """测试所有输入设备"""
    print("🔊 测试所有音频输入设备")
    print("=" * 50)
    
    audio = pyaudio.PyAudio()
    
    # 获取所有输入设备
    input_devices = []
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            input_devices.append((i, info['name']))
            print(f"设备 {i}: {info['name']}")
    
    print(f"\n找到 {len(input_devices)} 个输入设备")
    print("现在测试每个设备...")
    print("请确保有音频正在播放！")
    
    # 测试每个设备
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 16000
    CHUNK = 512
    TEST_DURATION = 3  # 每个设备测试3秒
    
    results = []
    
    for device_index, device_name in input_devices:
        print(f"\n--- 测试设备 {device_index}: {device_name} ---")
        
        try:
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK
            )
            
            max_values = []
            start_time = time.time()
            
            while time.time() - start_time < TEST_DURATION:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    max_val = np.max(np.abs(audio_data))
                    max_values.append(max_val)
                    
                    # 实时显示
                    bar_length = int(max_val * 20)  # 缩短显示
                    bar = "█" * bar_length + "░" * (20 - bar_length)
                    print(f"\r  [{bar}] {max_val:.6f}", end="", flush=True)
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"\r  读取错误: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            
            # 分析结果
            if max_values:
                avg_max = np.mean(max_values)
                overall_max = np.max(max_values)
                non_zero_count = sum(1 for x in max_values if x > 0.005)
                
                result = {
                    'device_index': device_index,
                    'device_name': device_name,
                    'avg_max': avg_max,
                    'overall_max': overall_max,
                    'non_zero_count': non_zero_count,
                    'total_frames': len(max_values)
                }
                results.append(result)
                
                print(f"\n  平均: {avg_max:.6f}, 最大: {overall_max:.6f}, 有效帧: {non_zero_count}/{len(max_values)}")
                
                if overall_max > 0.005:
                    print(f"  ✅ 检测到音频信号!")
                else:
                    print(f"  ❌ 没有音频信号")
            else:
                print(f"\n  ❌ 无法读取数据")
                
        except Exception as e:
            print(f"  ❌ 设备错误: {e}")
    
    # 总结结果
    print(f"\n" + "=" * 50)
    print("🎯 测试结果总结:")
    
    working_devices = [r for r in results if r['overall_max'] > 0.005]
    
    if working_devices:
        print(f"\n✅ 找到 {len(working_devices)} 个可用设备:")
        for result in working_devices:
            print(f"  设备 {result['device_index']}: {result['device_name']}")
            print(f"    最大音频强度: {result['overall_max']:.6f}")
            print(f"    有效音频帧: {result['non_zero_count']}/{result['total_frames']}")
        
        # 推荐最佳设备
        best_device = max(working_devices, key=lambda x: x['overall_max'])
        print(f"\n🏆 推荐使用设备 {best_device['device_index']}: {best_device['device_name']}")
        print(f"   (最大音频强度: {best_device['overall_max']:.6f})")
        
    else:
        print(f"\n❌ 没有找到任何可用设备")
        print("可能的原因:")
        print("1. 音频路由配置仍有问题")
        print("2. 没有音频正在播放")
        print("3. 系统音量被静音")
        print("4. BlackHole配置不正确")
    
    audio.terminate()
    return working_devices

if __name__ == "__main__":
    print("请确保:")
    print("1. 系统输出设备选择了多输出设备")
    print("2. 多输出设备包含BlackHole 2ch")
    print("3. 有音频正在播放")
    print("4. 能听到音频")
    print()
    
    input("按回车开始测试所有设备...")
    
    working_devices = test_all_input_devices()
    
    if working_devices:
        print(f"\n🎉 成功! 可以使用设备 {working_devices[0]['device_index']} 进行系统音频转录")
    else:
        print(f"\n😞 需要进一步排查音频路由问题")
