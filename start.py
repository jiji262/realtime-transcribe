#!/usr/bin/env python3
"""
Simple launcher for Real-time Speech Transcription
"""

import os
import sys
import subprocess

def print_header():
    print("=" * 50)
    print("🎤 Real-time Speech Transcription")
    print("=" * 50)
    print()

def print_menu():
    print("Choose your language:")
    print()
    print("1. 🇺🇸 English (Fast & Accurate)")
    print("2. 🇨🇳 Chinese (中文)")
    print("3. ⚡ Ultra-fast English (Lower quality)")
    print("4. 🎯 High-accuracy English (Slower)")
    print()
    print("0. Exit")
    print()

def run_transcription(command):
    """Run the transcription with the given command"""
    try:
        print("Starting transcription...")
        print("Press Ctrl+C to stop")
        print("-" * 30)
        subprocess.run(command, shell=True)
    except KeyboardInterrupt:
        print("\nTranscription stopped.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print_header()
    
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (0-4): ").strip()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        
        if choice == "0":
            print("Goodbye!")
            break
        elif choice == "1":
            # Standard English mode - balanced speed and accuracy
            command = "python3 transcribe.py --model tiny.en --language en --realtime-mode --chunk-size 1024 --min-duration 0.5 --max-duration 3.0 --stabilize-turns 0"
            run_transcription(command)
        elif choice == "2":
            # Chinese mode
            command = "python3 transcribe.py --model small --language zh --chunk-size 2048 --min-duration 1.0 --max-duration 5.0"
            run_transcription(command)
        elif choice == "3":
            # Ultra-fast English mode
            command = "python3 transcribe.py --model tiny.en --language en --realtime-mode --chunk-size 512 --min-duration 0.3 --max-duration 2.0 --stabilize-turns 0"
            run_transcription(command)
        elif choice == "4":
            # High-accuracy English mode
            command = "python3 transcribe.py --model base.en --language en --chunk-size 2048 --min-duration 1.0 --max-duration 4.0"
            run_transcription(command)
        else:
            print("Invalid choice. Please try again.")
        
        print()

if __name__ == "__main__":
    main()
