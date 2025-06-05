#!/bin/bash

# Quick start for Chinese transcription
echo "🎤 开始中文实时转录..."
echo "按 Ctrl+C 停止"
echo "请对着麦克风清晰说话！"
echo ""
python3 transcribe.py --model small --language zh --chunk-size 2048 --min-duration 1.0 --max-duration 5.0