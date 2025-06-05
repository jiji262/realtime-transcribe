# 🎤 Real-time Speech Transcription

<div align="center">

![GitHub last commit](https://img.shields.io/github/last-commit/jiji262/realtime-transcribe)
![GitHub license](https://img.shields.io/github/license/jiji262/realtime-transcribe)
![Python version](https://img.shields.io/badge/python-3.7%2B-blue)

**Turn your speech into text in real-time with beautiful floating captions!**

</div>

## ✅ Status

**🎉 FULLY WORKING!** All major bugs fixed and ready to use.

### 🆕 Latest Major Update (2025-01-XX)
- 🎉 **Multi-line subtitle display**: Shows up to 5 lines of transcription history
- ⏱️ **Stable 5-second display**: No more flickering subtitles
- 🔄 **Smart scrolling**: Automatic upward scrolling when exceeding max lines
- 🎯 **Auto MacBook mic detection**: Automatically finds and uses MacBook Pro microphone
- ✨ **Professional subtitle experience**: Smooth transitions and visual improvements
- 🚀 **One-command start**: Super simple `python start.py` to get started

### ⚠️ Known Issues
- Some audio devices may require manual selection
- First-time model download may take a few minutes

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirement.txt
```

### 2. Super Simple Start ⭐

**The easiest way (recommended):**
```bash
python start.py
```
Choose from the interactive menu, or start directly:

```bash
python start.py --english    # English transcription
python start.py --chinese    # Chinese transcription
python start.py --auto       # Auto-detect language
```

### 3. Advanced Usage
```bash
# Default optimized settings (tiny.en model, MacBook mic, English)
python transcribe.py

# Better quality (slower)
python transcribe.py --model base.en

# Chinese transcription
python transcribe.py --model base --language zh

# Larger subtitle font
python transcribe.py --font-size 40
```

That's it! 🎉

## ✨ What It Does

🎯 **Real-time speech-to-text** - Speak and see your words appear instantly
📝 **Multi-line subtitle display** - Shows up to 5 lines of transcription history
⏱️ **Stable 5-second display** - No more flickering, subtitles stay visible
🔄 **Smart scrolling** - Automatic upward scrolling for continuous conversation
🖥️ **Beautiful floating captions** - Elegant overlay window you can move around
🎤 **Auto microphone detection** - Automatically finds your MacBook microphone
🌍 **Multiple languages** - English, Chinese, and more
⚡ **Fast and accurate** - Powered by OpenAI's Whisper AI
🔒 **Privacy-first** - Everything runs locally on your computer

## 📋 Requirements

- Python 3.7+
- Working microphone
- 4GB+ RAM recommended

## 🎛️ Usage Options

### Interactive Menu (Recommended)
```bash
python3 start.py
```
Choose from:
- 🇺🇸 English (Fast & Accurate)
- 🇨🇳 Chinese (中文)
- ⚡ Ultra-fast English
- 🎯 High-accuracy English

### Direct Commands
```bash
# Default optimized settings (recommended)
python transcribe.py

# Better quality English
python transcribe.py --model base.en

# Chinese transcription
python transcribe.py --model base --language zh

# Auto-detect language
python transcribe.py --model base --language auto

# Larger subtitle font
python transcribe.py --font-size 40
```

## 🛠️ Installation

### Option 1: Automatic Installation (Recommended)
```bash
git clone https://github.com/jiji262/realtime-transcribe.git
cd realtime-transcribe
./install.sh
```

### Option 2: Manual Installation
```bash
git clone https://github.com/jiji262/realtime-transcribe.git
cd realtime-transcribe
pip install -r requirement.txt
python3 start.py
```

## 💡 Tips

- **Speak clearly** and at a normal pace
- **Position your microphone** close to your mouth
- **Minimize background noise** for better accuracy
- **Drag the caption window** to your preferred position
- **Press Ctrl+C** to stop transcription

## 🔧 Troubleshooting

**No microphone detected?**
- Check system permissions
- Try a different microphone
- Restart the application

**Poor transcription quality?**
- Speak more clearly
- Reduce background noise
- Try a larger model (base.en instead of tiny.en)
- Move closer to the microphone

**Application crashes?**
- Make sure no other apps are using your microphone
- Check that you have enough RAM
- Try the ultra-fast mode first

## 🎛️ Advanced Options

### Model Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| tiny.en | 76MB | ⚡⚡⚡ | ⭐⭐ | Quick demos |
| base.en | 145MB | ⚡⚡ | ⭐⭐⭐ | Daily use |
| small.en | 465MB | ⚡ | ⭐⭐⭐⭐ | High accuracy |

### Custom Commands

```bash
# Ultra-fast mode
python3 transcribe.py --model tiny.en --language en --realtime-mode --chunk-size 512

# High accuracy mode
python3 transcribe.py --model base.en --language en --chunk-size 2048

# Chinese mode
python3 transcribe.py --model small --language zh

# Custom font size
python3 transcribe.py --model tiny.en --language en --font-size 40
```

---

## 🌍 中文说明

### 🚀 快速开始
```bash
# 1. 安装依赖
pip install -r requirement.txt

# 2. 运行程序
python3 start.py

# 3. 选择中文模式
```

### 💡 使用提示
- **清晰说话**，保持正常语速
- **靠近麦克风**，减少背景噪音
- **拖动字幕窗口**到合适位置
- **按 Ctrl+C** 停止转录

### 🔧 故障排除
- **麦克风无法识别**：检查系统权限，重启程序
- **转录质量差**：说话更清晰，减少噪音，尝试更大模型
- **程序崩溃**：确保没有其他程序占用麦克风

---

## 📄 License

[MIT License](LICENSE) - Free to use, modify, and distribute.
