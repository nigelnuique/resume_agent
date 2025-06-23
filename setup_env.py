#!/usr/bin/env python3
"""
Setup script to create .env file from template
"""

import os
import shutil

def setup_env_file():
    """Create .env file from template if it doesn't exist"""
    
    env_file = ".env"
    template_file = "env_template.txt"
    
    # Check if .env already exists
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        return
    
    # Check if template exists
    if not os.path.exists(template_file):
        print("❌ env_template.txt not found")
        return
    
    try:
        # Copy template to .env
        shutil.copy2(template_file, env_file)
        print("✅ Created .env file from template")
        print("📝 Please edit .env and add your OpenAI API key")
        print("🔗 Get your API key from: https://platform.openai.com/api-keys")
        
        # Show the current content
        print("\nCurrent .env content:")
        print("-" * 40)
        with open(env_file, 'r') as f:
            print(f.read())
        print("-" * 40)
        print("⚠️  Remember to replace 'your-openai-api-key-here' with your actual API key!")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    setup_env_file() 