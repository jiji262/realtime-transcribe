#!/bin/bash

# Start quick English mode
echo "Starting English real-time transcription..."
python3 transcribe.py --input-provider pyaudio --model tiny.en --no-faster-whisper --language en --chunk-size 1024 --realtime-mode 