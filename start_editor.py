#!/usr/bin/env python3
"""
Startup script for the YAML Editor App
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    # Check if RenderCV is installed
    try:
        result = subprocess.run(["rendercv", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ RenderCV is installed")
        else:
            print("❌ RenderCV not found")
            print("   Install it with: pip install rendercv")
            return False
    except Exception:
        print("❌ RenderCV not found")
        print("   Install it with: pip install rendercv")
        return False
    
    # Check if working_CV.yaml exists
    if not os.path.exists("working_CV.yaml"):
        print("⚠️ working_CV.yaml not found")
        print("   Run the resume agent first to generate it")
        print("   Or create it manually")
    
    return True

def main():
    """Main function to start the YAML editor."""
    print("🚀 YAML CV Editor")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot start editor due to missing dependencies")
        sys.exit(1)
    
    print("\n✅ All dependencies satisfied!")
    print("\n🌐 Starting YAML Editor...")
    print("   The editor will open at: http://localhost:5001")
    print("   Press Ctrl+C to stop the server")
    print("\n" + "=" * 40)
    
    # Import and run the Flask app
    try:
        from yaml_editor_app import app
        app.run(debug=True, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 YAML Editor stopped")
    except Exception as e:
        print(f"\n❌ Error starting editor: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 