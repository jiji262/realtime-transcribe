#!/usr/bin/env python3
"""
简化版本的实时转录测试程序
用于测试基本功能和避免段错误
"""

import sys
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import pyaudio
import faster_whisper

class SimpleHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Transcription Test")
        self.setGeometry(100, 100, 600, 200)
        
        # 创建文本显示区域
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Arial", 14))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 2px solid #333;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        self.setCentralWidget(self.text_edit)
        
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def update_text(self, text):
        """更新显示的文本"""
        self.text_edit.setPlainText(text)

class SimpleTranscriber:
    def __init__(self):
        self.model = None
        self.audio_stream = None
        self.is_recording = False
        
    def load_model(self):
        """加载Whisper模型"""
        print("Loading Whisper model...")
        try:
            self.model = faster_whisper.WhisperModel("tiny.en", device="cpu")
            print("Model loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def start_audio(self):
        """开始音频录制"""
        try:
            self.audio = pyaudio.PyAudio()
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            self.is_recording = True
            print("Audio recording started")
            return True
        except Exception as e:
            print(f"Error starting audio: {e}")
            return False
    
    def record_and_transcribe(self, duration=2.0):
        """录制音频并转录"""
        if not self.is_recording or not self.model:
            return ""
        
        try:
            # 录制音频
            frames = []
            chunk_size = 1024
            sample_rate = 16000
            total_frames = int(sample_rate * duration / chunk_size)
            
            print(f"Recording {duration} seconds of audio...")
            for _ in range(total_frames):
                data = self.audio_stream.read(chunk_size)
                frames.append(data)
            
            # 转换为numpy数组
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            audio_data = audio_data.astype(np.float32) / 32768.0
            
            print(f"Audio recorded: {len(audio_data)} samples")
            
            # 转录
            print("Transcribing...")
            segments, info = self.model.transcribe(audio_data, language="en")
            
            # 提取文本
            texts = []
            for segment in segments:
                if segment.text.strip():
                    texts.append(segment.text.strip())
            
            result = " ".join(texts) if texts else ""
            print(f"Transcription result: '{result}'")
            return result
            
        except Exception as e:
            print(f"Error in transcription: {e}")
            return ""
    
    def stop_audio(self):
        """停止音频录制"""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        self.is_recording = False
        print("Audio recording stopped")

def main():
    app = QApplication(sys.argv)
    
    # 创建HUD窗口
    hud = SimpleHUD()
    hud.show()
    hud.update_text("Initializing...")
    
    # 创建转录器
    transcriber = SimpleTranscriber()
    
    # 加载模型
    if not transcriber.load_model():
        hud.update_text("Failed to load model")
        return
    
    # 开始音频录制
    if not transcriber.start_audio():
        hud.update_text("Failed to start audio")
        return
    
    hud.update_text("Ready! Recording will start in 3 seconds...")
    
    # 创建定时器进行周期性转录
    def transcribe_cycle():
        try:
            result = transcriber.record_and_transcribe(2.0)
            if result:
                hud.update_text(f"Transcription: {result}")
            else:
                hud.update_text("Listening... (no speech detected)")
        except Exception as e:
            print(f"Error in transcribe cycle: {e}")
            hud.update_text(f"Error: {e}")
    
    # 设置定时器
    timer = QTimer()
    timer.timeout.connect(transcribe_cycle)
    timer.start(3000)  # 每3秒转录一次
    
    try:
        # 运行应用
        app.exec_()
    finally:
        # 清理资源
        timer.stop()
        transcriber.stop_audio()

if __name__ == "__main__":
    main()
