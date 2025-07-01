#!/usr/bin/env python3
"""
Simple Split-Screen YAML CV Editor
Left: YAML editor with syntax highlighting
Right: Fast PDF preview using RenderCV
"""

import os
import yaml
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file

app = Flask(__name__)

class SimpleYAMLEditor:
    def __init__(self):
        self.working_cv_file = "working_CV.yaml"
        self.temp_dir = "temp_renders"
        self.ensure_directories()
        self.current_render = None
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def load_yaml(self):
        """Load YAML content from file."""
        try:
            if os.path.exists(self.working_cv_file):
                with open(self.working_cv_file, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                return "# Create your CV YAML here\ncv:\n  name: Your Name\n  email: your.email@example.com"
        except Exception as e:
            return f"# Error loading file: {str(e)}"
    
    def save_yaml(self, yaml_content):
        """Save and render YAML content."""
        try:
            # Validate YAML syntax
            yaml.safe_load(yaml_content)
            
            # Save to file
            with open(self.working_cv_file, 'w', encoding='utf-8') as file:
                file.write(yaml_content)
            
            # Render immediately
            render_result = self.render_pdf(yaml_content)
            
            return {
                "success": True,
                "render": render_result
            }
        except yaml.YAMLError as e:
            return {"error": f"Invalid YAML: {str(e)}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}
    
    def render_pdf(self, yaml_content):
        """Render CV to PDF using RenderCV."""
        try:
            # Create unique temp directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_render_dir = os.path.join(self.temp_dir, f"render_{timestamp}")
            os.makedirs(temp_render_dir, exist_ok=True)
            
            # Create temp YAML file
            temp_yaml = os.path.join(temp_render_dir, "temp_cv.yaml")
            with open(temp_yaml, 'w', encoding='utf-8') as file:
                file.write(yaml_content)
            
            # Use RenderCV to render PDF
            pdf_path = os.path.join(temp_render_dir, "cv.pdf")
            cmd = ["python", "-m", "rendercv", "render", temp_yaml, "--pdf-path", pdf_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(pdf_path):
                self.current_render = {
                    "pdf_path": pdf_path,
                    "timestamp": timestamp,
                    "temp_dir": temp_render_dir
                }
                
                return {
                    "success": True,
                    "pdf_url": f"/pdf/{timestamp}",
                    "timestamp": timestamp
                }
            else:
                return {
                    "error": f"RenderCV failed: {result.stderr or 'Unknown error'}"
                }
                
        except subprocess.TimeoutExpired:
            return {"error": "Rendering timed out"}
        except Exception as e:
            return {"error": f"Render error: {str(e)}"}

editor = SimpleYAMLEditor()

# HTML Template for the split-screen editor
EDITOR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple YAML CV Editor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/yaml/yaml.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/darcula.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1e1e1e;
            color: #ffffff;
            height: 100vh;
            overflow: hidden;
        }
        
        .header {
            background: #2d2d2d;
            padding: 10px 20px;
            border-bottom: 1px solid #404040;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .header h1 {
            font-size: 18px;
            font-weight: 600;
        }
        
        .status {
            font-size: 14px;
            padding: 4px 8px;
            border-radius: 4px;
            background: #007acc;
        }
        
        .status.error {
            background: #d73a49;
        }
        
        .status.success {
            background: #28a745;
        }
        
        .main {
            display: flex;
            height: calc(100vh - 60px);
        }
        
        .editor-panel {
            width: 50%;
            border-right: 1px solid #404040;
            position: relative;
        }
        
        .preview-panel {
            width: 50%;
            background: #f8f9fa;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        .CodeMirror {
            height: 100% !important;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .pdf-preview {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        .preview-message {
            text-align: center;
            color: #666;
            font-size: 16px;
        }
        
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #007acc;
            font-size: 16px;
        }
        
        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60% { content: '...'; }
            80%, 100% { content: ''; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 Simple YAML CV Editor</h1>
        <div class="status" id="status">Ready</div>
    </div>
    
    <div class="main">
        <div class="editor-panel">
            <textarea id="yaml-editor">{{ yaml_content }}</textarea>
        </div>
        
        <div class="preview-panel">
            <div class="preview-message" id="preview-message">
                Start editing to see your CV preview
            </div>
            <iframe class="pdf-preview" id="pdf-preview" style="display: none;"></iframe>
        </div>
    </div>

    <script>
        // Initialize CodeMirror
        const editor = CodeMirror.fromTextArea(document.getElementById('yaml-editor'), {
            mode: 'yaml',
            theme: 'darcula',
            lineNumbers: true,
            lineWrapping: true,
            indentUnit: 2,
            tabSize: 2,
            autoCloseBrackets: true,
            matchBrackets: true
        });
        
        const statusEl = document.getElementById('status');
        const previewMessage = document.getElementById('preview-message');
        const pdfPreview = document.getElementById('pdf-preview');
        
        let saveTimeout;
        let isRendering = false;
        
        function setStatus(message, type = 'info') {
            statusEl.textContent = message;
            statusEl.className = 'status ' + type;
        }
        
        function showPreviewMessage(message) {
            previewMessage.textContent = message;
            previewMessage.style.display = 'block';
            pdfPreview.style.display = 'none';
        }
        
        function showPDF(url) {
            pdfPreview.src = url;
            pdfPreview.style.display = 'block';
            previewMessage.style.display = 'none';
        }
        
        function saveAndRender() {
            if (isRendering) return;
            
            isRendering = true;
            setStatus('Rendering...', 'info');
            showPreviewMessage('🔄 Rendering CV...');
            
            const yamlContent = editor.getValue();
            
            fetch('/api/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ yaml: yamlContent })
            })
            .then(response => response.json())
            .then(data => {
                isRendering = false;
                
                if (data.success) {
                    setStatus('Rendered successfully', 'success');
                    if (data.render && data.render.success) {
                        showPDF(data.render.pdf_url);
                    } else if (data.render && data.render.error) {
                        setStatus('Render error', 'error');
                        showPreviewMessage('❌ ' + data.render.error);
                    }
                } else {
                    setStatus('Error: ' + data.error, 'error');
                    showPreviewMessage('❌ ' + data.error);
                }
            })
            .catch(error => {
                isRendering = false;
                setStatus('Network error', 'error');
                showPreviewMessage('❌ Network error: ' + error.message);
            });
        }
        
        // Auto-save with debouncing
        editor.on('change', function() {
            setStatus('Editing...', 'info');
            
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                saveAndRender();
            }, 1500); // 1.5 second delay after stopping typing
        });
        
        // Initial render
        setTimeout(() => {
            saveAndRender();
        }, 500);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main editor page."""
    yaml_content = editor.load_yaml()
    return render_template_string(EDITOR_HTML, yaml_content=yaml_content)

@app.route('/api/save', methods=['POST'])
def save_yaml():
    """Save YAML and render PDF."""
    data = request.get_json()
    yaml_content = data.get('yaml', '')
    
    result = editor.save_yaml(yaml_content)
    return jsonify(result)

@app.route('/pdf/<timestamp>')
def serve_pdf(timestamp):
    """Serve the rendered PDF."""
    if editor.current_render and editor.current_render['timestamp'] == timestamp:
        pdf_path = editor.current_render['pdf_path']
        if os.path.exists(pdf_path):
            return send_file(pdf_path, mimetype='application/pdf')
    
    return "PDF not found", 404

if __name__ == '__main__':
    print("🚀 Starting Simple YAML CV Editor")
    print("📝 Open your browser to: http://localhost:5000")
    print("💡 Edit YAML on the left, see PDF preview on the right")
    print("⚡ Auto-saves and renders after 1.5 seconds of inactivity")
    print("\nPress Ctrl+C to stop")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 