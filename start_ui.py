#!/usr/bin/env python3
"""
Resume Agent UI Launcher
Simple script to start the Resume Agent web interface
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if required files and environment are set up."""
    print("🔍 Checking requirements...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found")
        print("   Please create a .env file with your OpenAI API key:")
        print("   1. Copy env_template.txt to .env")
        print("   2. Add your OpenAI API key: OPENAI_API_KEY=your-key-here")
        print("   3. Get your API key from: https://platform.openai.com/api-keys")
        print()
    
    # Check if required Python packages are installed
    try:
        import flask
        import flask_socketio
        import yaml
        import openai
        print("✅ Required packages are installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("   Please install requirements: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Launch the Resume Agent UI."""
    print("🚀 Resume Agent UI Launcher")
    print("=" * 50)
    
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        return
    
    print("\n🌐 Starting Resume Agent UI...")
    print("   URL: http://localhost:5000")
    print("   Features:")
    print("   - Upload CV and job description")
    print("   - AI-powered resume tailoring")
    print("   - Real-time progress tracking") 
    print("   - Live YAML editor with PDF preview")
    print("   - Download tailored resume")
    print("\n💡 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Import and run the UI
        from resume_agent_ui import socketio, app
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Resume Agent UI stopped")
    except Exception as e:
        print(f"\n❌ Error starting UI: {e}")
        print("   Check that all requirements are installed")

if __name__ == "__main__":
    main() 