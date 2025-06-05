#!/usr/bin/env python3
"""
Test script to verify the bug fixes in transcribe.py
"""

import sys
import subprocess
import argparse

def test_argument_parsing():
    """Test that all arguments parse correctly"""
    print("Testing argument parsing...")
    
    # Test basic argument parsing
    try:
        from transcribe import parse_args
        
        # Test with default arguments
        sys.argv = ['transcribe.py']
        args = parse_args()
        
        # Check that stabilize-turns is correctly named
        assert hasattr(args, 'stabilize_turns'), "stabilize_turns argument not found"
        assert args.stabilize_turns == 1, f"Expected stabilize_turns=1, got {args.stabilize_turns}"
        
        # Check that realtime-mode defaults to False
        assert args.realtime_mode == False, f"Expected realtime_mode=False, got {args.realtime_mode}"
        
        print("✓ Argument parsing test passed")
        return True
        
    except Exception as e:
        print(f"✗ Argument parsing test failed: {e}")
        return False

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        import transcribe
        print("✓ Main module imports successfully")
        
        # Test that classes can be instantiated (basic syntax check)
        from transcribe import HUD, Transcriber
        print("✓ Classes can be imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_syntax():
    """Test that the Python syntax is valid"""
    print("Testing Python syntax...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'py_compile', 'transcribe.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Python syntax is valid")
            return True
        else:
            print(f"✗ Syntax error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Syntax test failed: {e}")
        return False

def test_help_output():
    """Test that help output works and contains correct parameter names"""
    print("Testing help output...")
    
    try:
        result = subprocess.run([
            sys.executable, 'transcribe.py', '--help'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            help_text = result.stdout
            
            # Check for corrected parameter names
            if 'stabilize-turns' in help_text:
                print("✓ stabilize-turns parameter found in help")
            else:
                print("✗ stabilize-turns parameter not found in help")
                return False
                
            if 'realtime-mode' in help_text:
                print("✓ realtime-mode parameter found in help")
            else:
                print("✗ realtime-mode parameter not found in help")
                return False
                
            print("✓ Help output test passed")
            return True
        else:
            print(f"✗ Help command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Help test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running bug fix verification tests...\n")
    
    tests = [
        test_syntax,
        test_imports,
        test_argument_parsing,
        test_help_output,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bug fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
