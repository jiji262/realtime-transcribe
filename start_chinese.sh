#!/bin/bash

# Start Chinese mode
echo "Starting Chinese real-time transcription..."
python3 transcribe.py --input-provider pyaudio --model medium --no-faster-whisper --language zh --chunk-size 2048 