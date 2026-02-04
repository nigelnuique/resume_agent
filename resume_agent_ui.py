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
                    'message': 'Loading initial data...',
                    'progress': 5
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
                    'message': 'Setting up AI workflow...',
                    'progress': 10
                })
                
                # Set up workflow
                workflow = setup_workflow()
                app_workflow = workflow.compile()
                
                # Define workflow steps for progress tracking
                workflow_steps = [
                    ('parse_job_ad', 'Analyzing job requirements...', 20),
                    ('reorder_sections', 'Optimizing section order...', 30),
                    ('tailor_summary_and_skills', 'Tailoring summary and skills together...', 45),
                    ('tailor_experience', 'Tailoring work experience...', 55),
                    ('tailor_projects', 'Tailoring projects...', 65),
                    ('tailor_education', 'Tailoring education...', 70),
                    ('tailor_certifications', 'Tailoring certifications...', 75),
                    ('tailor_extracurricular', 'Tailoring extracurricular activities...', 80),
                    ('validate_yaml', 'Validating final output...', 85)
                ]
                
                # Create step lookup for progress tracking
                step_lookup = {step_name: (message, progress) for step_name, message, progress in workflow_steps}
                
                # Execute workflow with real-time progress tracking using streaming
                current_step = 0
                final_state = state  # Initialize with current state
                
                try:
                    # Use streaming to get real-time updates as each node completes
                    for chunk in app_workflow.stream(state):
                        # chunk contains {node_name: node_output}
                        for node_name, node_output in chunk.items():
                            print(f"🔄 Completed node: {node_name}")
                            
                            if node_name in step_lookup:
                                message, progress = step_lookup[node_name]
                                socketio.emit('workflow_progress', {
                                    'step': node_name,
                                    'message': message,
                                    'progress': progress
                                })
                                current_step += 1
                                print(f"   ✅ Progress update sent: {message} ({progress}%)")
                            
                            # Update final_state with the node output (should be complete ResumeState)
                            if isinstance(node_output, dict):
                                final_state = node_output
                                print(f"   📝 State updated from {node_name}")
                    
                    print(f"✅ Workflow streaming completed. Final state type: {type(final_state)}")
                    
                except Exception as workflow_error:
                    # If streaming fails, fall back to regular execution
                    print(f"⚠️ Streaming failed, falling back to regular execution: {workflow_error}")
                    socketio.emit('workflow_progress', {
                        'step': 'fallback',
                        'message': 'Continuing with standard execution...',
                        'progress': 50
                    })
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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f;
            color: #e4e4e7;
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* ── Toast Notifications ── */
        .toast-container {
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        }

        .toast {
            pointer-events: auto;
            min-width: 320px;
            max-width: 480px;
            padding: 14px 20px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            animation: toastIn 0.35s cubic-bezier(0.21,1.02,0.73,1) forwards;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.06);
        }

        .toast.hiding {
            animation: toastOut 0.3s ease forwards;
        }

        .toast-success {
            background: rgba(34,197,94,0.15);
            color: #4ade80;
            border-color: rgba(34,197,94,0.2);
        }

        .toast-error {
            background: rgba(239,68,68,0.15);
            color: #f87171;
            border-color: rgba(239,68,68,0.2);
        }

        .toast-info {
            background: rgba(59,130,246,0.15);
            color: #60a5fa;
            border-color: rgba(59,130,246,0.2);
        }

        .toast-icon { font-size: 18px; flex-shrink: 0; }
        .toast-text { flex: 1; }

        .toast-close {
            background: none;
            border: none;
            color: inherit;
            cursor: pointer;
            opacity: 0.5;
            font-size: 18px;
            padding: 0 0 0 8px;
            line-height: 1;
        }
        .toast-close:hover { opacity: 1; }

        @keyframes toastIn {
            from { opacity: 0; transform: translateX(40px) scale(0.96); }
            to   { opacity: 1; transform: translateX(0) scale(1); }
        }
        @keyframes toastOut {
            from { opacity: 1; transform: translateX(0) scale(1); }
            to   { opacity: 0; transform: translateX(40px) scale(0.96); }
        }

        /* ── Header ── */
        .header {
            background: linear-gradient(135deg, #18181b 0%, #1a1a2e 100%);
            padding: 28px 24px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(16px);
        }

        .header h1 {
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header p {
            color: #71717a;
            font-size: 14px;
            margin-top: 4px;
        }

        /* ── Container ── */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
            flex: 1;
        }

        /* ── Cards ── */
        .card {
            background: #18181b;
            margin: 24px 0;
            padding: 28px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.06);
            transition: border-color 0.2s;
        }

        .card:hover {
            border-color: rgba(255,255,255,0.1);
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #e4e4e7;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-title .icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }

        .icon-blue   { background: rgba(59,130,246,0.15); }
        .icon-purple { background: rgba(139,92,246,0.15); }
        .icon-green  { background: rgba(34,197,94,0.15); }
        .icon-amber  { background: rgba(245,158,11,0.15); }

        /* ── Collapsible How-it-Works ── */
        .how-it-works-toggle {
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            user-select: none;
        }

        .how-it-works-toggle .chevron {
            transition: transform 0.3s ease;
            color: #71717a;
            font-size: 20px;
        }

        .how-it-works-toggle .chevron.open {
            transform: rotate(180deg);
        }

        .collapsible-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s;
            opacity: 0;
        }

        .collapsible-content.open {
            max-height: 800px;
            opacity: 1;
        }

        /* ── Workflow Steps (horizontal on desktop) ── */
        .workflow-steps {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin: 20px 0;
        }

        .workflow-step {
            padding: 20px;
            background: rgba(255,255,255,0.02);
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.05);
            text-align: center;
            transition: border-color 0.2s, transform 0.2s;
        }

        .workflow-step:hover {
            border-color: rgba(96,165,250,0.3);
            transform: translateY(-2px);
        }

        .step-number {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: #fff;
            font-weight: 700;
            font-size: 15px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
        }

        .step-content h3 {
            color: #e4e4e7;
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .step-content p {
            color: #a1a1aa;
            font-size: 13px;
            line-height: 1.5;
        }

        .workflow-tip {
            background: rgba(34,197,94,0.06);
            border: 1px solid rgba(34,197,94,0.15);
            border-radius: 8px;
            padding: 14px 16px;
            color: #86efac;
            font-size: 13px;
            line-height: 1.6;
        }

        /* ── Input Section ── */
        .input-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        .input-group {
            display: flex;
            flex-direction: column;
        }

        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            font-size: 14px;
            color: #a1a1aa;
        }

        .input-group textarea {
            width: 100%;
            min-height: 200px;
            padding: 14px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            color: #e4e4e7;
            font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            resize: vertical;
            transition: border-color 0.2s, box-shadow 0.2s;
            flex: 1;
        }

        .input-group textarea:focus {
            outline: none;
            border-color: rgba(96,165,250,0.5);
            box-shadow: 0 0 0 3px rgba(96,165,250,0.1);
        }

        .input-group textarea::placeholder {
            color: #52525b;
        }

        .input-hint {
            font-size: 13px;
            color: #71717a;
            margin-bottom: 10px;
            line-height: 1.5;
        }

        /* ── File Upload - Drag & Drop Zone ── */
        .file-drop-zone {
            border: 2px dashed rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.25s;
            margin-bottom: 12px;
            position: relative;
        }

        .file-drop-zone:hover {
            border-color: rgba(96,165,250,0.4);
            background: rgba(96,165,250,0.04);
        }

        .file-drop-zone.drag-over {
            border-color: #3b82f6;
            background: rgba(59,130,246,0.08);
            transform: scale(1.01);
        }

        .file-drop-zone input[type=file] {
            position: absolute;
            inset: 0;
            opacity: 0;
            cursor: pointer;
        }

        .file-drop-icon { font-size: 28px; margin-bottom: 8px; }
        .file-drop-text { font-size: 14px; color: #a1a1aa; }
        .file-drop-text strong { color: #60a5fa; }
        .file-drop-hint { font-size: 12px; color: #52525b; margin-top: 4px; }

        .file-name-display {
            font-size: 13px;
            color: #4ade80;
            margin-top: 8px;
            display: none;
        }

        /* ── Buttons ── */
        .btn {
            border: none;
            padding: 12px 28px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-family: 'Inter', sans-serif;
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #6366f1);
            color: #fff;
            box-shadow: 0 4px 16px rgba(59,130,246,0.3);
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(59,130,246,0.4);
        }

        .btn-primary:disabled {
            background: #27272a;
            color: #52525b;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .btn-secondary {
            background: rgba(255,255,255,0.06);
            color: #a1a1aa;
            border: 1px solid rgba(255,255,255,0.08);
        }

        .btn-secondary:hover {
            background: rgba(255,255,255,0.1);
            color: #e4e4e7;
        }

        .btn-download {
            background: linear-gradient(135deg, #059669, #10b981);
            color: #fff;
            box-shadow: 0 4px 16px rgba(16,185,129,0.25);
        }

        .btn-download:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(16,185,129,0.35);
        }

        .btn-center {
            display: flex;
            justify-content: center;
            margin-top: 24px;
        }

        /* ── Progress Section ── */
        .progress-section {
            margin: 24px 0;
            display: none;
        }

        .progress-card {
            background: #18181b;
            padding: 28px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.06);
        }

        .progress-bar-track {
            width: 100%;
            height: 6px;
            background: rgba(255,255,255,0.06);
            border-radius: 3px;
            overflow: hidden;
            margin: 20px 0;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            border-radius: 3px;
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            width: 0%;
            position: relative;
        }

        .progress-bar-fill::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .progress-message {
            font-size: 14px;
            color: #a1a1aa;
            text-align: center;
        }

        .progress-steps {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            gap: 4px;
        }

        .progress-step-dot {
            flex: 1;
            height: 3px;
            border-radius: 2px;
            background: rgba(255,255,255,0.06);
            transition: background 0.3s;
        }

        .progress-step-dot.active {
            background: #3b82f6;
        }

        .progress-step-dot.completed {
            background: #4ade80;
        }

        /* ── Editor Section ── */
        .editor-section {
            background: #18181b;
            margin: 24px 0;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.06);
            overflow: hidden;
            display: none;
        }

        .editor-header {
            background: rgba(255,255,255,0.02);
            padding: 16px 24px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }

        .editor-header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .editor-header-right {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .editor-status {
            font-size: 12px;
            padding: 5px 12px;
            border-radius: 6px;
            font-weight: 500;
            letter-spacing: 0.3px;
        }

        .editor-status.info {
            background: rgba(59,130,246,0.12);
            color: #60a5fa;
        }

        .editor-status.error {
            background: rgba(239,68,68,0.12);
            color: #f87171;
        }

        .editor-status.success {
            background: rgba(34,197,94,0.12);
            color: #4ade80;
        }

        .editor-main {
            display: flex;
            height: 650px;
        }

        .editor-panel {
            width: 50%;
            border-right: 1px solid rgba(255,255,255,0.06);
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
            font-size: 13px;
            line-height: 1.6;
        }

        .pdf-preview {
            width: 100%;
            height: 100%;
            border: none;
        }

        .preview-message {
            text-align: center;
            color: #71717a;
            font-size: 14px;
            padding: 20px;
        }

        .editor-footer {
            padding: 14px 24px;
            background: rgba(255,255,255,0.02);
            border-top: 1px solid rgba(255,255,255,0.06);
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }

        /* ── Spinner ── */
        .spinner {
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .spinner::after {
            content: '';
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.2);
            border-top: 2px solid #fff;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* ── Footer ── */
        .footer {
            text-align: center;
            padding: 24px;
            color: #3f3f46;
            font-size: 13px;
            border-top: 1px solid rgba(255,255,255,0.04);
            margin-top: auto;
        }

        .footer a {
            color: #60a5fa;
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
        }

        /* ── Responsive ── */
        @media (max-width: 900px) {
            .input-grid {
                grid-template-columns: 1fr;
            }

            .workflow-steps {
                grid-template-columns: 1fr;
            }

            .editor-main {
                flex-direction: column;
                height: auto;
            }

            .editor-panel,
            .preview-panel {
                width: 100%;
            }

            .editor-panel {
                border-right: none;
                border-bottom: 1px solid rgba(255,255,255,0.06);
            }

            .preview-panel {
                min-height: 400px;
            }

            .CodeMirror {
                min-height: 350px;
            }

            .header h1 { font-size: 22px; }

            .editor-header {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <!-- Toast Container -->
    <div class="toast-container" id="toast-container"></div>

    <div class="header">
        <h1>Resume Agent</h1>
        <p>AI-powered resume tailoring for every opportunity</p>
    </div>

    <div class="container">
        <!-- How It Works (collapsible) -->
        <div class="card">
            <div class="how-it-works-toggle" onclick="toggleHowItWorks()">
                <h2 class="section-title" style="margin-bottom:0;">
                    <span class="icon icon-purple">?</span>
                    How It Works
                </h2>
                <span class="chevron" id="how-chevron">&#9660;</span>
            </div>
            <div class="collapsible-content" id="how-it-works-content">
                <div class="workflow-steps" style="margin-top:20px;">
                    <div class="workflow-step">
                        <div class="step-number">1</div>
                        <div class="step-content">
                            <h3>Upload Your Master CV</h3>
                            <p>Provide a comprehensive YAML CV with all your experiences, skills, projects, and achievements.</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <div class="step-number">2</div>
                        <div class="step-content">
                            <h3>AI Tailors Your Resume</h3>
                            <p>Paste the job ad and our AI analyzes requirements, selects relevant content, and optimizes descriptions.</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <div class="step-number">3</div>
                        <div class="step-content">
                            <h3>Review &amp; Download</h3>
                            <p>Fine-tune the AI output with the live editor, preview the PDF in real-time, then download your tailored resume.</p>
                        </div>
                    </div>
                </div>
                <div class="workflow-tip">
                    <strong>Tip:</strong> Keep your master CV comprehensive and up-to-date. The more complete information you provide, the better the AI can tailor each resume.
                </div>
            </div>
        </div>

        <!-- Input Section -->
        <div class="card">
            <h2 class="section-title">
                <span class="icon icon-blue">1</span>
                Input Your Data
            </h2>

            <div class="input-grid">
                <div class="input-group">
                    <label for="master-cv">Master CV (YAML format)</label>
                    <div class="input-hint">
                        Don't have a YAML file? Upload the <strong>master_CV_template.yaml</strong> from the project folder.
                    </div>
                    <div class="file-drop-zone" id="cv-drop-zone">
                        <input type="file" id="cv-file" accept=".yaml,.yml" />
                        <div class="file-drop-icon">&#128196;</div>
                        <div class="file-drop-text">Drag &amp; drop your <strong>.yaml</strong> file here, or click to browse</div>
                        <div class="file-drop-hint">Accepts .yaml and .yml files</div>
                        <div class="file-name-display" id="file-name-display"></div>
                    </div>
                    <textarea id="master-cv" placeholder="Or paste your master CV YAML here..."></textarea>
                </div>

                <div class="input-group">
                    <label for="job-ad">Job Advertisement</label>
                    <div class="input-hint">Paste the full job posting including requirements, responsibilities, and qualifications.</div>
                    <textarea id="job-ad" placeholder="Paste the job advertisement text here..."></textarea>
                </div>
            </div>

            <div class="btn-center">
                <button class="btn btn-primary" id="process-btn" onclick="startAIProcessing()">
                    Process with AI
                </button>
            </div>
        </div>

        <!-- Progress Section -->
        <div class="progress-section" id="progress-section">
            <div class="progress-card">
                <h2 class="section-title">
                    <span class="icon icon-amber">&#9881;</span>
                    AI Processing
                </h2>
                <div class="progress-bar-track">
                    <div class="progress-bar-fill" id="progress-fill"></div>
                </div>
                <div class="progress-message" id="progress-message">Initializing...</div>
                <div class="progress-steps" id="progress-steps">
                    <div class="progress-step-dot" data-step="parse_job_ad"></div>
                    <div class="progress-step-dot" data-step="reorder_sections"></div>
                    <div class="progress-step-dot" data-step="tailor_summary_and_skills"></div>
                    <div class="progress-step-dot" data-step="tailor_experience"></div>
                    <div class="progress-step-dot" data-step="tailor_projects"></div>
                    <div class="progress-step-dot" data-step="tailor_education"></div>
                    <div class="progress-step-dot" data-step="tailor_certifications"></div>
                    <div class="progress-step-dot" data-step="tailor_extracurricular"></div>
                    <div class="progress-step-dot" data-step="validate_yaml"></div>
                </div>
            </div>
        </div>

        <!-- Editor Section -->
        <div class="editor-section" id="editor-section">
            <div class="editor-header">
                <div class="editor-header-left">
                    <h2 class="section-title" style="margin-bottom:0;">
                        <span class="icon icon-green">2</span>
                        Final Editing
                    </h2>
                    <div class="editor-status info" id="editor-status">Ready</div>
                </div>
                <div class="editor-header-right">
                    <button class="btn btn-download" onclick="downloadYAML()" title="Download YAML">
                        &#11123; Download YAML
                    </button>
                    <button class="btn btn-secondary" onclick="downloadFromServer()" title="Download from server">
                        &#128190; Save to Disk
                    </button>
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

            <div class="editor-footer">
                <button class="btn btn-secondary" onclick="saveAndRender()">
                    &#8635; Re-render Preview
                </button>
                <button class="btn btn-download" onclick="downloadYAML()">
                    &#11123; Download YAML
                </button>
            </div>
        </div>
    </div>

    <div class="footer">
        Resume Agent &mdash; Built with LangGraph &amp; RenderCV
    </div>

    <script>
        const socket = io();
        let editor;
        let saveTimeout;
        let isRendering = false;
        const completedSteps = new Set();

        /* ── Toast System ── */
        function showToast(message, type = 'info', duration = 4000) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast toast-' + type;

            const icons = { success: '&#10003;', error: '&#10007;', info: '&#8505;' };
            toast.innerHTML =
                '<span class="toast-icon">' + (icons[type] || icons.info) + '</span>' +
                '<span class="toast-text">' + message + '</span>' +
                '<button class="toast-close" onclick="dismissToast(this)">&times;</button>';

            container.appendChild(toast);

            if (duration > 0) {
                setTimeout(function() { dismissToast(toast.querySelector('.toast-close')); }, duration);
            }
        }

        function dismissToast(btn) {
            const toast = btn.closest('.toast');
            if (!toast || toast.classList.contains('hiding')) return;
            toast.classList.add('hiding');
            setTimeout(function() { toast.remove(); }, 300);
        }

        /* ── Collapsible How-it-Works ── */
        function toggleHowItWorks() {
            const content = document.getElementById('how-it-works-content');
            const chevron = document.getElementById('how-chevron');
            content.classList.toggle('open');
            chevron.classList.toggle('open');
        }

        /* ── Initialize CodeMirror ── */
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

                editor.on('change', function() {
                    setEditorStatus('Editing...', 'info');
                    clearTimeout(saveTimeout);
                    saveTimeout = setTimeout(function() { saveAndRender(); }, 1500);
                });
            }
        }

        /* ── Drag & Drop File Upload ── */
        (function() {
            const dropZone = document.getElementById('cv-drop-zone');
            const fileInput = document.getElementById('cv-file');
            const nameDisplay = document.getElementById('file-name-display');

            ['dragenter','dragover'].forEach(function(evt) {
                dropZone.addEventListener(evt, function(e) {
                    e.preventDefault();
                    dropZone.classList.add('drag-over');
                });
            });

            ['dragleave','drop'].forEach(function(evt) {
                dropZone.addEventListener(evt, function(e) {
                    e.preventDefault();
                    dropZone.classList.remove('drag-over');
                });
            });

            dropZone.addEventListener('drop', function(e) {
                const files = e.dataTransfer.files;
                if (files.length) handleFile(files[0]);
            });

            fileInput.addEventListener('change', function(e) {
                if (e.target.files.length) handleFile(e.target.files[0]);
            });

            function handleFile(file) {
                if (!file.name.match(/\\.ya?ml$/i)) {
                    showToast('Please upload a .yaml or .yml file', 'error');
                    return;
                }
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('master-cv').value = e.target.result;
                    nameDisplay.textContent = '&#10003; ' + file.name;
                    nameDisplay.style.display = 'block';
                    showToast('File loaded: ' + file.name, 'success');
                };
                reader.readAsText(file);
            }
        })();

        /* ── AI Processing ── */
        function startAIProcessing() {
            const masterCV = document.getElementById('master-cv').value.trim();
            const jobAd = document.getElementById('job-ad').value.trim();

            if (!masterCV) {
                showToast('Please provide your master CV in YAML format', 'error');
                return;
            }
            if (!jobAd) {
                showToast('Please provide the job advertisement text', 'error');
                return;
            }

            const btn = document.getElementById('process-btn');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner">Processing</span>';
            completedSteps.clear();
            document.querySelectorAll('.progress-step-dot').forEach(function(d) {
                d.className = 'progress-step-dot';
            });

            fetch('/api/save-master-cv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: masterCV })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.error) { throw new Error(data.error); }
                return fetch('/api/save-job-ad', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ job_ad: jobAd })
                });
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.error) { throw new Error(data.error); }
                return fetch('/api/start-workflow', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.error) { throw new Error(data.error); }
                document.getElementById('progress-section').style.display = 'block';
                document.getElementById('progress-section').scrollIntoView({ behavior: 'smooth', block: 'center' });
                showToast('AI processing started', 'info');
            })
            .catch(function(error) {
                showToast(error.message, 'error', 6000);
                resetProcessBtn();
            });
        }

        function resetProcessBtn() {
            const btn = document.getElementById('process-btn');
            btn.disabled = false;
            btn.innerHTML = 'Process with AI';
        }

        /* ── Socket.IO handlers ── */
        socket.on('workflow_progress', function(data) {
            document.getElementById('progress-fill').style.width = (data.progress || 0) + '%';
            document.getElementById('progress-message').textContent = data.message;

            if (data.step) {
                completedSteps.add(data.step);
                document.querySelectorAll('.progress-step-dot').forEach(function(dot) {
                    if (completedSteps.has(dot.dataset.step)) {
                        dot.className = 'progress-step-dot completed';
                    } else if (dot.dataset.step === data.step) {
                        dot.className = 'progress-step-dot active';
                    }
                });
            }
        });

        socket.on('workflow_complete', function(data) {
            document.getElementById('progress-fill').style.width = '100%';
            document.getElementById('progress-message').textContent = 'Complete! Loading editor...';
            document.querySelectorAll('.progress-step-dot').forEach(function(d) {
                d.className = 'progress-step-dot completed';
            });

            fetch('/api/load-working-cv')
                .then(function(r) { return r.text(); })
                .then(function(workingCV) {
                    document.getElementById('yaml-editor').value = workingCV;
                    document.getElementById('editor-section').style.display = 'block';
                    initializeEditor();
                    editor.setValue(workingCV);

                    setTimeout(function() {
                        document.getElementById('progress-section').style.display = 'none';
                        document.getElementById('editor-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 1500);

                    resetProcessBtn();
                    showToast('Resume tailored successfully!', 'success', 5000);

                    setTimeout(function() {
                        if (editor) { saveAndRender(); }
                    }, 500);
                });
        });

        socket.on('workflow_error', function(data) {
            showToast('Workflow error: ' + data.error, 'error', 8000);
            document.getElementById('progress-section').style.display = 'none';
            resetProcessBtn();
        });

        /* ── Editor helpers ── */
        function setEditorStatus(message, type) {
            var el = document.getElementById('editor-status');
            el.textContent = message;
            el.className = 'editor-status ' + (type || 'info');
        }

        function showPreviewMessage(msg) {
            document.getElementById('preview-message').textContent = msg;
            document.getElementById('preview-message').style.display = 'block';
            document.getElementById('pdf-preview').style.display = 'none';
        }

        function showPDF(url) {
            document.getElementById('pdf-preview').src = url;
            document.getElementById('pdf-preview').style.display = 'block';
            document.getElementById('preview-message').style.display = 'none';
        }

        function saveAndRender() {
            if (isRendering || !editor) return;
            isRendering = true;
            setEditorStatus('Rendering...', 'info');

            fetch('/api/save-working-cv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: editor.getValue() })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                isRendering = false;
                if (data.success) {
                    if (data.render && data.render.success) {
                        setEditorStatus(data.render.cached ? 'Up to date' : 'Rendered', 'success');
                        showPDF(data.render.pdf_url);
                    } else if (data.render && data.render.error) {
                        if (data.render.error.includes('in progress')) {
                            setEditorStatus('Rendering...', 'info');
                            showPreviewMessage('Rendering changes...');
                            setTimeout(function() { if (!isRendering) saveAndRender(); }, 1500);
                        } else {
                            setEditorStatus('Render error', 'error');
                            showPreviewMessage(data.render.error);
                        }
                    }
                } else {
                    setEditorStatus('Save error', 'error');
                    showPreviewMessage(data.error);
                }
            })
            .catch(function(err) {
                isRendering = false;
                setEditorStatus('Network error', 'error');
                showPreviewMessage('Network error: ' + err.message);
            });
        }

        /* ── Download Functions ── */
        function downloadYAML() {
            if (!editor) return;
            var content = editor.getValue();
            var blob = new Blob([content], { type: 'text/yaml' });
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'tailored_resume.yaml';
            a.click();
            URL.revokeObjectURL(url);
            showToast('YAML file downloaded', 'success');
        }

        function downloadFromServer() {
            window.location.href = '/api/download-yaml';
        }

        /* ── Init on load ── */
        var yamlEl = document.getElementById('yaml-editor');
        if (yamlEl.value.trim() && yamlEl.value.indexOf('No working CV available') === -1) {
            document.getElementById('editor-section').style.display = 'block';
            initializeEditor();
            setTimeout(function() {
                if (editor) {
                    setEditorStatus('Rendering...', 'info');
                    saveAndRender();
                }
            }, 500);
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

@app.route('/api/download-yaml')
def download_yaml():
    """Download the working CV YAML file."""
    if os.path.exists(ui.working_cv_file):
        return send_file(
            os.path.abspath(ui.working_cv_file),
            mimetype='text/yaml',
            as_attachment=True,
            download_name='tailored_resume.yaml'
        )
    return jsonify({"error": "No working CV file available"}), 404



if __name__ == '__main__':
    print("🚀 Starting Resume Agent UI")
    print("🌐 Open your browser to: http://localhost:5000")
    print("📋 Complete workflow: Input → AI Processing → Manual Editing → Download")
    print("\nPress Ctrl+C to stop")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 