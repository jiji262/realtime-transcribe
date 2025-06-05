#!/bin/bash

echo "🎤 Real-time Speech Transcription - Installation"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

echo "✅ Python 3 found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirement.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "To start the application, run:"
    echo "  python3 start.py"
    echo ""
    echo "Or use quick start commands:"
    echo "  ./start_english.sh    # For English"
    echo "  ./start_chinese.sh    # For Chinese"
    echo ""
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
