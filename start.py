#!/usr/bin/env python3
"""
🎤 Real-time Speech Transcription - Quick Start
===============================================

The simplest way to start real-time transcription with optimal settings.

Usage:
    python start.py                    # Interactive menu
    python start.py --english          # Direct English transcription
    python start.py --chinese          # Direct Chinese transcription
    python start.py --help             # Show help
"""

import os
import sys
import subprocess
import argparse

def print_header():
    print("=" * 60)
    print("🎤 Real-time Speech Transcription with Live Subtitles")
    print("=" * 60)
    print("✨ Features: Multi-line subtitles • 5s stable display • Auto MacBook mic")
    print()

def print_menu():
    print("🚀 Quick Start Options:")
    print()
    print("1. 🇺🇸 English (Recommended - Fast & Accurate)")
    print("2. 🇨🇳 Chinese (中文转录)")
    print("3. 🌍 Auto-detect Language")
    print("4. 🎯 High-quality English (Better accuracy, slower)")
    print()
    print("0. Exit")
    print()

def run_transcription(command_args):
    """Run the transcription with the given command arguments"""
    try:
        print("🚀 Starting transcription...")
        print("💡 Tips:")
        print("   - Speak clearly at normal volume")
        print("   - Subtitle window will appear automatically")
        print("   - Press Ctrl+C to stop")
        print("   - Drag subtitle window to desired position")
        print("-" * 50)

        # Use the optimized command with new defaults
        subprocess.run(["python", "transcribe.py"] + command_args)
    except KeyboardInterrupt:
        print("\n\n👋 Transcription stopped by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   - Ensure microphone permissions are granted")
        print("   - Check: pip install -r requirements.txt")

def main():
    # Handle command line arguments for direct start
    parser = argparse.ArgumentParser(description="Quick start real-time transcription")
    parser.add_argument("--english", action="store_true", help="Start English transcription directly")
    parser.add_argument("--chinese", action="store_true", help="Start Chinese transcription directly")
    parser.add_argument("--auto", action="store_true", help="Start auto-language detection")

    args = parser.parse_args()

    # Direct start options
    if args.english:
        print("🇺🇸 Starting English transcription...")
        run_transcription(["--model", "tiny.en", "--language", "en"])
        return
    elif args.chinese:
        print("🇨🇳 Starting Chinese transcription...")
        run_transcription(["--model", "base", "--language", "zh"])
        return
    elif args.auto:
        print("🌍 Starting auto-language detection...")
        run_transcription(["--model", "base", "--language", "auto"])
        return

    # Interactive menu
    print_header()

    while True:
        print_menu()

        try:
            choice = input("Enter your choice (0-4): ").strip()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            # Optimized English mode with new defaults
            run_transcription(["--model", "tiny.en", "--language", "en"])
        elif choice == "2":
            # Chinese mode
            run_transcription(["--model", "base", "--language", "zh"])
        elif choice == "3":
            # Auto-detect language
            run_transcription(["--model", "base", "--language", "auto"])
        elif choice == "4":
            # High-quality English mode
            run_transcription(["--model", "base.en", "--language", "en"])
        else:
            print("❌ Invalid choice. Please try again.")

        print()

if __name__ == "__main__":
    main()
