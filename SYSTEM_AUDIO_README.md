# 🔊 System Audio Transcription

Real-time transcription of system audio output (speakers/headphones) using BlackHole virtual audio device.

## 🚀 Quick Start

### Prerequisites
1. **BlackHole** must be installed on your macOS system (already installed)
2. **Configure Audio Routing** to capture system audio through BlackHole

### Basic Usage

```bash
# Start system audio transcription with default settings
python3 system_audio_transcribe.py

# Use better accuracy model
python3 system_audio_transcribe.py --model base.en

# Transcribe Chinese audio
python3 system_audio_transcribe.py --language zh

# Larger subtitle font
python3 system_audio_transcribe.py --font-size 40
```

## 🔧 BlackHole Setup

### Method 1: Multi-Output Device (Recommended)
1. Open **Audio MIDI Setup** (Applications > Utilities)
2. Click **+** and select **Create Multi-Output Device**
3. Check both:
   - Your speakers/headphones (e.g., "MacBook Pro Speakers")
   - **BlackHole 2ch**
4. Set this Multi-Output Device as your system output in System Preferences > Sound

### Method 2: Direct BlackHole Output
1. System Preferences > Sound > Output
2. Select **BlackHole 2ch** as output device
3. ⚠️ **Warning**: You won't hear audio unless you route it back to speakers

### Method 3: Using SoundSource or Similar Apps
1. Use apps like SoundSource to route specific app audio to BlackHole
2. Keep system audio on regular speakers
3. More granular control over what gets transcribed

## 🎯 Use Cases

### Video Calls & Meetings
- Transcribe Zoom, Teams, Google Meet audio
- Real-time captions for accessibility
- Meeting notes and transcription

### Media Content
- Transcribe YouTube videos, podcasts, movies
- Language learning with real-time subtitles
- Content analysis and note-taking

### System Notifications
- Transcribe system alerts and notifications
- Accessibility for hearing-impaired users

## ⚡ Performance Features

### Ultra-Low Latency Settings
- **Min duration**: 0.2s (vs 0.5s for microphone)
- **Max duration**: 1.5s for real-time processing
- **Chunk size**: 512 for responsive audio capture
- **Timeout**: 1.0s for quick processing

### Optimized for System Audio
- **BlackHole auto-detection**: Automatically finds and uses BlackHole device
- **Noise filtering**: Reduced sensitivity to prevent processing silence
- **Multi-line display**: Shows transcription history with smooth scrolling
- **Stable display**: 3-second display duration for readability

## 🎛️ Advanced Options

```bash
# Specify BlackHole device manually
python3 system_audio_transcribe.py --input 0

# Use faster-whisper for better performance
python3 system_audio_transcribe.py --no-faster-whisper

# Adjust latency settings
python3 system_audio_transcribe.py --min-duration 0.1 --max-duration 1.0

# Larger audio buffer for stability
python3 system_audio_transcribe.py --chunk-size 1024
```

## 🔍 Troubleshooting

### No Audio Detected
1. **Check BlackHole setup**: Ensure audio is routing through BlackHole
2. **Test with system audio**: Play music/video to verify audio flow
3. **Check device selection**: Verify BlackHole is detected and selected
4. **Audio levels**: Ensure system volume is not muted

### Poor Transcription Quality
1. **Use better model**: Try `--model base.en` or `--model small.en`
2. **Check audio quality**: Ensure clear audio source
3. **Adjust language**: Use `--language auto` for auto-detection
4. **Reduce background noise**: Use apps with good audio quality

### High CPU Usage
1. **Use tiny model**: Default `tiny.en` is most efficient
2. **Increase min-duration**: Use `--min-duration 0.5` for less frequent processing
3. **Larger chunks**: Use `--chunk-size 1024` for less frequent callbacks

## 🆚 Differences from Microphone Version

| Feature | Microphone (`transcribe.py`) | System Audio (`system_audio_transcribe.py`) |
|---------|------------------------------|---------------------------------------------|
| **Audio Source** | Physical microphone | System audio output via BlackHole |
| **Device Detection** | Auto-detects MacBook Pro microphone | Auto-detects BlackHole virtual device |
| **Use Case** | Speech input, dictation | Media transcription, meeting captions |
| **Setup Required** | None (built-in mic) | BlackHole installation and audio routing |
| **Audio Quality** | Depends on microphone | Depends on source application |
| **Background Noise** | Room noise, environment | Digital audio (cleaner) |

## 📝 Technical Details

### Audio Pipeline
1. **BlackHole Capture**: Virtual audio device captures system output
2. **PyAudio Processing**: Real-time audio stream processing
3. **Whisper Transcription**: AI-powered speech-to-text conversion
4. **Live Subtitles**: Multi-line display with history management

### Supported Formats
- **Sample Rate**: 16kHz (Whisper standard)
- **Channels**: Mono (converted from stereo if needed)
- **Format**: 16-bit PCM
- **Latency**: ~200-500ms end-to-end

### Models Available
- `tiny.en`: Fastest, English-only (~39 MB)
- `base.en`: Better accuracy, English-only (~74 MB)
- `small.en`: Good balance, English-only (~244 MB)
- `tiny`: Multilingual (~39 MB)
- `base`: Multilingual (~74 MB)

## 🔗 Related Files

- `transcribe.py`: Original microphone input transcription
- `start.py`: Simplified launcher for microphone version
- `README.md`: Main project documentation

## 🎉 Success Indicators

When working correctly, you should see:
```
✅ Found BlackHole device: 0. BlackHole 2ch
✅ System audio capture test successful! Queue size: X
✅ Audio data sufficient (X.XX seconds), starting transcription...
✅ Transcription result: 'Your transcribed text here'
```

The subtitle window will appear at the bottom of your screen showing real-time transcriptions of any audio playing through your system.
