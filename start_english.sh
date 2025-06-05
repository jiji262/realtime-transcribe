#!/bin/bash

# Quick start for English transcription
echo "🎤 Starting English real-time transcription..."
echo "Press Ctrl+C to stop"
echo "Speak clearly into your microphone!"
echo ""
python3 transcribe.py --model tiny.en --language en --realtime-mode --chunk-size 1024 --min-duration 0.5 --max-duration 3.0 --stabilize-turns 0