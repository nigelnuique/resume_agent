#!/usr/bin/env python3
"""
Startup script for the Simple YAML CV Editor
"""

import os
import sys
import subprocess
import webbrowser
import time
from threading import Timer

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    # Check if RenderCV is installed
    try:
        result = subprocess.run(["python", "-m", "rendercv", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ RenderCV is installed")
            return True
        else:
            print("❌ RenderCV not found")
            print("   Install it with: pip install rendercv")
            return False
    except Exception:
        print("❌ RenderCV not found")
        print("   Install it with: pip install rendercv")
        return False

def create_sample_cv():
    """Create a sample working_CV.yaml if it doesn't exist."""
    if not os.path.exists("working_CV.yaml"):
        print("📝 Creating sample working_CV.yaml...")
        
        sample_cv = """cv:
  name: John Doe
  label: Software Engineer
  location: San Francisco, CA
  email: john.doe@example.com
  phone: "+1 (555) 123-4567"
  website: https://johndoe.dev
  social_networks:
    - network: LinkedIn
      username: johndoe
    - network: GitHub
      username: johndoe

  sections:
    summary:
      - "Experienced software engineer with 5+ years of expertise in full-stack development, cloud technologies, and team leadership."
      - "Proven track record of delivering scalable solutions and mentoring junior developers."

    experience:
      - company: Tech Corp
        position: Senior Software Engineer
        location: San Francisco, CA
        start_date: 2020-01
        end_date: present
        highlights:
          - Led development of microservices architecture serving 1M+ users
          - Mentored 3 junior developers and improved team productivity by 40%
          - Built CI/CD pipelines reducing deployment time by 60%

      - company: StartupXYZ
        position: Full Stack Developer
        location: San Francisco, CA
        start_date: 2018-06
        end_date: 2019-12
        highlights:
          - Developed React-based frontend and Node.js backend
          - Implemented real-time features using WebSockets
          - Collaborated with design team to create responsive UI

    education:
      - institution: University of California, Berkeley
        area: Computer Science
        degree: Bachelor of Science
        start_date: 2014-09
        end_date: 2018-05
        gpa: 3.8/4.0

    skills:
      - label: Programming Languages
        details: Python, JavaScript, TypeScript, Java, Go
      - label: Frameworks & Libraries
        details: React, Node.js, Express, Django, Flask
      - label: Cloud & DevOps
        details: AWS, Docker, Kubernetes, CI/CD, Terraform
      - label: Databases
        details: PostgreSQL, MongoDB, Redis

    projects:
      - name: Task Management App
        start_date: 2023-01
        end_date: 2023-03
        highlights:
          - Built full-stack task management application with React and Node.js
          - Implemented real-time collaboration features
          - Deployed on AWS with auto-scaling capabilities

design:
  theme: engineeringresumes
  font: Charter
  font_size: 10pt
  page_size: letterpaper
  color_primary: rgb(0,79,144)
  disable_page_numbering: false
  page_numbering_style: "Page [PAGE_NUMBER] of [TOTAL_PAGES]"
  disable_last_updated_date: false
  last_updated_date_style: "Last updated in [MONTH_ABBREVIATION] [YEAR]"
  header_separator: true
  use_icons_for_connections: true
  margins:
    page:
      top: 0.7 in
      bottom: 0.7 in
      left: 0.7 in
      right: 0.7 in
    section_title:
      top: 0.1 in
      bottom: 0.05 in
    entry_area:
      left_and_right: 0.2 in
      vertical_between: 0.12 in
      date_and_location_width: 1.2 in
      education_degree_width: 1 in
"""
        
        with open("working_CV.yaml", 'w', encoding='utf-8') as file:
            file.write(sample_cv)
        
        print("✅ Sample CV created successfully!")
        return True
    
    return False

def open_browser():
    """Open browser to the editor URL after a short delay."""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

def main():
    """Main function to start the Simple YAML CV Editor."""
    print("🚀 Simple YAML CV Editor")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot start editor due to missing dependencies")
        sys.exit(1)
    
    # Create sample CV if needed
    created_sample = create_sample_cv()
    
    print("\n✅ All dependencies satisfied!")
    
    if created_sample:
        print("\n📝 Sample CV created - you can now edit it!")
    
    print("\n🌐 Starting Simple YAML CV Editor...")
    print("   📝 YAML editor on the left")
    print("   📄 PDF preview on the right") 
    print("   ⚡ Auto-saves after 1.5 seconds of inactivity")
    print("   🎨 Uses RenderCV for fast PDF generation")
    print("\n   Opening browser to: http://localhost:5000")
    print("   Press Ctrl+C to stop the server")
    print("\n" + "=" * 50)
    
    # Open browser in background
    Timer(1.0, open_browser).start()
    
    # Import and run the Flask app
    try:
        from simple_yaml_editor import app
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 YAML Editor stopped")
    except Exception as e:
        print(f"\n❌ Error starting editor: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 