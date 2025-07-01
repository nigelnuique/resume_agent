#!/usr/bin/env python3
"""
Resume Agent UI - Complete Resume Tailoring Interface
Combines AI-powered tailoring with manual editing capabilities
"""

import os
import json
import copy
import threading
import tempfile
import subprocess
import hashlib
import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast
from flask import Flask, render_template_string, request, jsonify, send_file, Response
from flask_socketio import SocketIO, emit
import yaml
from dotenv import load_dotenv

# Import resume agent components
from state import ResumeState, create_initial_state, save_cv_to_file, load_cv_from_file
from run import setup_workflow, validate_working_cv_sections, save_working_cv as save_working_cv_to_file, render_cv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'resume-agent-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class ResumeAgentUI:
    def __init__(self):
        self.temp_dir = "temp_renders"
        self.working_cv_file = "working_CV.yaml"
        self.master_cv_file = "master_CV.yaml"
        self.job_ad_file = "job_advertisement.txt"
        self.current_render = None
        self.workflow_running = False
        
        # Performance optimization attributes
        self.last_render_content_hash = None
        self.render_cache = {}  # content_hash -> render_result
        self.render_queue = []
        self.render_lock = threading.Lock()
        self.is_rendering = False
        
        self.ensure_directories()
        self.cleanup_old_renders()
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs("rendercv_output", exist_ok=True)
    
    def cleanup_old_renders(self):
        """Clean up old render directories to free disk space."""
        try:
            if not os.path.exists(self.temp_dir):
                return
            
            # Keep only the last 5 renders
            render_dirs = []
            for item in os.listdir(self.temp_dir):
                item_path = os.path.join(self.temp_dir, item)
                if os.path.isdir(item_path) and item.startswith('render_'):
                    render_dirs.append((item_path, os.path.getctime(item_path)))
            
            # Sort by creation time, oldest first
            render_dirs.sort(key=lambda x: x[1])
            
            # Remove all but the 5 most recent
            for item_path, _ in render_dirs[:-5]:
                try:
                    shutil.rmtree(item_path)
                    print(f"🧹 Cleaned up old render: {item_path}")
                except Exception as e:
                    print(f"⚠️ Could not remove {item_path}: {e}")
                    
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
    
    def get_content_hash(self, content: str) -> str:
        """Generate a hash for content to detect changes."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def should_render(self, yaml_content: str) -> bool:
        """Check if content has changed enough to warrant a new render."""
        content_hash = self.get_content_hash(yaml_content)
        
        # Check if content is the same as last render
        if self.last_render_content_hash == content_hash:
            return False
            
        # Check if we have this render cached
        if content_hash in self.render_cache:
            # Use cached render
            cached_result = self.render_cache[content_hash]
            self.current_render = cached_result
            self.last_render_content_hash = content_hash
            return False
            
        return True
    
    def save_master_cv(self, yaml_content):
        """Save master CV YAML content."""
        try:
            # Validate YAML syntax
            cv_data = yaml.safe_load(yaml_content)
            
            # Save to master CV file
            with open(self.master_cv_file, 'w', encoding='utf-8') as file:
                file.write(yaml_content)
            
            return {"success": True, "message": "Master CV saved successfully"}
        except yaml.YAMLError as e:
            return {"error": f"Invalid YAML: {str(e)}"}
        except Exception as e:
            return {"error": f"Error saving master CV: {str(e)}"}
    
    def save_job_advertisement(self, job_ad_text):
        """Save job advertisement text."""
        try:
            with open(self.job_ad_file, 'w', encoding='utf-8') as file:
                file.write(job_ad_text)
            
            return {"success": True, "message": "Job advertisement saved successfully"}
        except Exception as e:
            return {"error": f"Error saving job advertisement: {str(e)}"}
    
    def run_ai_workflow(self):
        """Run the AI workflow in a separate thread with progress updates."""
        if self.workflow_running:
            return {"error": "Workflow already running"}
        
        self.workflow_running = True
        
        def workflow_thread():
            try:
                # Load environment variables
                load_dotenv()
                
                # Check API key
                if not os.getenv("OPENAI_API_KEY"):
                    socketio.emit('workflow_error', {
                        'error': 'OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.'
                    })
                    return
                
                socketio.emit('workflow_progress', {
                    'step': 'initializing',
                    'message': 'Loading initial data...'
                })
                
                # Create initial state
                state = create_initial_state()
                
                # Load master CV
                if not os.path.exists(self.master_cv_file):
                    socketio.emit('workflow_error', {
                        'error': 'Master CV file not found. Please upload your CV first.'
                    })
                    return
                
                master_cv = load_cv_from_file(self.master_cv_file)
                state['master_cv'] = master_cv
                state['working_cv'] = copy.deepcopy(master_cv)
                
                # Load job advertisement
                if not os.path.exists(self.job_ad_file):
                    socketio.emit('workflow_error', {
                        'error': 'Job advertisement not found. Please enter the job description first.'
                    })
                    return
                
                with open(self.job_ad_file, 'r', encoding='utf-8') as file:
                    job_ad = file.read()
                
                state['job_advertisement'] = job_ad
                
                # Validate working CV sections
                validate_working_cv_sections(state)
                
                socketio.emit('workflow_progress', {
                    'step': 'workflow_setup',
                    'message': 'Setting up AI workflow...'
                })
                
                # Set up workflow
                workflow = setup_workflow()
                app_workflow = workflow.compile()
                
                # Define workflow steps for progress tracking
                workflow_steps = [
                    ('parse_job_ad', 'Analyzing job requirements...'),
                    ('reorder_sections', 'Optimizing section order...'),
                    ('update_summary', 'Updating professional summary...'),
                    ('tailor_experience', 'Tailoring work experience...'),
                    ('tailor_projects', 'Tailoring projects...'),
                    ('tailor_education', 'Tailoring education...'),
                    ('tailor_certifications', 'Tailoring certifications...'),
                    ('tailor_extracurricular', 'Tailoring extracurricular activities...'),
                    ('tailor_skills', 'Tailoring skills...'),
                    ('validate_yaml', 'Validating final output...')
                ]
                
                # Run workflow with progress updates
                for i, (step_name, message) in enumerate(workflow_steps):
                    socketio.emit('workflow_progress', {
                        'step': step_name,
                        'message': message,
                        'progress': int((i / len(workflow_steps)) * 100)
                    })
                
                # Execute the workflow
                final_state = cast(ResumeState, app_workflow.invoke(state))
                
                socketio.emit('workflow_progress', {
                    'step': 'saving',
                    'message': 'Saving tailored resume...',
                    'progress': 90
                })
                
                # Save the working CV
                save_cv_to_file(final_state['working_cv'], "working_CV.yaml")
                
                socketio.emit('workflow_progress', {
                    'step': 'complete',
                    'message': 'AI tailoring complete! Ready for final edits.',
                    'progress': 100
                })
                
                # Emit completion with results
                socketio.emit('workflow_complete', {
                    'success': True,
                    'message': 'Resume tailoring completed successfully!',
                    'errors': final_state.get('errors', []),
                    'warnings': final_state.get('warnings', [])
                })
                
            except Exception as e:
                socketio.emit('workflow_error', {
                    'error': f'Workflow failed: {str(e)}'
                })
            finally:
                self.workflow_running = False
        
        # Start workflow in separate thread
        thread = threading.Thread(target=workflow_thread)
        thread.daemon = True
        thread.start()
        
        return {"success": True, "message": "Workflow started"}
    
    def load_working_cv(self):
        """Load working CV content."""
        try:
            if os.path.exists(self.working_cv_file):
                with open(self.working_cv_file, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                return "# No working CV available yet\n# Please run AI processing first or upload your CV"
        except Exception as e:
            return f"# Error loading working CV: {str(e)}"
    
    def save_working_cv_content(self, yaml_content):
        """Save working CV YAML content."""
        try:
            # Validate YAML syntax
            yaml.safe_load(yaml_content)
            
            # Save to working CV file
            with open(self.working_cv_file, 'w', encoding='utf-8') as file:
                file.write(yaml_content)
            
            return {"success": True}
        except yaml.YAMLError as e:
            return {"error": f"Invalid YAML: {str(e)}"}
        except Exception as e:
            return {"error": f"Error saving working CV: {str(e)}"}
    
    def render_pdf(self, yaml_content):
        """Render CV to PDF using RenderCV with performance optimizations."""
        try:
            # Check if we need to render at all
            if not self.should_render(yaml_content):
                if self.current_render:
                    return {
                        "success": True,
                        "pdf_url": f"/pdf/{self.current_render['timestamp']}",
                        "timestamp": self.current_render['timestamp'],
                        "cached": True
                    }
                
            # Prevent concurrent renders
            with self.render_lock:
                if self.is_rendering:
                    return {"error": "Another render is in progress, please wait..."}
                
                self.is_rendering = True
            
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
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(pdf_path):
                    render_result = {
                        "pdf_path": pdf_path,
                        "timestamp": timestamp,
                        "temp_dir": temp_render_dir
                    }
                    
                    # Cache the result
                    content_hash = self.get_content_hash(yaml_content)
                    self.render_cache[content_hash] = render_result
                    self.last_render_content_hash = content_hash
                    self.current_render = render_result
                    
                    # Clean up old renders after successful render
                    self.cleanup_old_renders()
                    
                    return {
                        "success": True,
                        "pdf_url": f"/pdf/{timestamp}",
                        "timestamp": timestamp
                    }
                else:
                    return {
                        "error": f"RenderCV failed: {result.stderr or 'Unknown error'}"
                    }
                    
            finally:
                self.is_rendering = False
                
        except subprocess.TimeoutExpired:
            self.is_rendering = False
            return {"error": "Rendering timed out (reduced to 10s)"}
        except Exception as e:
            self.is_rendering = False
            return {"error": f"Render error: {str(e)}"}

ui = ResumeAgentUI()

# HTML Template for the complete UI
UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Agent - AI-Powered Resume Tailoring</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/yaml/yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
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
            line-height: 1.6;
        }
        
        .header {
            background: #2d2d2d;
            padding: 20px;
            border-bottom: 1px solid #404040;
            text-align: center;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .header p {
            color: #ccc;
            font-size: 16px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .workflow-section {
            background: #2d2d2d;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #404040;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #4fc3f7;
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #ccc;
        }
        
        .input-group textarea {
            width: 100%;
            min-height: 120px;
            padding: 12px;
            background: #1e1e1e;
            border: 1px solid #404040;
            border-radius: 4px;
            color: #fff;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            resize: vertical;
        }
        
        .input-group textarea:focus {
            outline: none;
            border-color: #4fc3f7;
        }
        
        .btn {
            background: #4fc3f7;
            color: #1e1e1e;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn:hover {
            background: #29b6f6;
            transform: translateY(-1px);
        }
        
        .btn:disabled {
            background: #666;
            color: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #666;
            color: #fff;
        }
        
        .btn-secondary:hover {
            background: #777;
        }
        
        .progress-section {
            background: #2d2d2d;
            margin: 20px 0;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #404040;
            display: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #404040;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        
        .progress-fill {
            height: 100%;
            background: #4fc3f7;
            transition: width 0.3s ease;
            width: 0%;
        }
        
        .progress-message {
            font-size: 16px;
            color: #ccc;
            text-align: center;
        }
        
        .editor-section {
            background: #2d2d2d;
            margin: 20px 0;
            border-radius: 8px;
            border: 1px solid #404040;
            overflow: hidden;
            display: none;
        }
        
        .editor-header {
            background: #333;
            padding: 15px 20px;
            border-bottom: 1px solid #404040;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .editor-status {
            font-size: 14px;
            padding: 4px 8px;
            border-radius: 4px;
            background: #007acc;
        }
        
        .editor-status.error {
            background: #d73a49;
        }
        
        .editor-status.success {
            background: #28a745;
        }
        
        .editor-main {
            display: flex;
            height: 600px;
        }
        
        .editor-panel {
            width: 50%;
            border-right: 1px solid #404040;
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
        
        .actions {
            padding: 15px 20px;
            background: #333;
            border-top: 1px solid #404040;
            display: flex;
            gap: 10px;
            justify-content: center;
        }
        
        .file-upload {
            position: relative;
            display: inline-block;
            margin-bottom: 10px;
        }
        
        .file-upload input[type=file] {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        .file-upload .btn {
            display: inline-block;
        }
        
        .loading {
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .loading::after {
            content: '';
            width: 16px;
            height: 16px;
            border: 2px solid #ccc;
            border-top: 2px solid #4fc3f7;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Resume Agent</h1>
        <p>AI-Powered Resume Tailoring with Manual Editing</p>
    </div>
    
    <div class="container">
        <!-- Input Section -->
        <div class="workflow-section">
            <h2 class="section-title">📋 Step 1: Input Your Data</h2>
            
            <div class="input-group">
                <label for="master-cv">Master CV (YAML format):</label>
                <div class="file-upload">
                    <input type="file" id="cv-file" accept=".yaml,.yml" />
                    <button class="btn btn-secondary">Upload CV File</button>
                </div>
                <textarea id="master-cv" placeholder="Paste your master CV YAML here or upload a file above..."></textarea>
            </div>
            
            <div class="input-group">
                <label for="job-ad">Job Advertisement:</label>
                <textarea id="job-ad" placeholder="Paste the job advertisement text here..."></textarea>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn" id="process-btn" onclick="startAIProcessing()">
                    🤖 Process with AI
                </button>
            </div>
        </div>
        
        <!-- Progress Section -->
        <div class="progress-section" id="progress-section">
            <h2 class="section-title">⚙️ AI Processing Progress</h2>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <div class="progress-message" id="progress-message">Initializing...</div>
        </div>
        
        <!-- Editor Section -->
        <div class="editor-section" id="editor-section">
            <div class="editor-header">
                <h2 class="section-title">✏️ Step 2: Final Editing</h2>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <div class="performance-info" style="font-size: 12px; color: #888;">
                        ⚡ Real-time rendering • Smart change detection
                    </div>
                    <div class="editor-status" id="editor-status">Ready</div>
                </div>
            </div>
            
            <div class="editor-main">
                <div class="editor-panel">
                    <textarea id="yaml-editor">{{ working_cv_content }}</textarea>
                </div>
                
                <div class="preview-panel">
                    <div class="preview-message" id="preview-message">
                        Make edits to see your CV preview
                    </div>
                    <iframe class="pdf-preview" id="pdf-preview" style="display: none;"></iframe>
                </div>
            </div>
            
            <div class="actions">
                <button class="btn btn-secondary" onclick="downloadYAML()">
                    📄 Download YAML
                </button>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let editor;
        let saveTimeout;
        let isRendering = false;
        
        // Initialize CodeMirror when editor section becomes visible
        function initializeEditor() {
            if (!editor) {
                editor = CodeMirror.fromTextArea(document.getElementById('yaml-editor'), {
                    mode: 'yaml',
                    theme: 'darcula',
                    lineNumbers: true,
                    lineWrapping: true,
                    indentUnit: 2,
                    tabSize: 2,
                    autoCloseBrackets: true,
                    matchBrackets: true
                });
                
                // Auto-save with smart debouncing for real-time rendering
                editor.on('change', function() {
                    setEditorStatus('Editing...', 'info');
                    
                    clearTimeout(saveTimeout);
                    saveTimeout = setTimeout(() => {
                        saveAndRender();
                    }, 1500); // Optimized for real-time with smart caching
                });
            }
        }
        
        // File upload handler
        document.getElementById('cv-file').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('master-cv').value = e.target.result;
                };
                reader.readAsText(file);
            }
        });
        
        // AI Processing
        function startAIProcessing() {
            const masterCV = document.getElementById('master-cv').value.trim();
            const jobAd = document.getElementById('job-ad').value.trim();
            
            if (!masterCV) {
                alert('Please provide your master CV in YAML format');
                return;
            }
            
            if (!jobAd) {
                alert('Please provide the job advertisement text');
                return;
            }
            
            // Save master CV
            fetch('/api/save-master-cv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: masterCV })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error saving master CV: ' + data.error);
                    return;
                }
                
                // Save job advertisement
                return fetch('/api/save-job-ad', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ job_ad: jobAd })
                });
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error saving job advertisement: ' + data.error);
                    return;
                }
                
                // Start AI workflow
                return fetch('/api/start-workflow', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error starting workflow: ' + data.error);
                    return;
                }
                
                // Show progress section
                document.getElementById('progress-section').style.display = 'block';
                document.getElementById('process-btn').disabled = true;
                document.getElementById('process-btn').innerHTML = '<span class="loading">Processing...</span>';
            })
            .catch(error => {
                alert('Network error: ' + error.message);
            });
        }
        
        // Socket.IO event handlers
        socket.on('workflow_progress', function(data) {
            document.getElementById('progress-fill').style.width = (data.progress || 0) + '%';
            document.getElementById('progress-message').textContent = data.message;
        });
        
        socket.on('workflow_complete', function(data) {
            document.getElementById('progress-message').textContent = 'AI processing complete! Loading editor...';
            document.getElementById('progress-fill').style.width = '100%';
            
            // Load working CV and show editor
            fetch('/api/load-working-cv')
                .then(response => response.text())
                .then(workingCV => {
                    document.getElementById('yaml-editor').value = workingCV;
                    document.getElementById('editor-section').style.display = 'block';
                    initializeEditor();
                    
                    // Hide progress section after a delay
                    setTimeout(() => {
                        document.getElementById('progress-section').style.display = 'none';
                    }, 2000);
                    
                    // Re-enable process button
                    document.getElementById('process-btn').disabled = false;
                    document.getElementById('process-btn').innerHTML = '🤖 Process with AI';
                });
        });
        
        socket.on('workflow_error', function(data) {
            alert('Workflow Error: ' + data.error);
            document.getElementById('progress-section').style.display = 'none';
            document.getElementById('process-btn').disabled = false;
            document.getElementById('process-btn').innerHTML = '🤖 Process with AI';
        });
        
        // Editor functions
        function setEditorStatus(message, type = 'info') {
            const statusEl = document.getElementById('editor-status');
            statusEl.textContent = message;
            statusEl.className = 'editor-status ' + type;
        }
        
        function showPreviewMessage(message) {
            const previewMessage = document.getElementById('preview-message');
            const pdfPreview = document.getElementById('pdf-preview');
            
            previewMessage.textContent = message;
            previewMessage.style.display = 'block';
            pdfPreview.style.display = 'none';
        }
        
        function showPDF(url) {
            const previewMessage = document.getElementById('preview-message');
            const pdfPreview = document.getElementById('pdf-preview');
            
            pdfPreview.src = url;
            pdfPreview.style.display = 'block';
            previewMessage.style.display = 'none';
        }
        
        function saveAndRender() {
            if (isRendering || !editor) return;
            
            isRendering = true;
            setEditorStatus('Checking for changes...', 'info');
            
            const yamlContent = editor.getValue();
            
            fetch('/api/save-working-cv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: yamlContent })
            })
            .then(response => response.json())
            .then(data => {
                isRendering = false;
                
                if (data.success) {
                    if (data.render && data.render.success) {
                        // Check if result was cached (no changes detected)
                        if (data.render.cached) {
                            setEditorStatus('✅ No changes detected', 'success');
                        } else {
                            setEditorStatus('✅ Changes rendered', 'success');
                        }
                        showPDF(data.render.pdf_url);
                    } else if (data.render && data.render.error) {
                        if (data.render.error.includes('in progress')) {
                            setEditorStatus('⏳ Rendering...', 'info');
                            showPreviewMessage('🔄 Rendering changes...');
                            // Retry after a short delay
                            setTimeout(() => {
                                if (!isRendering) saveAndRender();
                            }, 1500);
                        } else {
                            setEditorStatus('❌ Render error', 'error');
                            showPreviewMessage('❌ ' + data.render.error);
                        }
                    }
                } else {
                    setEditorStatus('❌ Save error: ' + data.error, 'error');
                    showPreviewMessage('❌ ' + data.error);
                }
            })
            .catch(error => {
                isRendering = false;
                setEditorStatus('❌ Network error', 'error');
                showPreviewMessage('❌ Network error: ' + error.message);
            });
        }
        
        function downloadYAML() {
            if (!editor) return;
            
            const yamlContent = editor.getValue();
            const blob = new Blob([yamlContent], { type: 'text/yaml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'tailored_resume.yaml';
            a.click();
            URL.revokeObjectURL(url);
        }
        

        
        // Initialize editor if working CV is already available
        if (document.getElementById('yaml-editor').value.trim() && 
            !document.getElementById('yaml-editor').value.includes('No working CV available')) {
            document.getElementById('editor-section').style.display = 'block';
            initializeEditor();
        }
    </script>
</body>
</html>
"""

# Flask routes
@app.route('/')
def index():
    """Serve the main UI page."""
    working_cv_content = ui.load_working_cv()
    return render_template_string(UI_HTML, working_cv_content=working_cv_content)

@app.route('/api/save-master-cv', methods=['POST'])
def save_master_cv():
    """Save master CV YAML."""
    data = request.get_json()
    yaml_content = data.get('yaml', '')
    result = ui.save_master_cv(yaml_content)
    return jsonify(result)

@app.route('/api/save-job-ad', methods=['POST'])
def save_job_ad():
    """Save job advertisement."""
    data = request.get_json()
    job_ad = data.get('job_ad', '')
    result = ui.save_job_advertisement(job_ad)
    return jsonify(result)

@app.route('/api/start-workflow', methods=['POST'])
def start_workflow():
    """Start the AI workflow."""
    result = ui.run_ai_workflow()
    return jsonify(result)

@app.route('/api/load-working-cv')
def load_working_cv():
    """Load working CV content."""
    return ui.load_working_cv()

@app.route('/api/save-working-cv', methods=['POST'])
def save_working_cv():
    """Save working CV and render PDF automatically when changes are detected."""
    data = request.get_json()
    yaml_content = data.get('yaml', '')
    
    # Save the working CV
    save_result = ui.save_working_cv_content(yaml_content)
    if save_result.get('error'):
        return jsonify(save_result)
    
    # Automatically render PDF (smart caching will handle duplicates)
    render_result = ui.render_pdf(yaml_content)
    
    return jsonify({
        "success": True,
        "render": render_result
    })

@app.route('/pdf/<timestamp>')
def serve_pdf(timestamp):
    """Serve the rendered PDF."""
    if ui.current_render and ui.current_render['timestamp'] == timestamp:
        pdf_path = ui.current_render['pdf_path']
        if os.path.exists(pdf_path):
            return send_file(pdf_path, mimetype='application/pdf')
    
    return "PDF not found", 404



if __name__ == '__main__':
    print("🚀 Starting Resume Agent UI")
    print("🌐 Open your browser to: http://localhost:5000")
    print("📋 Complete workflow: Input → AI Processing → Manual Editing → Download")
    print("\nPress Ctrl+C to stop")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 