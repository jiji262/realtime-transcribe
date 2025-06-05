#! python3.7

import sounddevice
import argparse
import os
import numpy as np
import speech_recognition as sr
import whisper
import torch
import threading
import pyaudio
import signal
import time
from faster_whisper import WhisperModel

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel, QTextEdit
from PyQt5.QtGui import QFont, QFontMetrics, QCursor
from PyQt5.QtCore import QChildEvent, Qt, QTimer, QPoint, QRect, QSize, pyqtSignal, QObject

# 全局共享变量用于线程间通信
text_to_display = "Loading captions..."
text_lock = threading.Lock()

def parse_args():
  parser = argparse.ArgumentParser(
    description="🔊 Real-time System Audio Transcription with Live Subtitles",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
🚀 Quick Start Examples:
  python system_audio_transcribe.py                    # Start with default settings (tiny.en model, BlackHole audio)
  python system_audio_transcribe.py --model base.en    # Use base model for better accuracy
  python system_audio_transcribe.py --language zh      # Transcribe Chinese audio
  python system_audio_transcribe.py --font-size 40     # Larger subtitle font

📝 For more help: https://github.com/jiji262/realtime-transcribe
    """
  )

  # 简化的核心参数，设置最佳默认值
  parser.add_argument("--model", default="tiny.en", help="Whisper model to use (default: tiny.en for fast English transcription)",
            choices=["tiny", "base", "small", "medium", "large", "tiny.en", "base.en", "small.en", "medium.en", "large-v3"])
  parser.add_argument("--language", default="en",
            help="Language for transcription (default: en). Use 'zh' for Chinese, 'auto' for auto-detection", type=str)
  parser.add_argument("--font-size", default=32,
            help="Subtitle font size (default: 32)", type=int)

  # 高级参数（大多数用户不需要修改）
  parser.add_argument("--input", default=None,
            help="Audio input device (auto-detects BlackHole by default)", type=str)
  parser.add_argument("--input-provider", default="pyaudio",
            choices=["pyaudio", "speech-recognition"],
            help="Audio input provider (default: pyaudio)", type=str)
  parser.add_argument("--no-faster-whisper", action='store_true', default=True,
            help="Use standard Whisper instead of faster-whisper (default: enabled for stability)")

  parser.add_argument("--translate", action='store_true', default=False,
            help="Translate to English")

  parser.add_argument("--no-fp16", action='store_true', default=False,
            help="Disable fp16 optimization")
  parser.add_argument("--stabilize-turns", default=0,
            help="Turns to stabilize result (default: 0 for real-time)", type=int)
  parser.add_argument("--min-duration", default=0.2,
            help="Min duration of audio to process (default: 0.2s for low latency)", type=float)
  parser.add_argument("--max-duration", default=1.5,
            help="Max duration of audio to process (default: 1.5s for low latency)", type=float)
  parser.add_argument("--keep-transcriptions", action='store_true', default=False,
            help="Keep all previous transcriptions")

  # args for input provider 'speech-recognition'
  parser.add_argument("--energy_threshold", default=300,
            help="Energy level for mic to detect", type=int)
  parser.add_argument("--record_timeout", default=0.3,
            help="How real time the recording is in seconds", type=float)
  parser.add_argument("--phrase_timeout", default=0.8,
            help="How much empty space between recordings before considering it a new line", type=float)

  # args for input provider 'pyaudio'
  parser.add_argument("--moving-window", default=10,
            help="Moving window duration in seconds", type=int)
  parser.add_argument("--chunk-size", default=512,
            help="Audio chunk size (default: 512 for low latency)", type=int)
  parser.add_argument("--realtime-mode", action='store_true', default=True,
            help="Enable real-time optimizations (default: enabled)")
  args = parser.parse_args()
  return args


class HUDText(QTextEdit):
  def __init__(self, font_size):
    super().__init__()

    self.setReadOnly(True)
    self.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
    self.setStyleSheet("""
      background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 rgba(20,20,20,0.8), 
                                        stop:1 rgba(40,40,40,0.8));
      color: #FFFFFF;
      border-radius: 15px;
      border: 1px solid rgba(255,255,255,0.3);
      padding: 10px;
      selection-background-color: rgba(30,144,255,0.5);
      selection-color: white;
    """)
    self.setLineWrapMode(QTextEdit.WidgetWidth)
    
    # 设置字体
    font = QFont("Arial", font_size)
    font.setWeight(QFont.Medium)
    self.setFont(font)
    
    # 设置文本格式
    self.document().setDefaultStyleSheet("""
      p { margin-bottom: 10px; line-height: 120%; }
      .current { color: #F8F8F8; }
      .previous { color: rgba(255,255,255,0.75); }
    """)
    
    self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
    
    # 设置文档边距
    document = self.document()
    document.setDocumentMargin(15)

  def mousePressEvent(self, event):
    event.ignore()

  def mouseMoveEvent(self, event):
    event.ignore()

  def mouseReleaseEvent(self, event):
    event.ignore()

class HUD(QMainWindow):
  max_width_percentage = 0.7  # 增大窗口宽度，避免文本换行过多
  max_height_percentage = 0.35  # 再增加高度以容纳更多文本
  max_lines = 6
  padding = 15
  corner_spacing = 20

  def __init__(self, font_size):
    super().__init__()

    # 设置窗口属性
    self.setWindowFlags(Qt.CustomizeWindowHint|Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.WindowDoesNotAcceptFocus)
    self.setAttribute(Qt.WA_TranslucentBackground)

    # 设置窗口透明度
    self.setWindowOpacity(1.0)

    # 设置中央窗口
    central_widget = QWidget()
    layout = QHBoxLayout(central_widget)
    layout.setContentsMargins(10, 10, 10, 10)

    self.text_widget = HUDText(font_size)
    self.text_widget.setParent(central_widget)
    layout.addWidget(self.text_widget)

    self.setCentralWidget(central_widget)

    # 限制窗口大小
    screen_geometry = QApplication.desktop().screenGeometry()
    max_width = int(self.max_width_percentage * screen_geometry.width())
    max_height = int(self.max_height_percentage * screen_geometry.height())
    self.setFixedWidth(max_width)
    self.setFixedHeight(max_height)
    
    # 将窗口放在屏幕底部中央
    self.move(int((screen_geometry.width() - max_width) / 2), 
              screen_geometry.height() - max_height - self.corner_spacing)

    # 定期更新文本的定时器
    self.update_text_timer = QTimer(self)
    self.update_text_timer.timeout.connect(self.updateTextWidget)
    self.update_text_timer.start(33)  # 约30fps的更新频率

    # 拖动窗口的变量
    self.old_pos = None
    
    # 上一次显示的文本
    self.last_displayed_text = ""
    
    # 初始测试文本
    global text_to_display
    with text_lock:
      text_to_display = "System audio caption window started\nStart playing audio..."
    
    print("HUD window created, initial text set")

  def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
      self.old_pos = event.globalPos()

  def mouseMoveEvent(self, event):
    if self.old_pos:
      delta = QPoint(event.globalPos() - self.old_pos)
      self.move(self.x() + delta.x(), self.y() + delta.y())
      self.old_pos = event.globalPos()

  def mouseReleaseEvent(self, event):
    if event.button() == Qt.LeftButton:
      self.old_pos = None

  def updateTextWidget(self):
    # 从全局变量获取当前文本
    global text_to_display
    with text_lock:
      current_text = text_to_display
    
    # 调试信息，显示当前文本
    if current_text:
      print(f"Current text_to_display: '{current_text[:30]}...' (len={len(current_text)})")
    else:
      print("Current text_to_display is empty")
    
    # 只在文本非空且与上次不同时更新，并且确保最小长度，避免显示过短的片段
    if current_text and current_text.strip() and current_text != self.last_displayed_text:
      try:
        # 处理文本，确保每句话换行显示
        formatted_text = self.format_text(current_text)
        
        # 使用HTML格式化文本
        html_text = self.format_text_html(formatted_text)
        
        # 更新显示文本
        self.text_widget.setHtml(html_text)
        
        # 记录显示的文本
        self.last_displayed_text = current_text
        
        # 自动滚动到底部
        vertical_scrollbar = self.text_widget.verticalScrollBar()
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())

        # 调试信息
        print(f"HUD text updated successfully, length: {len(current_text)}")
        
        # 强制重绘窗口
        self.text_widget.repaint()
      except Exception as e:
        print(f"Error updating caption window: {e}")
        import traceback
        traceback.print_exc()

  def format_text(self, text):
    # 处理文本，确保每句话都换行
    # 首先按原有的换行符分割
    paragraphs = text.split('\n')
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
      # 处理段落内的句子
      # 按句号、问号、感叹号等分割句子，保留分隔符
      sentences = []
      current_pos = 0
      for i, char in enumerate(paragraph):
        if char in '.!?。！？':
          if i+1 < len(paragraph) and paragraph[i+1] != ' ':
            # 如果句号后面没有空格，可能是缩写或小数点，不分割
            continue
          if i+1 < len(paragraph):
            sentences.append(paragraph[current_pos:i+2])
            current_pos = i+2
          else:
            sentences.append(paragraph[current_pos:i+1])
            current_pos = i+1
      
      # 添加最后一句（如果有）
      if current_pos < len(paragraph):
        sentences.append(paragraph[current_pos:])
      
      # 将处理后的句子添加到格式化段落
      if sentences:
        formatted_paragraphs.append('\n'.join(sentences))
      else:
        formatted_paragraphs.append(paragraph)
    
    # 将格式化的段落组合成最终文本
    return '\n\n'.join(formatted_paragraphs)
  
  def format_text_html(self, text):
    # 将文本转换为HTML格式，增强可读性
    lines = text.split('\n')
    html_parts = ['<html><body>']

    # 添加顶部边距
    html_parts.append('<div style="margin-top:5px;"></div>')

    for i, line in enumerate(lines):
      if line.strip():
        # 最后一行（当前正在转录的）使用较亮的颜色
        # 之前的行使用稍暗的颜色表示已完成
        if i == len(lines) - 1:
          # 当前正在转录的句子 - 使用动画效果减少跳跃感
          html_parts.append(f'<p class="current" style="line-height:130%; margin-bottom:8px; letter-spacing:0.5px; color:#F8F8F8; transition: all 0.3s ease-in-out; opacity: 1; transform: translateY(0);">{line}</p>')
        else:
          # 已完成的句子 - 稍暗但稳定
          html_parts.append(f'<p class="previous" style="line-height:130%; margin-bottom:8px; letter-spacing:0.5px; color:rgba(255,255,255,0.85); transition: all 0.3s ease-in-out; opacity: 0.9;">{line}</p>')

    html_parts.append('</body></html>')
    return ''.join(html_parts)

class AudioInputProvider:
  def list_input_devices(self):
    raise NotImplementedError

  def init_input_device(self, device_index):
    raise NotImplementedError

  def start_record(self):
    raise NotImplementedError

  def stop_record(self):
    raise NotImplementedError

  def phrase_cut_off(self, acc_data, new_data):
    raise NotImplementedError

class SystemAudioProvider(AudioInputProvider):
  def __init__(self, args, data_queue, sample_rate):
    self.audio = pyaudio.PyAudio()

    self.audio_format = pyaudio.paFloat32  # 改为Float32格式，与诊断工具一致
    self.audio_channels = 1  # Number of audio channels (1 for mono, 2 for stereo)
    self.sample_rate = sample_rate  # Sample rate (samples per second)
    self.sample_size = self.audio.get_sample_size(self.audio_format)
    self.audio_chunk = args.chunk_size

    self.moving_window = args.moving_window

    self.device_index = None
    self.stop_event = threading.Event()
    self.stream = None  # Add stream reference for proper cleanup

    self.data_queue = data_queue
    print(f"SystemAudioProvider initialized successfully, sample rate: {sample_rate}Hz, chunk size: {args.chunk_size}")

  def __del__(self):
    """Ensure PyAudio is properly terminated when object is destroyed"""
    try:
      if hasattr(self, 'audio') and self.audio:
        # Only terminate if not already terminated
        if hasattr(self.audio, '_pa'):
          self.audio.terminate()
          self.audio = None
    except Exception as e:
      print(f"Error terminating PyAudio: {e}")

  def list_input_devices(self):
    devices = []
    self.device_index_map = {}  # 映射列表索引到实际PyAudio设备索引
    try:
      print("Finding available audio input devices...")
      list_idx = 0
      for pyaudio_idx in range(self.audio.get_device_count()):
        device_info = self.audio.get_device_info_by_index(pyaudio_idx)
        # Only include devices that support input
        if device_info.get('maxInputChannels', 0) > 0:
          devices.append(device_info['name'])
          self.device_index_map[list_idx] = pyaudio_idx  # 保存映射关系
          print(f"Found input device {list_idx}: {device_info['name']} (PyAudio index: {pyaudio_idx})")
          list_idx += 1

      # If no input devices found, add a default option
      if not devices:
        print("No input devices found, using default device")
        devices.append("Default Input Device")
        self.device_index_map[0] = None
    except Exception as e:
      print(f"Error listing audio devices: {e}")
      devices.append("Default Input Device")
      self.device_index_map[0] = None

    return devices

  def init_input_device(self, device_list_index):
    # 将设备列表索引转换为实际的PyAudio设备索引
    if hasattr(self, 'device_index_map') and device_list_index in self.device_index_map:
      actual_device_index = self.device_index_map[device_list_index]
      print(f"Mapping device list index {device_list_index} to PyAudio index {actual_device_index}")
    else:
      actual_device_index = device_list_index
      print(f"No mapping found, using device index {device_list_index} directly")

    # Validate the device supports input
    try:
      print(f"Initializing audio device, PyAudio index: {actual_device_index}")
      if actual_device_index is not None:
        device_info = self.audio.get_device_info_by_index(actual_device_index)
        if device_info.get('maxInputChannels', 0) <= 0:
          print(f"Warning: Device {actual_device_index} does not support input, attempting to use default input device")
          actual_device_index = self.audio.get_default_input_device_info()['index']
    except Exception as e:
      print(f"Error with device {actual_device_index}: Using default device: {e}")
      actual_device_index = None

    self.device_index = actual_device_index
    print(f"Using input device index: {self.device_index}")

  def start_record(self):
    print("Starting SystemAudio recording thread...")
    self.stop_event.clear()

    self.record_thread = threading.Thread(target=self._record_audio)
    self.record_thread.daemon = True  # Make thread daemon so it exits when main program exits
    self.record_thread.start()
    print("SystemAudio recording thread started")

  def stop_record(self):
    try:
      print("Stopping SystemAudio recording...")
      self.stop_event.set()

      # Close stream if it exists
      if hasattr(self, 'stream') and self.stream:
        try:
          if self.stream.is_active():
            self.stream.stop_stream()
          self.stream.close()
          self.stream = None
        except Exception as e:
          print(f"Error closing audio stream: {e}")

      if hasattr(self, 'record_thread') and self.record_thread.is_alive():
        self.record_thread.join(timeout=2.0)  # Wait up to 2 seconds for thread to finish
        print("SystemAudio recording stopped")

      # Terminate PyAudio
      if hasattr(self, 'audio') and self.audio:
        try:
          self.audio.terminate()
          self.audio = None
        except Exception as e:
          print(f"Error terminating PyAudio: {e}")

    except Exception as e:
      print(f"Error stopping recording: {e}")

  def phrase_cut_off(self, acc_data, new_data):
    if (exceed := len(acc_data) + len(new_data) - self.sample_rate*self.moving_window) > 0:
      return exceed
    else:
      return 0

  def _record_audio(self):
    def stream_callback(in_data, frame_count, time_info, status):
      # Add small visual feedback that we're receiving audio
      data_size = len(in_data)
      if data_size > 0:
        # 音频数据有效，放入队列
        self.data_queue.put(in_data)
        # 视觉反馈，但限制打印频率
        print(".", end="", flush=True)
      else:
        print("x", end="", flush=True)  # 收到空数据时显示x

      # 返回None表示无输出数据，pyaudio.paContinue表示继续录制
      return (None, pyaudio.paContinue)

    try:
      # 尝试多次初始化音频流
      max_attempts = 3
      attempts = 0
      stream = None

      while attempts < max_attempts and not self.stop_event.is_set():
        attempts += 1
        try:
          # Open audio stream with the selected input device
          if self.device_index is None:
            # Use default input device if none specified
            print(f"Attempt {attempts}/{max_attempts}: Using default input device")
            stream = self.audio.open(
              format=self.audio_format,
              channels=self.audio_channels,
              rate=self.sample_rate,
              input=True,
              frames_per_buffer=self.audio_chunk,
              stream_callback=stream_callback,
            )
          else:
            # Use specified input device
            print(f"Attempt {attempts}/{max_attempts}: Using device index {self.device_index}")
            stream = self.audio.open(
              format=self.audio_format,
              channels=self.audio_channels,
              rate=self.sample_rate,
              input=True,
              input_device_index=self.device_index,
              frames_per_buffer=self.audio_chunk,
              stream_callback=stream_callback,
            )

          # 成功打开流
          print(f"Audio stream started, device index: {self.device_index}")
          break
        except Exception as e:
          print(f"Error opening audio stream (attempt {attempts}/{max_attempts}): {e}")
          if attempts < max_attempts:
            print("Retrying in 1 second...")
            time.sleep(1)
            if self.device_index is not None and attempts == max_attempts - 1:
              print("Trying with default device as last resort")
              self.device_index = None
          else:
            raise

      if not stream or not stream.is_active():
        print("CRITICAL ERROR: Failed to open an active audio stream")
        return

      # 直接测试音频捕获
      print("Testing system audio capture for 2 seconds...")
      test_start = time.time()
      while time.time() - test_start < 2.0 and not self.stop_event.is_set():
        if self.data_queue.qsize() > 0:
          print(f"\nSystem audio capture test successful! Queue size: {self.data_queue.qsize()}")
          break
        sleep(0.1)

      if self.data_queue.qsize() == 0:
        print("\nWARNING: No system audio data received during test. Check your BlackHole setup.")

      # Store stream reference for cleanup
      self.stream = stream

      # Keep the stream active until stop is requested
      while not self.stop_event.is_set() and stream.is_active():
        # 每隔一段时间报告一下队列大小
        if self.data_queue.qsize() > 0 and self.data_queue.qsize() % 20 == 0:
          print(f"\nAudio queue size: {self.data_queue.qsize()}")
        sleep(0.1)

      # Close the audio stream
      if stream:
        try:
          stream.stop_stream()
          stream.close()
          self.stream = None
          print("Audio stream closed")
        except Exception as e:
          print(f"Error closing stream: {e}")

    except Exception as e:
      print(f"Critical error in system audio recording: {e}")
      import traceback
      traceback.print_exc()
      # No automatic retry with default device, let the error bubble up

class SystemAudioTranscriber():
  n_context = 5
  max_transcription_history = 100

  def __init__(self, args):
    self.args = args
    self.language = args.language
    self.sample_rate = whisper.audio.SAMPLE_RATE
    # Use CPU by default for more compatibility, allow opt-in to GPU
    self.compute_device = "cpu"
    if torch.cuda.is_available():
      print("CUDA is available! To use GPU, restart the program without --no-faster-whisper flag")

    self.model_name = args.model

    # Thread safe Queue for passing data from the threaded recording callback.
    self.data_queue = Queue()
    self.transcribe_thread = None
    self.stop_event = threading.Event()

    # Use SystemAudioProvider for capturing system audio
    self.input_provider = SystemAudioProvider(args=self.args, data_queue=self.data_queue, sample_rate=self.sample_rate)

    print(f"Using SystemAudioProvider for system audio capture")
    print(f"Using {self.model_name} model")
    print(f"Computing on {self.compute_device}")

    self.init_input_device(args)

    print(f"Loading model {self.model_name}...")
    # Load / Download model
    start_time = time.time()
    try:
      if self.args.no_faster_whisper:
        self.audio_model = whisper.load_model(self.model_name, device=self.compute_device)
      else:
        self.audio_model = WhisperModel(self.model_name, device=self.compute_device)
      print(f"Model loaded in {time.time() - start_time:.2f} seconds")
    except Exception as e:
      print(f"Error loading model: {e}")
      raise

    # Cue the user that we're ready to go.
    print("System ready. Starting system audio transcription...\n")

  def init_input_device(self, args):
    device_index = None

    if args.input is not None:
      try:
        # 检查是否输入的是数字索引
        if args.input.isdigit():
          device_index = int(args.input)
          devices = self.input_provider.list_input_devices()
          if device_index < 0 or device_index >= len(devices):
            print(f"Warning: Device index {device_index} out of range, will list available devices")
            device_index = None
          else:
            print(f"Using specified device index: {device_index} ({devices[device_index]})")
        else:
          # 如果不是数字，尝试匹配设备名称
          for idx, name in enumerate(self.input_provider.list_input_devices()):
            if args.input.lower() in name.lower():  # 使用部分匹配而不是精确匹配
              device_index = idx
              print(f"Found matching device: {idx}. {name}")
              break
      except Exception as e:
        print(f"Error finding specified input device: {e}")
        device_index = None

    if device_index is None:
      try:
        # 打印可用音频设备列表
        print("Available input devices:")
        devices = list(self.input_provider.list_input_devices())
        for idx, name in enumerate(devices):
          print(f"{idx}. {name}")

        if args.input is None:
          # 选择所需输入设备的索引 - 优先查找BlackHole
          default_device = 0
          # 优先查找BlackHole设备
          for idx, name in enumerate(devices):
            if "BlackHole" in name or "blackhole" in name.lower():
              default_device = idx
              print(f"Found BlackHole device: {idx}. {name}")
              break
          # 如果没找到BlackHole，查找其他可能的虚拟音频设备
          if default_device == 0:
            for idx, name in enumerate(devices):
              if any(keyword in name.lower() for keyword in ["virtual", "loopback", "soundflower"]):
                default_device = idx
                print(f"Found virtual audio device: {idx}. {name}")
                break

          print(f"Default device will be {default_device}: {devices[default_device]} in 5 seconds...")
          print("Enter device number to override (or press Enter to use default):", end="", flush=True)

          # 设置超时读取输入
          import select
          import sys

          # 检查是否有用户输入，最多等待5秒
          ready, _, _ = select.select([sys.stdin], [], [], 5)
          if ready:
            user_input = sys.stdin.readline().strip()
            if user_input.isdigit() and 0 <= int(user_input) < len(devices):
              device_index = int(user_input)
              print(f"User selected device: {device_index}. {devices[device_index]}")
            else:
              if user_input:
                print(f"Invalid input '{user_input}', using default device")
              device_index = default_device
          else:
            print("\nNo input received, using default device")
            device_index = default_device
        else:
          print(f"Could not find device matching '{args.input}', please select from available devices")
          return self.init_input_device(argparse.Namespace(**{**vars(args), 'input': None}))  # 重新调用但清除input参数
      except Exception as e:
        print(f"Error in device selection: {e}")
        device_index = None  # 使用默认设备

    try:
      self.input_provider.init_input_device(device_index)
    except Exception as e:
      print(f"Critical error initializing input device: {e}")
      raise

  def start_transcribe_thread(self):
    if self.transcribe_thread is not None:
      print("Warning: Transcription thread already running")
      return

    self.transcribe_thread = threading.Thread(target=self.listen)
    self.transcribe_thread.daemon = True
    self.transcribe_thread.start()
    print("Transcription thread started")

  def stop_transcribe_thread(self):
    if self.transcribe_thread is None:
      return

    print("Stopping transcription thread...")
    self.stop_event.set()
    self.transcribe_thread.join(timeout=5.0)  # Wait up to 5 seconds
    print("Transcription thread stopped")

  def update_hud_text(self, text):
    # 更新全局文本变量
    global text_to_display
    with text_lock:
      # 确保是字符串且不为空
      if text is None:
        print("Warning: Attempted to update with None text, ignored")
        return

      if not isinstance(text, str):
        text = str(text)
        print(f"Warning: Non-string text converted to: {text}")

      # 去除多余空白字符但保留基本格式
      cleaned_text = ' '.join([line.strip() for line in text.split('\n')])

      # 确保文本非空
      if cleaned_text.strip():
        # 更新全局变量
        text_to_display = cleaned_text
        # 限制日志长度以避免刷屏
        preview = cleaned_text[:50] + "..." if len(cleaned_text) > 50 else cleaned_text
        print(f"Updated global text_to_display: '{preview}' (len={len(cleaned_text)})")

        # Note: UI updates are handled by the main thread timer, no need to force update here
      else:
        print("Warning: Attempted to update with empty text, ignored")

  def manage_caption_history(self, new_texts, caption_history, current_caption, last_complete_caption, max_lines=5):
    """
    智能管理字幕历史，防止跳跃，支持多行滚动显示
    返回: (updated_history, updated_current, updated_last_complete, display_text)
    """
    if not new_texts:
      return caption_history, current_caption, last_complete_caption, None

    # 获取最新的转录文本
    latest_text = new_texts[-1] if new_texts else ""
    latest_text = latest_text.strip()

    if not latest_text:
      return caption_history, current_caption, last_complete_caption, None

    # 总是添加新的转录结果到历史中（不管是否完整）
    if latest_text and latest_text != last_complete_caption:
      # 避免重复添加相同的文本
      if not caption_history or caption_history[-1] != latest_text:
        caption_history.append(latest_text)
        last_complete_caption = latest_text
        print(f"Added new caption: {latest_text}")

        # 保持最大行数限制，实现向上滚动效果
        if len(caption_history) > max_lines:
          caption_history = caption_history[-max_lines:]
          print(f"Caption history trimmed to {max_lines} lines")

    # 构建显示文本 - 显示所有历史记录
    display_lines = []
    for sentence in caption_history:
      if sentence.strip():
        display_lines.append(sentence.strip())

    # 生成最终显示文本
    display_text = '\n'.join(display_lines) if display_lines else None

    return caption_history, current_caption, last_complete_caption, display_text

  def listen(self):
    args = self.args
    transcription = []
    last_texts = []
    texts = []  # Initialize texts variable to prevent UnboundLocalError
    result = {'segments': []}  # Initialize result variable to prevent UnboundLocalError
    realtime_mode = args.realtime_mode

    # 字幕历史管理 - 防止跳跃
    caption_history = []  # 已完成的字幕句子
    current_caption = ""  # 当前正在转录的句子
    max_caption_lines = 5  # 最多显示的字幕行数
    last_complete_caption = ""  # 上次的完整字幕，用于检测新句子

    # 字幕显示稳定性控制
    last_transcription_result = ""  # 上次的转录结果
    last_result_display_time = 0  # 上次显示结果的时间
    result_display_duration = 5.0  # 转录结果显示持续时间（秒）- 增加到5秒，提高稳定性
    is_showing_result = False  # 是否正在显示转录结果

    try:
      print("Starting system audio recording...")
      self.input_provider.start_record()
      print("System audio recording started, waiting for audio data")

      if args.no_faster_whisper:
        import torch
        acc_audio_data = torch.zeros((0,), dtype=torch.float32, device=self.compute_device)
        last_transcription_time = time.time()
        last_audio_debug_time = time.time()

        # 确保启动时更新UI
        self.update_hud_text("🔊 正在监听系统音频...\n播放音频内容以开始转录")
      else:
        acc_audio_data = np.zeros((0,), dtype=np.float32)

        last_transcription_time = time.time()
        last_audio_debug_time = time.time()

        # 确保启动时更新UI
        self.update_hud_text("🔊 正在监听系统音频...\n播放音频内容以开始转录")

      while not self.stop_event.is_set():
        try:
          current_time = time.time()

          # 每10秒打印一次调试信息
          if current_time - last_audio_debug_time > 10:
            print(f"Transcription status: Cumulative audio length {len(acc_audio_data)/self.sample_rate:.2f} seconds")
            last_audio_debug_time = current_time

          # 获取音频数据
          try:
            # 安全地获取队列中的所有数据
            audio_data_list = []
            while not self.data_queue.empty():
              try:
                data = self.data_queue.get_nowait()
                audio_data_list.append(data)
              except:
                break

            audio_data = b''.join(audio_data_list)

            if len(audio_data_list) > 0:
              print(f"Detected {len(audio_data_list)} audio data packets")
              print(f"Received audio data: {len(audio_data)} bytes")

              # 转换音频数据 - 现在使用Float32格式
              if args.no_faster_whisper:
                # 对于标准whisper，转换为torch tensor
                audio_np = np.frombuffer(audio_data, dtype=np.float32)  # 直接使用float32，无需除法转换
                audio_tensor = torch.from_numpy(audio_np).to(self.compute_device)
                acc_audio_data = torch.cat([acc_audio_data, audio_tensor])
              else:
                # 对于faster-whisper，使用numpy
                audio_np = np.frombuffer(audio_data, dtype=np.float32)  # 直接使用float32，无需除法转换
                acc_audio_data = np.concatenate([acc_audio_data, audio_np])

              print(f"Audio data processed, current cumulative {len(acc_audio_data)/self.sample_rate:.2f} seconds")

          except Exception as e:
            print(f"Error processing audio data: {e}")
            continue

          # 检查是否需要转录
          should_transcribe = False

          # 在实时模式下，减小所需的最小音频数据量以降低延迟
          min_audio_length = 0.2 if realtime_mode else 0.5  # 秒 - 减少延迟

          if len(acc_audio_data) >= min_audio_length * self.sample_rate:
            print(f"Audio data sufficient ({len(acc_audio_data)/self.sample_rate:.2f} seconds), starting transcription...")
            should_transcribe = True
          # 如果音频数据不够长，但已经等待了足够长的时间，也进行转录 - 减少超时时间
          elif current_time - last_transcription_time >= 1.0 and len(acc_audio_data) > 0:
            print(f"Timeout reached, processing {len(acc_audio_data)/self.sample_rate:.2f} seconds of audio")
            should_transcribe = True

          if should_transcribe:
            # 检查是否是静音 - 调整阈值适应Float32格式
            if args.no_faster_whisper:
              audio_max = torch.max(torch.abs(acc_audio_data)).item()
            else:
              audio_max = np.max(np.abs(acc_audio_data))

            if audio_max < 0.005:  # 降低阈值，适应Float32格式的音频数据
              print(f"Audio appears to be silent (max: {audio_max:.6f}), skipping transcription")
              if args.no_faster_whisper:
                acc_audio_data = torch.zeros((0,), dtype=torch.float32, device=self.compute_device)
              else:
                acc_audio_data = np.array([], dtype=np.float32)
              continue

            print(f"Starting transcription of {len(acc_audio_data)/self.sample_rate:.2f} seconds of audio...")
            print(f"Audio max amplitude: {audio_max:.6f}")
            print("Proceeding with transcription...")

            # 移除"正在转录"状态显示，避免闪烁
            # 直接等待转录结果，保持当前字幕稳定显示

            try:
              # 执行转录
              print("Calling audio_model.transcribe...")

              if args.no_faster_whisper:
                # 标准whisper转录
                result = self.audio_model.transcribe(
                  acc_audio_data.cpu().numpy(),
                  language=self.language,
                  task="translate" if args.translate else "transcribe",
                  fp16=not args.no_fp16
                )
                texts = [result['text']]
              else:
                # faster-whisper转录
                segments, info = self.audio_model.transcribe(
                  acc_audio_data,
                  language=self.language,
                  task="translate" if args.translate else "transcribe",
                  beam_size=1,
                  best_of=1,
                  temperature=0.0
                )
                texts = [segment.text for segment in segments]

              print("Transcription call completed successfully")
              print("Transcription completed, processing result...")

              if texts and any(text.strip() for text in texts):
                # 有有效的转录结果
                combined_text = ' '.join(texts).strip()
                print(f"Transcription result: '{combined_text}'")

                # 使用字幕历史管理
                caption_history, current_caption, last_complete_caption, display_text = self.manage_caption_history(
                  [combined_text], caption_history, current_caption, last_complete_caption, max_caption_lines
                )

                if display_text:
                  self.update_hud_text(display_text)

                  # 设置结果显示状态 - 延长显示时间
                  last_transcription_result = display_text
                  last_result_display_time = current_time
                  is_showing_result = True
                  print(f"Showing result for {result_display_duration} seconds")
              else:
                print("No speech detected, clearing audio buffer")

            except Exception as e:
              print(f"Error during transcription: {e}")
              import traceback
              traceback.print_exc()

            # 清空累积的音频数据
            if args.no_faster_whisper:
              acc_audio_data = torch.zeros((0,), dtype=torch.float32, device=self.compute_device)
            else:
              acc_audio_data = np.array([], dtype=np.float32)

            last_transcription_time = current_time

          # 检查是否需要清除显示的结果
          if is_showing_result and current_time - last_result_display_time >= result_display_duration:
            print("Result display time expired, allowing new transcription...")
            is_showing_result = False
            # 保持字幕历史显示，不回到"等待"状态
            # 如果有字幕历史，继续显示最后的字幕；如果没有，显示等待状态
            if caption_history:
              # 重新显示字幕历史，保持稳定显示
              display_text = '\n'.join(caption_history[-max_caption_lines:])
              self.update_hud_text(display_text)
              print(f"Maintaining caption history display: {len(caption_history)} lines")
            elif not current_caption:
              self.update_hud_text("🔊 正在监听系统音频...\n播放音频内容以开始转录")

          # 短暂休眠以避免过度占用CPU
          sleep(0.05)

        except Exception as e:
          print(f"Error in transcription loop: {e}")
          import traceback
          traceback.print_exc()
          sleep(1)  # 出错时稍长的休眠

    except Exception as e:
      print(f"Critical error in transcription thread: {e}")
      import traceback
      traceback.print_exc()
    finally:
      # 始终清理资源
      try:
        self.input_provider.stop_record()
      except Exception as e:
        print(f"Error stopping recording: {e}")

    return transcription

def main():
  args = parse_args()

  try:
    # 首先在主线程创建QApplication
    app = QApplication([])

    print("Creating system audio caption display window...")

    # 创建HUD窗口
    hud_window = HUD(font_size=args.font_size)
    hud_window.show()

    # 强制窗口显示在前台
    hud_window.raise_()
    hud_window.activateWindow()

    print("System audio caption window displayed")

    # 全局变量初始内容
    global text_to_display
    with text_lock:
      text_to_display = "🔊 系统音频转录已启动\n播放音频内容以开始转录..."

    print("Creating system audio transcriber...")

    # 创建转录器
    transcriber = SystemAudioTranscriber(args)

    print("Starting system audio transcription thread...")

    # 启动转录线程
    transcriber.start_transcribe_thread()

    # 设置信号处理
    def handle_signal(sig, frame):
      print("\nReceived interrupt signal, shutting down...")
      transcriber.stop_transcribe_thread()
      app.quit()
    signal.signal(signal.SIGINT, handle_signal)

    print("Starting UI event loop...")

    # 运行事件循环
    app.exec()

    # 停止转录线程
    transcriber.stop_transcribe_thread()

  except KeyboardInterrupt:
    print("\nProgram interrupted by user. Exiting...")
  except Exception as e:
    print(f"Critical error in main function: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
  main()
