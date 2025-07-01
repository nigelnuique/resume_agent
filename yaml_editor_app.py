#!/usr/bin/env python3
"""
YAML Editor App - Split-screen interface for editing working_CV.yaml
Left side: YAML editor with syntax highlighting
Right side: Live PDF preview using RenderCV
"""

import os
import yaml
import subprocess
import tempfile
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
WORKING_CV_FILE = "working_CV.yaml"
RENDERCV_OUTPUT_DIR = "rendercv_output"
TEMP_DIR = "temp_renders"

class YAMLEditor:
    def __init__(self):
        self.working_cv_file = WORKING_CV_FILE
        self.output_dir = RENDERCV_OUTPUT_DIR
        self.temp_dir = TEMP_DIR
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def load_yaml(self) -> dict:
        """Load the working CV YAML file."""
        try:
            if os.path.exists(self.working_cv_file):
                with open(self.working_cv_file, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)
            else:
                return {"error": "Working CV file not found"}
        except Exception as e:
            return {"error": f"Error loading YAML: {str(e)}"}
    
    def save_yaml(self, yaml_content: str) -> dict:
        """Save YAML content to the working CV file."""
        try:
            # Validate YAML syntax
            parsed_yaml = yaml.safe_load(yaml_content)
            
            # Save to file
            with open(self.working_cv_file, 'w', encoding='utf-8') as file:
                yaml.dump(parsed_yaml, file, default_flow_style=False, allow_unicode=True)
            
            return {"success": True, "message": "YAML saved successfully"}
        except yaml.YAMLError as e:
            return {"error": f"Invalid YAML syntax: {str(e)}"}
        except Exception as e:
            return {"error": f"Error saving YAML: {str(e)}"}
    
    def render_pdf(self) -> dict:
        """Render the CV to PDF using RenderCV v2."""
        try:
            # Check if RenderCV is installed
            result = subprocess.run(["rendercv", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return {"error": "RenderCV not found. Please install it first."}
            
            # Create temporary directory for this render
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_render_dir = os.path.join(self.temp_dir, f"render_{timestamp}")
            os.makedirs(temp_render_dir, exist_ok=True)
            
            # Copy working CV to temp directory
            temp_yaml_file = os.path.join(temp_render_dir, "temp_cv.yaml")
            shutil.copy2(self.working_cv_file, temp_yaml_file)
            
            # Run RenderCV v2 with specific output paths
            pdf_output_path = os.path.join(temp_render_dir, "cv.pdf")
            cmd = [
                "rendercv", "render", temp_yaml_file,
                "--pdf-path", pdf_output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Check if PDF was generated
                if os.path.exists(pdf_output_path):
                    return {
                        "success": True,
                        "pdf_path": pdf_output_path,
                        "pdf_filename": "cv.pdf",
                        "temp_dir": temp_render_dir
                    }
                else:
                    # Look for PDF in the temp directory
                    pdf_files = [f for f in os.listdir(temp_render_dir) if f.endswith('.pdf')]
                    if pdf_files:
                        pdf_path = os.path.join(temp_render_dir, pdf_files[0])
                        return {
                            "success": True,
                            "pdf_path": pdf_path,
                            "pdf_filename": pdf_files[0],
                            "temp_dir": temp_render_dir
                        }
                    else:
                        return {"error": "PDF not generated"}
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return {"error": f"RenderCV failed: {error_msg}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "RenderCV command timed out"}
        except Exception as e:
            return {"error": f"Error rendering PDF: {str(e)}"}
    
    def get_yaml_as_string(self) -> str:
        """Get the YAML content as a string."""
        try:
            if os.path.exists(self.working_cv_file):
                with open(self.working_cv_file, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                return "# Working CV file not found\n"
        except Exception as e:
            return f"# Error reading file: {str(e)}\n"
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary render files, keeping only the 5 most recent."""
        try:
            if not os.path.exists(self.temp_dir):
                return
            
            # Get all temp directories with creation times
            temp_dirs = []
            for item in os.listdir(self.temp_dir):
                item_path = os.path.join(self.temp_dir, item)
                if os.path.isdir(item_path):
                    temp_dirs.append((item_path, os.path.getctime(item_path)))
            
            # Sort by creation time (newest first)
            temp_dirs.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old directories (keep first 5)
            for temp_dir, _ in temp_dirs[5:]:
                shutil.rmtree(temp_dir)
                print(f"   🧹 Removed old temp directory: {os.path.basename(temp_dir)}")
                
        except Exception as e:
            print(f"   ⚠️ Error during cleanup: {str(e)}")

# Initialize the editor
editor = YAMLEditor()

@app.route('/')
def index():
    """Main page with split-screen interface."""
    return render_template('editor.html')

@app.route('/api/yaml', methods=['GET'])
def get_yaml():
    """Get the current YAML content."""
    yaml_content = editor.get_yaml_as_string()
    return jsonify({"content": yaml_content})

@app.route('/api/yaml', methods=['POST'])
def save_yaml():
    """Save YAML content."""
    data = request.get_json()
    yaml_content = data.get('content', '')
    
    result = editor.save_yaml(yaml_content)
    return jsonify(result)

@app.route('/api/render', methods=['POST'])
def render_cv():
    """Render the CV to PDF."""
    result = editor.render_pdf()
    return jsonify(result)

@app.route('/api/render-watch', methods=['POST'])
def start_watch_mode():
    """Start RenderCV in watch mode for real-time rendering."""
    try:
        # Start RenderCV in watch mode
        cmd = ["rendercv", "render", editor.working_cv_file, "--watch"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return jsonify({
            "success": True, 
            "message": "Watch mode started",
            "pid": process.pid
        })
    except Exception as e:
        return jsonify({"error": f"Failed to start watch mode: {str(e)}"})

@app.route('/api/stop-watch', methods=['POST'])
def stop_watch_mode():
    """Stop RenderCV watch mode."""
    try:
        # Find and kill RenderCV watch processes
        result = subprocess.run(["pkill", "-f", "rendercv.*--watch"], 
                              capture_output=True, text=True)
        return jsonify({"success": True, "message": "Watch mode stopped"})
    except Exception as e:
        return jsonify({"error": f"Failed to stop watch mode: {str(e)}"})

@app.route('/api/pdf/<path:filename>')
def serve_pdf(filename):
    """Serve the generated PDF file."""
    try:
        # Find the PDF in temp directories
        for temp_dir in os.listdir(editor.temp_dir):
            temp_path = os.path.join(editor.temp_dir, temp_dir)
            if os.path.isdir(temp_path):
                pdf_path = os.path.join(temp_path, filename)
                if os.path.exists(pdf_path):
                    return send_file(pdf_path, mimetype='application/pdf')
        
        return jsonify({"error": "PDF not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_yaml():
    """Validate YAML syntax."""
    data = request.get_json()
    yaml_content = data.get('content', '')
    
    try:
        yaml.safe_load(yaml_content)
        return jsonify({"valid": True, "message": "Valid YAML"})
    except yaml.YAMLError as e:
        return jsonify({"valid": False, "error": str(e)})

@app.route('/api/cleanup', methods=['POST'])
def cleanup_temp_files():
    """Clean up temporary render files."""
    try:
        # Keep only the 5 most recent temp directories
        temp_dirs = []
        for item in os.listdir(editor.temp_dir):
            item_path = os.path.join(editor.temp_dir, item)
            if os.path.isdir(item_path):
                temp_dirs.append((item_path, os.path.getctime(item_path)))
        
        # Sort by creation time (newest first)
        temp_dirs.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old directories (keep first 5)
        for temp_dir, _ in temp_dirs[5:]:
            shutil.rmtree(temp_dir)
        
        return jsonify({"success": True, "message": "Cleanup completed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting YAML Editor App...")
    print(f"📁 Working CV file: {WORKING_CV_FILE}")
    print(f"📁 Output directory: {RENDERCV_OUTPUT_DIR}")
    print("🌐 Open http://localhost:5001 in your browser")
    
    # Clean up old temp files on startup
    editor.cleanup_temp_files()
    
    app.run(debug=True, host='0.0.0.0', port=5001) 