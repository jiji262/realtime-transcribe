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
  parser = argparse.ArgumentParser()
  parser.add_argument("--model", default="tiny", help="Model to use",
            choices=["tiny", "base", "small", "medium", "large", "tiny.en", "base.en", "small.en", "medium.en", "large-v3"])
  parser.add_argument("--input", default=None,
            help="Audio input device (can be a device index or partial device name).", type=str)
  parser.add_argument("--input-provider", default="pyaudio",
            choices=["pyaudio", "speech-recognition"],
            help="Default input provider.", type=str)
  parser.add_argument("--no-faster-whisper", action='store_true', default=False,
            help="Disable faster whisper.")

  parser.add_argument("--language", default=None,
            help="Default language.", type=str)
  parser.add_argument("--translate", action='store_true', default=False,
            help="Translate to English.")

  parser.add_argument("--no-fp16", action='store_true', default=False,
            help="Disable fp16.")
  parser.add_argument("--stabilize-turns", default=1,
            help="Turns to stabilize result (before discarding audio record). 0 means never.", type=int)
  parser.add_argument("--min-duration", default=2.0,
            help="Min duration of audio record to keep.", type=float)
  parser.add_argument("--max-duration", default=10.0,
            help="Max duration of audio record to keep.", type=float)
  parser.add_argument("--keep-transcriptions", action='store_true', default=False,
            help="Keep all previous transcriptions")

  parser.add_argument("--font-size", default=30,
            help="Font size of HUD.", type=int)

  # args for input provider 'speech-recognition'
  parser.add_argument("--energy_threshold", default=300,
            help="Energy level for mic to detect.", type=int)
  parser.add_argument("--record_timeout", default=0.3, 
            help="How real time the recording is in seconds.", type=float)
  parser.add_argument("--phrase_timeout", default=0.8, 
            help="How much empty space between recordings before we "
               "consider it a new line in the transcription.", type=float)

  # args for input provider 'pyaudio'
  parser.add_argument("--moving-window", default=10, 
            help="Moving window duration in seconds for transription.", type=int)
  parser.add_argument("--chunk-size", default=1024, 
            help="Audio chunk size for pyaudio.", type=int)
  parser.add_argument("--realtime-mode", action='store_true', default=False,
            help="Enable optimizations for real-time display")
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
      text_to_display = "Caption window started\nStart speaking..."
    
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
    paragraphs = text.split('\n\n')
    html_parts = ['<html><body>']
    
    # 添加顶部边距
    html_parts.append('<div style="margin-top:5px;"></div>')
    
    for paragraph in paragraphs:
      lines = paragraph.split('\n')
      for i, line in enumerate(lines):
        if line.strip():
          # 当前行使用current类，较亮
          # 增加行高和底部边距，提高可读性
          html_parts.append(f'<p class="current" style="line-height:130%; margin-bottom:8px; letter-spacing:0.5px;">{line}</p>')
      
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

class SpeechRecognitionAudioProvider(AudioInputProvider):
  def __init__(self, args, data_queue, sample_rate):
    self.sample_rate = sample_rate
    self.energy_threshold = args.energy_threshold
    self.record_timeout = args.record_timeout
    self.phrase_timeout = args.phrase_timeout

    self.data_queue = data_queue
    self.stop_listening = None

  def list_input_devices(self):
    try:
      devices = sr.Microphone.list_microphone_names()
      print(f"Detected {len(devices)} microphone devices")
      return devices
    except Exception as e:
      print(f"Error listing microphone devices: {e}")
      return ["Default Microphone"]

  def init_input_device(self, device_index):
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    try:
      print(f"Initializing microphone, device index: {device_index}")
      self.recorder = sr.Recognizer()
      self.recorder.energy_threshold = self.energy_threshold
      # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
      self.recorder.dynamic_energy_threshold = False
      print(f"Energy threshold set to: {self.energy_threshold}")

      # Try to create the microphone with the given device index
      try:
        print(f"Attempting to initialize microphone with device index {device_index}")
        self.source = sr.Microphone(sample_rate=self.sample_rate, device_index=device_index)
        print(f"Microphone initialized successfully, device index: {device_index}")
      except Exception as e:
        print(f"Failed to initialize microphone with device index {device_index}: {e}")
        print("Attempting to use default microphone")
        self.source = sr.Microphone(sample_rate=self.sample_rate)

      # Test if the microphone works
      try:
        print("Testing microphone functionality...")
        with self.source:
          self.recorder.adjust_for_ambient_noise(self.source)
          print("Microphone test successful, ambient noise adjusted")
      except Exception as e:
        print(f"Error adjusting ambient noise: {e}")
        # Try to create a default microphone instead
        print("Attempting to use alternative method to initialize default microphone")
        self.source = sr.Microphone(sample_rate=self.sample_rate)
        with self.source:
          print("Using default microphone instead")
    
    except Exception as e:
      print(f"Critical SpeechRecognition error: {e}")
      import traceback
      traceback.print_exc()
      raise

  def start_record(self):
    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    try:
      print(f"Starting recording, timeout: {self.record_timeout} seconds")
      self.stop_listening = self.recorder.listen_in_background(self.source, self.record_callback, phrase_time_limit=self.record_timeout)
      self.phrase_time = None
      print("Recording started successfully, starting to listen to microphone")
    except Exception as e:
      print(f"Recording start failed: {e}")
      import traceback
      traceback.print_exc()
      raise

  def stop_record(self):
    if self.stop_listening is None:
      print("Warning: Recording not started")
      return

    try:
      self.stop_listening(True)
      print("Recording stopped successfully")
    except Exception as e:
      print(f"Error stopping recording: {e}")

    if hasattr(self, 'phrase_time'):
      del self.phrase_time

  def phrase_cut_off(self, acc_data, new_data):
    now = datetime.now()

    # If enough time has passed between recordings, consider the phrase complete.
    # Clear the current working audio buffer to start over with the new data.
    if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.phrase_timeout):
      # This is the last time we received new audio data from the queue.
      self.phrase_time = now # should set after the transcription is done
      return len(acc_data)
    else:
      return 0

  def record_callback(self, _, audio: sr.AudioData) -> None:
    """
    Threaded callback function to receive audio data when recordings finish.
    audio: An AudioData containing the recorded bytes.
    """
    # Grab the raw bytes and push it into the thread safe queue.
    try:
      data = audio.get_raw_data()
      data_size = len(data)
      if data_size > 0:
        self.data_queue.put(data)
        print(f"Received audio data: {data_size} bytes")
      else:
        print("Warning: Received empty audio data")
      # Print a small indicator that data was received
      print(".", end="", flush=True)
    except Exception as e:
      print(f"Error in recording callback: {e}")

class PyAudioProvider(AudioInputProvider):
  def __init__(self, args, data_queue, sample_rate):
    self.audio = pyaudio.PyAudio()

    self.audio_format = pyaudio.paInt16  # Format of the audio samples
    self.audio_channels = 1  # Number of audio channels (1 for mono, 2 for stereo)
    self.sample_rate = sample_rate  # Sample rate (samples per second)
    self.sample_size = self.audio.get_sample_size(self.audio_format)
    self.audio_chunk = args.chunk_size

    self.moving_window = args.moving_window

    self.device_index = None
    self.stop_event = threading.Event()
    self.stream = None  # Add stream reference for proper cleanup

    self.data_queue = data_queue
    print(f"PyAudio initialized successfully, sample rate: {sample_rate}Hz, chunk size: {args.chunk_size}")

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
    try:
      print("Finding available audio input devices...")
      for idx in range(self.audio.get_device_count()):
        device_info = self.audio.get_device_info_by_index(idx)
        # Only include devices that support input
        if device_info.get('maxInputChannels', 0) > 0:
          devices.append(device_info['name'])
          print(f"Found input device {idx}: {device_info['name']}")
      
      # If no input devices found, add a default option
      if not devices:
        print("No input devices found, using default device")
        devices.append("Default Input Device")
    except Exception as e:
      print(f"Error listing audio devices: {e}")
      devices.append("Default Input Device")
    
    return devices

  def init_input_device(self, device_index):
    # Validate the device supports input
    try:
      print(f"Initializing audio device, index: {device_index}")
      device_info = self.audio.get_device_info_by_index(device_index)
      if device_info.get('maxInputChannels', 0) <= 0:
        print(f"Warning: Device {device_index} does not support input, attempting to use default input device")
        device_index = self.audio.get_default_input_device_info()['index']
    except Exception as e:
      print(f"Error with device {device_index}: Using default device: {e}")
      device_index = None
    
    self.device_index = device_index
    print(f"Using input device index: {self.device_index}")

  def start_record(self):
    print("Starting PyAudio recording thread...")
    self.stop_event.clear()

    self.record_thread = threading.Thread(target=self._record_audio)
    self.record_thread.daemon = True  # Make thread daemon so it exits when main program exits
    self.record_thread.start()
    print("PyAudio recording thread started")

  def stop_record(self):
    try:
      print("Stopping PyAudio recording...")
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
        print("PyAudio recording stopped")

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
      print("Testing audio capture for 2 seconds...")
      test_start = time.time()
      while time.time() - test_start < 2.0 and not self.stop_event.is_set():
        if self.data_queue.qsize() > 0:
          print(f"\nAudio capture test successful! Queue size: {self.data_queue.qsize()}")
          break
        sleep(0.1)
      
      if self.data_queue.qsize() == 0:
        print("\nWARNING: No audio data received during test. Check your microphone.")
      
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
      print(f"Critical error in audio recording: {e}")
      import traceback
      traceback.print_exc()
      # No automatic retry with default device, let the error bubble up

class Transcriber():
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

    if args.input_provider == "speech-recognition":
      self.input_provider = SpeechRecognitionAudioProvider(args=self.args, data_queue=self.data_queue, sample_rate=self.sample_rate)
    elif args.input_provider == "pyaudio":
      self.input_provider = PyAudioProvider(args=self.args, data_queue=self.data_queue, sample_rate=self.sample_rate)

    print(f"Using {args.input_provider} as input provider")
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
    print("System ready. Starting transcription...\n")

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
          # 选择所需输入设备的索引
          default_device = 0
          # 查找名称中带有"mic"的第一个设备
          for idx, name in enumerate(devices):
            if "mic" in name.lower() or "microphone" in name.lower():
              default_device = idx
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

  def listen(self):
    args = self.args
    transcription = []
    last_texts = []
    texts = []  # Initialize texts variable to prevent UnboundLocalError
    result = {'segments': []}  # Initialize result variable to prevent UnboundLocalError
    realtime_mode = args.realtime_mode
    
    # 添加稳定显示相关变量
    stable_text = ""
    text_stability_count = 0
    min_stability_count = 2  # 至少需要多少次相同结果才更新显示
    last_shown_texts = []
    last_displayed_text_length = 0  # 跟踪上次显示的文本长度
    min_text_change = 3  # 最小文本变化量，小于此值不更新显示

    try:
      print("Starting recording...")
      self.input_provider.start_record()
      print("Recording started, waiting for audio data")

      if args.no_faster_whisper:
        acc_audio_data = torch.zeros((0,), dtype=torch.float32, device=self.compute_device)
        last_transcription_time = time.time()
        last_update_time = time.time()
        last_audio_debug_time = time.time()
        empty_queue_count = 0
        
        # 确保启动时更新UI
        self.update_hud_text("Listening...\nSay something to test")
      else:
        acc_audio_data = np.zeros((0,), dtype=np.float32)
        
        last_transcription_time = time.time()
        last_update_time = time.time()
        last_audio_debug_time = time.time()
        empty_queue_count = 0
        
        # 确保启动时更新UI
        self.update_hud_text("Listening...\nSay something to test")
        
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

            if len(audio_data) > 0:
              print(f"Received audio data: {len(audio_data)} bytes")
              empty_queue_count = 0
            else:
              empty_queue_count += 1
              if empty_queue_count % 100 == 0:
                print(f"Warning: Continued {empty_queue_count} times without receiving audio data")
                # Don't reinitialize automatically as it can cause crashes
                # if empty_queue_count >= 200:
                #   print("Attempting to reinitialize microphone...")
                #   self.input_provider.stop_record()
                #   time.sleep(1)
                #   self.input_provider.start_record()
                #   empty_queue_count = 0
          except Exception as e:
            print(f"Error getting audio data: {e}")
            sleep(0.05)
            continue

          # 即使没有新音频数据，也要定期尝试转录当前累积的音频
          if len(audio_data) == 0:
            # 如果已经有一定量的音频数据且经过了足够的时间
            if len(acc_audio_data) > 0 and current_time - last_transcription_time > 0.5:
              print(f"No new data, but processing existing {len(acc_audio_data)/self.sample_rate:.2f} seconds of audio")
              # 继续处理现有数据
            else:
              sleep(0.05)
            continue

          # 转换音频格式
          try:
            # Convert in-ram buffer to something the model can use directly without needing a temp file.
            # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
            # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            if args.no_faster_whisper:
              audio_torch = torch.from_numpy(audio_np).to(device=self.compute_device)
              acc_audio_data = torch.hstack([acc_audio_data, audio_torch])
            else:
              acc_audio_data = np.hstack([acc_audio_data, audio_np])

            print(f"Audio data processed, current cumulative {len(acc_audio_data)/self.sample_rate:.2f} seconds")
          except Exception as e:
            print(f"Error processing audio data: {e}")
            continue

          # Apply phrase cut off after accumulating data
          if args.stabilize_turns <= 0:
            phrase_cut_off = self.input_provider.phrase_cut_off(acc_audio_data, audio_data)
            if phrase_cut_off > 0:
              acc_audio_data = acc_audio_data[phrase_cut_off:]
              print(f"Applied phrase cut off: {phrase_cut_off} samples, remaining: {len(acc_audio_data)/self.sample_rate:.2f} seconds")

            # 在实时模式下，减小所需的最小音频数据量
            min_audio_length = 0.3 if realtime_mode else 1.0  # 秒

            # 如果音频数据太少，就不处理，除非已经过去太长时间
            if len(acc_audio_data) < self.sample_rate * min_audio_length:
              if current_time - last_transcription_time < 1.0:
                print(f"Audio data too short ({len(acc_audio_data)/self.sample_rate:.2f} seconds), waiting for more data...")
                continue
              else:
                print(f"Timeout reached, processing {len(acc_audio_data)/self.sample_rate:.2f} seconds of audio")
            else:
              print(f"Audio data sufficient ({len(acc_audio_data)/self.sample_rate:.2f} seconds), starting transcription...")
            
            # 更新最后转录时间
            last_transcription_time = current_time
            
            # 进行转录
            try:
              print(f"Starting transcription of {len(acc_audio_data)/self.sample_rate:.2f} seconds of audio...")
              # 显示正在转录的提示
              if current_time - last_update_time > 2.0:  # 避免频繁更新
                self.update_hud_text("正在转录您的语音...\n请稍候")
                last_update_time = current_time

              # 确保音频数据不为空
              if len(acc_audio_data) == 0:
                print("Warning: No audio data to transcribe")
                continue

              # 添加音频数据调试信息
              print(f"Audio data type: {type(acc_audio_data)}")

              # 处理不同类型的音频数据
              if hasattr(acc_audio_data, 'numpy'):
                # 如果是Tensor，转换为numpy
                audio_np = acc_audio_data.numpy().astype(np.float32)
                print("Converted Tensor to numpy array")
              elif isinstance(acc_audio_data, bytes):
                # 如果是bytes，使用frombuffer
                audio_np = np.frombuffer(acc_audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                print("Converted bytes to numpy array")
              elif isinstance(acc_audio_data, np.ndarray):
                # 如果已经是numpy数组
                audio_np = acc_audio_data.astype(np.float32)
                print("Audio data is already numpy array")
              else:
                # 尝试直接转换
                audio_np = np.array(acc_audio_data, dtype=np.float32)
                print(f"Converted {type(acc_audio_data)} to numpy array")

              audio_max = np.max(np.abs(audio_np))
              audio_rms = np.sqrt(np.mean(audio_np**2))
              print(f"Audio stats: max={audio_max:.4f}, rms={audio_rms:.4f}, length={len(audio_np)} samples")

              # 检查是否是静音
              if audio_max < 0.001:  # 非常小的阈值
                print("Warning: Audio appears to be silent (max amplitude < 0.001)")
              elif audio_rms < 0.0001:
                print("Warning: Audio appears to be very quiet (RMS < 0.0001)")

              params = {}
              # 在实时模式下设置更多优化参数
              if realtime_mode:
                if args.no_faster_whisper:
                  # Standard Whisper's real-time mode optimization
                  params['beam_size'] = 1
                  params['best_of'] = 1
                else:
                  # faster_whisper's real-time mode optimization
                  params['beam_size'] = 1
                  params['best_of'] = 1
                  params['temperature'] = [0.0]
              
              if args.no_faster_whisper and not args.no_fp16 and (self.compute_device == "cuda"):
                params['fp16'] = True

              if args.translate:
                params['task'] = 'translate'

              # Read the transcription.
              # 确保传递给Whisper的是正确的数据格式
              if hasattr(acc_audio_data, 'numpy'):
                # 如果是Tensor，转换为numpy
                audio_for_whisper = acc_audio_data.numpy()
              elif isinstance(acc_audio_data, np.ndarray):
                # 如果已经是numpy数组
                audio_for_whisper = acc_audio_data
              else:
                # 如果是bytes，保持原样
                audio_for_whisper = acc_audio_data

              result = self.audio_model.transcribe(
                audio_for_whisper,
                condition_on_previous_text=False,
                language=self.language,
                initial_prompt='\n'.join(transcription[-self.n_context:]),
                **params,
              )
              
              print("Transcription completed, processing result...")
              print(f"Result type: {type(result)}")
              
              if not args.no_faster_whisper:
                # 处理faster_whisper的结果
                segments, info = result
                result = { 'segments': [] }
                for seg in segments:
                  result['segments'].append({
                    'text': seg.text,
                    'start': seg.start,
                    'end': seg.end,
                  })
              else:
                # 标准whisper模式的结果处理
                print(f"Standard whisper result keys: {result.keys()}")
                
                # 确保结果包含segments
                if 'segments' not in result:
                  print("Warning: No 'segments' key in standard whisper result")
                  # 尝试从text中提取
                  if 'text' in result:
                    print(f"Found 'text' in result: {result['text']}")
                    # 直接使用text创建一个虚拟segment
                    result['segments'] = [{
                      'text': result['text'],
                      'start': 0,
                      'end': len(acc_audio_data)/self.sample_rate
                    }]
                  else:
                    print("ERROR: Could not find text in result")
                    result['segments'] = []
              
              # 检查segments是否为空
              if not result.get('segments'):
                print("Warning: Empty segments list in result")
                result['segments'] = []

              # 无论使用哪种模式，都统一提取texts
              texts = []
              for segment in result['segments']:
                # 打印调试信息
                print(f"Processing segment: {segment}")
                if 'text' in segment:
                  text = segment['text'].strip()
                  if text:  # 只添加非空文本
                    texts.append(text)

              if texts:
                print(f"Extracted texts count: {len(texts)}")
                print(f"Transcription result: {texts}")
              else:
                print("Warning: No transcription text extracted, possibly no speech in audio")
                
                # 如果没有提取到文本，但原始结果中有text字段，直接使用它
                if args.no_faster_whisper and isinstance(result, dict) and 'text' in result:
                  text = result['text'].strip()
                  if text:
                    texts = [text]
                    print(f"Using fallback text from result: {text}")
            except Exception as e:
              print(f"Error in transcription process: {e}")
              import traceback
              traceback.print_exc()
              sleep(0.3)
              continue

            # 即使只有部分转录结果也立即更新UI
            if texts:
              # 使用文本稳定性检查
              current_result = '\n'.join(texts)
              
              # 检查结果是否有效
              if current_result.strip():
                # 检查文本稳定性
                if current_result == stable_text:
                  text_stability_count += 1
                else:
                  stable_text = current_result
                  text_stability_count = 1
                
                # 根据稳定性决定是否更新UI
                should_update = False
                
                # 实时模式下降低稳定性要求，提高响应速度
                required_stability = 1 if realtime_mode else min_stability_count
                
                # 如果同样的文本多次出现，或者已经很长时间没更新，则更新
                if (text_stability_count >= required_stability) or (current_time - last_update_time > 0.8):
                  should_update = True
                
                # 对于新句子，检查是否有足够的新内容
                if texts != last_shown_texts and len(current_result) > last_displayed_text_length + min_text_change:
                  should_update = True

                # 在实时模式下，更积极地更新UI
                if realtime_mode and texts:
                  should_update = True

                if should_update:
                  # 直接调用更新，确保UI线程处理
                  print(f"Updating HUD with text: {current_result[:50]}..." if len(current_result) > 50 else current_result)
                  self.update_hud_text(current_result)
                  last_update_time = current_time
                  last_shown_texts = texts.copy()
                  last_displayed_text_length = len(current_result)  # 更新已显示文本长度记录
              else:
                # 如果没有文本但有有效的音频数据，显示正在处理的提示
                if len(acc_audio_data)/self.sample_rate > 1.0:  # 只有当有至少1秒的音频时才更新
                  if current_time - last_update_time > 3.0:  # 每3秒更新一次反馈
                    print("Updating HUD with listening prompt")
                    self.update_hud_text("正在听您说话...\n请继续说话")
                    last_update_time = current_time
                print("Warning: No transcription texts available")

          if args.stabilize_turns > 0:
            if len(texts) == 0 and len(acc_audio_data)/self.sample_rate > args.max_duration:
              cut_off = int(len(acc_audio_data) - args.min_duration*self.sample_rate)
              acc_audio_data = acc_audio_data[cut_off:]

            pos = 0
            while pos < min(len(last_texts), len(texts))-args.stabilize_turns:
              if last_texts[pos] != texts[pos]:
                break
              pos += 1

            if pos <= 0 and len(texts) > 1:
              pos = 0
              while len(acc_audio_data)/self.sample_rate - result['segments'][pos]['end'] > args.max_duration:
                pos += 1

            if pos > 0:
              seg = result['segments'][pos-1]
              cut_off = int(seg['end']*self.sample_rate)
              cut_off = min(cut_off, int(len(acc_audio_data)-args.min_duration*self.sample_rate))
              cut_off = max(0, cut_off)
              acc_audio_data = acc_audio_data[cut_off:]
              texts = texts[pos:]

              transcription += last_texts[:pos]
          else:
            if phrase_cut_off > 0:
              transcription += last_texts

          if not args.keep_transcriptions:
            transcription = transcription[-self.max_transcription_history:]

          last_texts = texts

          # 清空控制台并重新打印更新的转录
          os.system('cls' if os.name=='nt' else 'clear')
          for line in transcription:
            print(line)
          for seg in result['segments']:
            print('%.2f' % seg['start'], '->', '%.2f' % seg['end'], seg['text'])
            # 刷新标准输出
          print('', end='', flush=True)
          
        except KeyboardInterrupt:
          break
        except Exception as e:
          print(f"Error in transcription loop: {e}")
          import traceback
          traceback.print_exc()
          sleep(0.3)
          continue

      # 最终结果
      transcription += last_texts

      print("\n\nFinal Transcription:")
      for line in transcription:
        print(line)

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
    
    print("Creating caption display window...")
    
    # 创建HUD窗口
    hud_window = HUD(font_size=args.font_size)
    hud_window.show()
    
    # 强制窗口显示在前台
    hud_window.raise_()
    hud_window.activateWindow()
    
    print("Caption window displayed")
    
    # 全局变量初始内容
    global text_to_display
    with text_lock:
      text_to_display = "Caption system started\nInitializing transcriber..."
    
    print("Creating transcriber...")
    
    # 创建转录器
    transcriber = Transcriber(args)
    
    print("Starting transcription thread...")
    
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