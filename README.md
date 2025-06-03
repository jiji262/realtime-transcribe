# Realtime Speech Transcription | 实时语音转写系统

<div align="center">
  
![GitHub last commit](https://img.shields.io/github/last-commit/jiji262/realtime-transcribe)
![GitHub license](https://img.shields.io/github/license/jiji262/realtime-transcribe)
![Python version](https://img.shields.io/badge/python-3.7%2B-blue)

</div>

Real-time speech transcription using the OpenAI Whisper model, displaying elegant captions on screen. Supports multiple languages including English and Chinese with a beautiful floating interface.

*[English](#english-documentation) | [中文文档](#chinese-documentation)*

---

# English Documentation

## 🌟 Overview

This application utilizes the state-of-the-art Whisper AI model from OpenAI to provide real-time speech-to-text transcription, displaying the results as elegant captions on your screen. It's perfect for:

- Live presentations and lectures
- Creating accessible content for hearing-impaired audiences
- Generating real-time subtitles for videos or meetings
- Language learning and pronunciation practice
- Dictation and note-taking

## ✨ Features

- **Real-time Recognition**: Transcribe speech as you talk with minimal delay
- **Multi-language Support**: Works with English, Chinese, and many other languages
- **Elegant UI**: Beautiful semi-transparent floating caption window
- **Smart Text Formatting**: Automatic sentence detection and line breaks for better readability
- **Customizable**: Adjustable font size, window position, and transparency
- **Flexible Models**: Multiple performance modes from ultra-fast to high-accuracy
- **Movable Interface**: Drag the caption window anywhere on your screen
- **GPU Acceleration**: Optional CUDA support for faster processing
- **Offline Processing**: All speech processing happens locally on your machine
- **Open Source**: Free to use, modify, and distribute

## 🔧 System Requirements

- Python 3.7 or higher
- 4GB RAM minimum (8GB+ recommended for larger models)
- 1GB free disk space for model storage
- Working microphone
- For GPU acceleration: CUDA-compatible graphics card

## 📦 Installation

### Prerequisites

Ensure you have Python 3.7+ installed:

```shell
python --version
```

### Step 1: Clone the Repository

```shell
git clone https://github.com/jiji262/realtime-transcribe.git
cd realtime-transcribe
```

### Step 2: Install Dependencies

```shell
pip install -r requirement.txt
```

This will install the necessary packages including:
- whisper
- PyQt5
- torch
- numpy
- pyaudio
- SpeechRecognition
- faster-whisper (optional for GPU acceleration)

## 🚀 Quick Start

This project offers three convenient ways to start:

### 1. Quick Launch Scripts (Recommended)

Run one of the pre-configured scripts based on your language:

**English transcription:**
```shell
./start_english.sh
```

**Chinese transcription:**
```shell
./start_chinese.sh
```

### 2. Interactive Menu

For more options, use the interactive menu:

```shell
./run_transcribe.sh
```

This provides a user-friendly interface with detailed options:

- **Ultra-fast English Mode**: Lowest latency, best for simple content
- **Standard English Mode**: Balanced speed and accuracy
- **High-accuracy English Mode**: Best precision, higher resource usage
- **Standard Chinese Mode**: Optimized for Chinese recognition
- **Compact Chinese Mode**: Lighter Chinese model for limited resources
- **Ultra-realtime Mode**: Maximum responsiveness for live demonstrations

### 3. Advanced Usage

For complete control, use the Python script directly with custom parameters:

```shell
python3 transcribe.py --input-provider pyaudio --model tiny.en --language en --no-faster-whisper --realtime-mode
```

## ⚙️ Configuration Options

### Key Parameters

- `--model`: Model size/type
  - English-optimized: `tiny.en`, `base.en`, `small.en`, `medium.en`
  - Multilingual: `tiny`, `base`, `small`, `medium`
  
- `--language`: Language code
  - e.g., `en` (English), `zh` (Chinese), `fr` (French), etc.
  
- `--input-provider`: Audio input system
  - `pyaudio`: Better for continuous transcription
  - `speech-recognition`: Alternative option
  
- `--realtime-mode`: Optimize for lowest latency

- `--font-size`: Caption text size (default: 30)

- `--chunk-size`: Audio processing chunk size (lower = faster response, higher = better accuracy)

- `--no-faster-whisper`: Use standard Whisper implementation

### Model Size Comparison

| Model | Size | Speed | Accuracy | Memory Usage |
|-------|------|-------|----------|--------------|
| tiny.en | 76MB | Fastest | Basic | Minimal |
| base.en | 145MB | Fast | Good | Low |
| small.en | 465MB | Medium | Very Good | Moderate |
| medium.en | 1.5GB | Slow | Excellent | High |
| large | 3GB+ | Slowest | Best | Very High |

## 💡 Usage Tips

- **Position the Window**: Drag the caption window to your preferred location
- **Optimize for Speed**: 
  - Use smaller models (tiny/base) for faster response
  - Enable `--realtime-mode`
  - Reduce `--chunk-size` values
- **Optimize for Accuracy**:
  - Use larger models (small/medium)
  - Specify the correct language with `--language`
  - Increase `--chunk-size` values
- **System Performance**:
  - Close other audio applications
  - Ensure your microphone is not being used by other programs
  - For best performance, use a dedicated microphone

## ❓ Troubleshooting

### Audio Recognition Issues

- **Microphone Not Detected**: 
  - Check system permissions
  - Try a different microphone or USB port
  - Restart the application

- **Poor Recognition Quality**:
  - Speak clearly and at a moderate pace
  - Reduce background noise
  - Use a better microphone or position it closer
  - Try a larger model

### Performance Problems

- **High CPU Usage**:
  - Use a smaller model
  - Reduce chunk size
  - Close other applications

- **Delayed Captions**:
  - Switch to Ultra-realtime mode
  - Use tiny.en model
  - Reduce chunk-size parameter

### Technical Issues

- **CUDA Errors**: 
  - Update your GPU drivers
  - Install compatible PyTorch version
  - Remove `--no-faster-whisper` flag

- **Audio Input Errors**:
  - Install PortAudio library if missing
  - Try alternative input provider

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](LICENSE) - Feel free to use, modify, and distribute the code.

---

# Chinese Documentation

## 🌟 项目概述

本应用程序利用OpenAI的Whisper AI模型提供实时语音转文字功能，并将结果以优雅的字幕形式显示在屏幕上。它适用于：

- 现场演讲和讲座
- 为听障人士创建无障碍内容
- 为视频或会议生成实时字幕
- 语言学习和发音练习
- 听写和笔记记录

## ✨ 功能特性

- **实时识别**：在您说话的同时转录语音，延迟极小
- **多语言支持**：支持英语、中文等多种语言
- **优雅界面**：美观的半透明浮动字幕窗口
- **智能文本格式**：自动检测句子并换行，提高可读性
- **高度可定制**：可调整字体大小、窗口位置和透明度
- **灵活模型选择**：从超快速到高精度的多种性能模式
- **可移动界面**：可将字幕窗口拖动到屏幕上的任何位置
- **GPU加速**：可选CUDA支持，加快处理速度
- **离线处理**：所有语音处理在本地机器上完成
- **开源**：免费使用、修改和分发

## 🔧 系统要求

- Python 3.7或更高版本
- 最低4GB内存（推荐8GB+用于较大模型）
- 1GB可用磁盘空间用于模型存储
- 可用麦克风
- GPU加速：CUDA兼容的显卡

## 📦 安装

### 前提条件

确保已安装Python 3.7+：

```shell
python --version
```

### 步骤1：克隆仓库

```shell
git clone https://github.com/jiji262/realtime-transcribe.git
cd realtime-transcribe
```

### 步骤2：安装依赖

```shell
pip install -r requirement.txt
```

这将安装必要的包，包括：
- whisper
- PyQt5
- torch
- numpy
- pyaudio
- SpeechRecognition
- faster-whisper（GPU加速可选）

## 🚀 快速开始

本项目提供三种便捷的启动方式：

### 1. 快速启动脚本（推荐）

根据您的语言运行预配置脚本：

**英语转录：**
```shell
./start_english.sh
```

**中文转录：**
```shell
./start_chinese.sh
```

### 2. 交互式菜单

需要更多选项，请使用交互式菜单：

```shell
./run_transcribe.sh
```

这提供了一个用户友好的界面，带有详细选项：

- **超快速英语模式**：最低延迟，适合简单内容
- **标准英语模式**：平衡速度和准确性
- **高精度英语模式**：最佳精度，资源占用更高
- **标准中文模式**：针对中文识别优化
- **精简中文模式**：适用于资源受限设备的轻量级中文模型
- **超实时模式**：为现场演示提供最大响应速度

### 3. 高级用法

要完全控制，请使用Python脚本直接设置自定义参数：

```shell
python3 transcribe.py --input-provider pyaudio --model tiny.en --language en --no-faster-whisper --realtime-mode
```

## ⚙️ 配置选项

### 主要参数

- `--model`：模型大小/类型
  - 英语优化：`tiny.en`, `base.en`, `small.en`, `medium.en`
  - 多语言：`tiny`, `base`, `small`, `medium`
  
- `--language`：语言代码
  - 例如：`en`（英语）、`zh`（中文）、`fr`（法语）等
  
- `--input-provider`：音频输入系统
  - `pyaudio`：更适合连续转录
  - `speech-recognition`：替代选项
  
- `--realtime-mode`：优化最低延迟

- `--font-size`：字幕文本大小（默认：30）

- `--chunk-size`：音频处理块大小（较小=响应更快，较大=准确度更高）

- `--no-faster-whisper`：使用标准Whisper实现

### 模型大小比较

| 模型 | 大小 | 速度 | 准确度 | 内存使用 |
|-------|------|-------|----------|--------------|
| tiny.en | 76MB | 最快 | 基本 | 最小 |
| base.en | 145MB | 快 | 良好 | 低 |
| small.en | 465MB | 中等 | 很好 | 中等 |
| medium.en | 1.5GB | 慢 | 优秀 | 高 |
| large | 3GB+ | 最慢 | 最佳 | 非常高 |

## 💡 使用技巧

- **调整窗口位置**：将字幕窗口拖动到您喜欢的位置
- **优化速度**：
  - 使用较小模型（tiny/base）获得更快响应
  - 启用`--realtime-mode`
  - 减小`--chunk-size`值
- **优化准确度**：
  - 使用较大模型（small/medium）
  - 使用`--language`指定正确的语言
  - 增加`--chunk-size`值
- **系统性能**：
  - 关闭其他音频应用
  - 确保您的麦克风没有被其他程序使用
  - 为获得最佳性能，使用专用麦克风

## ❓ 故障排除

### 音频识别问题

- **麦克风未检测到**：
  - 检查系统权限
  - 尝试不同的麦克风或USB端口
  - 重启应用程序

- **识别质量差**：
  - 清晰地以适中速度说话
  - 减少背景噪音
  - 使用更好的麦克风或将其放置更近
  - 尝试使用更大的模型

### 性能问题

- **CPU使用率高**：
  - 使用较小模型
  - 减小块大小
  - 关闭其他应用程序

- **字幕延迟**：
  - 切换到超实时模式
  - 使用tiny.en模型
  - 减小chunk-size参数

### 技术问题

- **CUDA错误**：
  - 更新GPU驱动程序
  - 安装兼容的PyTorch版本
  - 移除`--no-faster-whisper`标志

- **音频输入错误**：
  - 如果缺少PortAudio库，请安装
  - 尝试替代输入提供程序

## 🤝 贡献

欢迎贡献！请随时提交Pull Request。

## 📄 许可证

[MIT许可证](LICENSE) - 可自由使用、修改和分发代码。
