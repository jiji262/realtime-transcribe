#!/bin/bash

# Color settings
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo -e "${BOLD}${BLUE}==============================================${NC}"
echo -e "${BOLD}${BLUE}     Real-time Transcription Launcher v1.1    ${NC}"
echo -e "${BOLD}${BLUE}==============================================${NC}"
echo
echo -e "${YELLOW}Please select a transcription mode:${NC}"
echo
echo -e "${BOLD}${GREEN}[English Transcription Options]${NC}"
echo -e "${CYAN}1. Ultra-fast English Mode${NC} - tiny.en model (76MB)"
echo -e "   Pros: Very low latency, minimal resource usage"
echo -e "   Cons: Lower accuracy, best for simple sentences"
echo -e "   Use case: Limited performance devices, quick response scenarios"
echo
echo -e "${CYAN}2. Standard English Mode${NC} - base.en model (145MB)"
echo -e "   Pros: Balanced speed and accuracy"
echo -e "   Cons: May have errors with complex sentences"
echo -e "   Use case: Everyday meetings, general conversations"
echo
echo -e "${CYAN}3. High-accuracy English Mode${NC} - small.en model (465MB)"
echo -e "   Pros: Higher accuracy, better punctuation"
echo -e "   Cons: Slower initial loading, higher memory usage"
echo -e "   Use case: Scenarios requiring high-quality transcription"
echo
echo -e "${BOLD}${GREEN}[Chinese Transcription Options]${NC}"
echo -e "${CYAN}4. Standard Chinese Mode${NC} - medium model (1.5GB)"
echo -e "   Pros: Good Chinese recognition capability"
echo -e "   Cons: Large model, longer initial loading time"
echo -e "   Use case: General Chinese scenarios, lectures, meetings"
echo
echo -e "${CYAN}5. Compact Chinese Mode${NC} - small model (465MB)"
echo -e "   Pros: Faster loading than medium model, less resource usage"
echo -e "   Cons: Slightly lower accuracy than medium model"
echo -e "   Use case: Devices with limited performance, non-professional scenarios"
echo
echo -e "${BOLD}${GREEN}[Special Optimization Modes]${NC}"
echo -e "${CYAN}6. Ultra-realtime Mode${NC} - tiny.en model (76MB)"
echo -e "   Pros: Lowest latency, real-time display"
echo -e "   Cons: Significant accuracy sacrifice"
echo -e "   Use case: Demonstrations requiring immediate feedback, live captioning"
echo
echo -e "${CYAN}0. Exit Program${NC}"
echo
echo -e "${YELLOW}Models will be automatically downloaded on first run, please ensure network connectivity${NC}"
echo -e "${YELLOW}Models will be cached in ~/.cache/whisper directory for future use${NC}"
echo
echo -e "${BOLD}Please enter your selection [0-6]:${NC} "
read choice

# Display startup info
show_starting_info() {
    local model=$1
    local mode=$2
    local lang=$3
    
    echo
    echo -e "${BLUE}==============================================${NC}"
    echo -e "${BLUE}Starting ${mode}...${NC}"
    echo -e "${BLUE}Model: ${model} | Language: ${lang}${NC}"
    echo -e "${BLUE}==============================================${NC}"
    echo
}

case $choice in
    1)
        show_starting_info "tiny.en" "Ultra-fast English Mode" "English"
        python3 transcribe.py --input-provider pyaudio --model tiny.en --no-faster-whisper --language en --chunk-size 1024 --realtime-mode
        ;;
    2)
        show_starting_info "base.en" "Standard English Mode" "English"
        python3 transcribe.py --input-provider pyaudio --model base.en --no-faster-whisper --language en --chunk-size 2048
        ;;
    3)
        show_starting_info "small.en" "High-accuracy English Mode" "English"
        python3 transcribe.py --input-provider pyaudio --model small.en --no-faster-whisper --language en --chunk-size 2048
        ;;
    4)
        show_starting_info "medium" "Standard Chinese Mode" "Chinese"
        python3 transcribe.py --input-provider pyaudio --model medium --no-faster-whisper --language zh --chunk-size 2048
        ;;
    5)
        show_starting_info "small" "Compact Chinese Mode" "Chinese"
        python3 transcribe.py --input-provider pyaudio --model small --no-faster-whisper --language zh --chunk-size 2048
        ;;
    6)
        show_starting_info "tiny.en" "Ultra-realtime Mode" "English"
        python3 transcribe.py --input-provider pyaudio --model tiny.en --no-faster-whisper --language en --chunk-size 512 --moving-window 3 --stablize-turns 0 --min-duration 1 --max-duration 5 --realtime-mode --font-size 36
        ;;
    0)
        echo -e "${BLUE}Exiting program${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid selection, starting default English mode...${NC}"
        show_starting_info "tiny.en" "Default English Mode" "English"
        python3 transcribe.py --input-provider pyaudio --model tiny.en --no-faster-whisper --language en --chunk-size 1024 --realtime-mode
        ;;
esac 