# Realtime Speech Transcription

Real-time speech transcription using the Whisper model, displaying elegant captions on screen. Supports multiple languages including English and Chinese.

## Features

- Real-time speech recognition and transcription
- Beautiful semi-transparent floating caption window
- Supports multiple languages including English and Chinese
- Automatic sentence line breaks for better readability
- Customizable font size and display position
- Multiple modes: fast, standard, high-accuracy, and ultra-real-time

## Installation

1. Download the project

```shell
# Download and extract the project
cd /path/to/your/projects/
```

2. Install dependencies

```shell
# Enter project directory
cd realtime-transcribe
# Install dependencies
pip install -r requirement.txt
```

## Quick Start

This project offers three ways to start:

### 1. Quick Launch (Recommended)

Run the English or Chinese quick start scripts:

**English transcription:**
```shell
./start_english.sh
```

**Chinese transcription:**
```shell
./start_chinese.sh
```

### 2. Interactive Menu

Run the interactive menu script and choose your desired mode:

```shell
./run_transcribe.sh
```

Options include:
- Fast English Mode - Using tiny.en model, optimized for English
- Standard English Mode - Using base.en model, balancing speed and accuracy
- High-Accuracy English Mode - Using small.en model, higher accuracy
- Chinese Mode - Optimized for Chinese recognition
- Ultra-Real-Time Mode - Lowest latency, ideal for real-time scenarios

### 3. Advanced Usage

Directly use the Python script with parameters:

```shell
python3 transcribe.py --input-provider pyaudio --model tiny.en --language en --no-faster-whisper --realtime-mode
```

## Key Parameter Explanation

- `--model`: Select Whisper model size (tiny.en, base.en, small.en, medium.en, tiny, base, small, medium)
- `--language`: Specify language code (e.g., "en" for English, "zh" for Chinese)
- `--input-provider`: Audio input provider (pyaudio or speech-recognition)
- `--realtime-mode`: Enable real-time optimization mode
- `--font-size`: Caption font size
- `--chunk-size`: Audio chunk size, affects response speed

## Usage Tips

- **Movable Caption Window**: Drag the caption window to a suitable position with your mouse
- **Reduce Latency**: Use ultra-real-time mode for minimum latency, may sacrifice some accuracy
- **Improve Accuracy**: Using language-specific models and specifying the language parameter improves accuracy
- **System Resources**: Smaller models (tiny/base) are suitable for low-spec computers; larger models require more resources but offer higher accuracy

## Troubleshooting

### Cannot Recognize Sound

- Ensure your microphone is working properly and has permissions
- Try increasing volume or adjusting microphone position
- Check if the correct input device is selected

### Caption Display Delay

- Use "Ultra-Real-Time Mode" to reduce delay
- Try using smaller models (like tiny.en)
- Reduce chunk-size parameter value

### GPU Acceleration

If you want to use GPU acceleration, make sure CUDA is installed and remove the `--no-faster-whisper` parameter.

## License

[MIT License](LICENSE)
