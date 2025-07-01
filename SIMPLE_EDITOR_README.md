# Simple YAML CV Editor

> 🎨 A clean, fast split-screen editor for RenderCV YAML files with real-time PDF preview.

[![Flask](https://img.shields.io/badge/Flask-2.3+-blue.svg)](https://flask.palletsprojects.com/)
[![RenderCV](https://img.shields.io/badge/RenderCV-Compatible-orange.svg)](https://rendercv.com/)
[![Real-time](https://img.shields.io/badge/Preview-Real--time-green.svg)]()

## Overview

The Simple YAML CV Editor provides a streamlined, distraction-free environment for editing your resume YAML files. It features a split-screen interface with live PDF preview, making it perfect for manual fine-tuning after AI tailoring or for users who prefer hands-on editing.

## Key Features

### 🖥️ **Split-Screen Interface**
- **Left Panel**: YAML editor with full syntax highlighting
- **Right Panel**: Live PDF preview that updates as you type
- **Clean Design**: No buttons, no complexity - just edit and see results

### ⚡ **Real-Time Updates**
- **Auto-save**: Saves changes automatically after 1.5 seconds of inactivity
- **Instant Rendering**: PDF regenerates immediately using RenderCV
- **Live Preview**: See your changes reflected in real-time

### 🎨 **Modern Experience**
- **Dark Theme**: Comfortable editing for extended sessions
- **Syntax Highlighting**: Full YAML syntax support with color coding
- **Status Indicators**: Clear feedback on rendering progress and errors

## Quick Start

### Option 1: Double-Click Launch (Windows)
```bash
start_simple_editor.bat
```

### Option 2: Auto-Setup Script
```bash
python start_simple_editor.py
```

### Option 3: Direct Launch
```bash
python simple_yaml_editor.py
```

**Access URL**: `http://localhost:5000`

## Installation & Setup

### Prerequisites
- Python 3.7+
- RenderCV: `pip install rendercv[full]`
- Flask: `pip install flask`

### Automatic Setup
The startup scripts will automatically:
- ✅ Check for required dependencies
- ✅ Install missing packages if needed
- ✅ Create a sample CV if `working_CV.yaml` doesn't exist
- ✅ Launch your default browser
- ✅ Start the Flask development server

### Manual Setup
```bash
# Install dependencies
pip install flask "rendercv[full]"

# Create initial CV file (optional)
cp master_CV_template.yaml working_CV.yaml

# Start editor
python simple_yaml_editor.py
```

## How It Works

### Workflow
1. **Start Editor** → Automatically opens browser at `http://localhost:5000`
2. **Edit YAML** → Type in left panel with syntax highlighting
3. **Auto-Save** → Changes saved to `working_CV.yaml` after 1.5s pause
4. **Live Preview** → PDF updates automatically in right panel
5. **Download** → Access final PDF from the preview panel

### File Management
- **Working File**: `working_CV.yaml` (auto-created if missing)
- **Temp Renders**: `temp_renders/` directory (auto-cleaned)
- **Auto-Save**: Every 1.5 seconds after typing stops

## Sample CV Generation

If `working_CV.yaml` doesn't exist, the editor creates a comprehensive sample CV featuring:

### Professional Template
- **Software Engineer Profile**: Complete with modern tech stack
- **Industry-Standard Sections**: Experience, education, skills, projects
- **RenderCV Theme**: Uses `engineeringresumes` theme for professional appearance
- **Proper Structure**: Valid YAML formatting with all required fields

### Sample Content
- **Work Experience**: Multiple realistic software engineering roles
- **Technical Skills**: Modern programming languages and frameworks
- **Projects**: Portfolio-worthy projects with descriptions
- **Education**: Computer science degree with relevant coursework
- **Contact Information**: Placeholder data ready for customization

## Advanced Features

### Editor Capabilities
- **Full YAML Support**: Complete syntax highlighting and validation
- **Error Detection**: Highlights YAML formatting issues
- **Auto-Indentation**: Maintains proper YAML structure
- **Find/Replace**: Standard text editor functionality

### Rendering Features
- **Multiple Formats**: PDF primary, with HTML/PNG support via RenderCV
- **Theme Support**: Compatible with all RenderCV themes
- **Error Handling**: Graceful handling of rendering failures
- **Performance**: Optimized for fast preview updates

### Status System
- **Ready**: Editor ready for input
- **Saving**: Auto-save in progress
- **Rendering**: PDF generation in progress
- **Error**: Display rendering or YAML errors
- **Success**: Successful render completion

## Troubleshooting

### Common Issues

**Port 5000 Already in Use**
```bash
# Edit simple_yaml_editor.py, change the last line:
app.run(debug=True, host='0.0.0.0', port=5001)  # Use different port
```

**RenderCV Not Found**
```bash
# Install full RenderCV package
pip install "rendercv[full]"

# Verify installation
python -m rendercv --version
```

**Browser Doesn't Open**
```bash
# Manually navigate to:
http://localhost:5000

# Or try different port if changed:
http://localhost:5001
```

**YAML Syntax Errors**
- Check indentation (use spaces, not tabs)
- Ensure proper YAML structure
- Look for unescaped special characters
- Validate required fields are present

**PDF Not Updating**
- Check browser console for errors
- Verify `working_CV.yaml` is being saved
- Ensure RenderCV can process the YAML
- Check `temp_renders/` directory for error files

### Debug Mode

Enable detailed logging:
```bash
# Run with debug output
python simple_yaml_editor.py --debug

# Check Flask logs in terminal
# Monitor temp_renders/ directory for render attempts
```

## Configuration

### Port Configuration
```python
# Edit simple_yaml_editor.py
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port here
```

### Auto-Save Timing
```javascript
// Edit the JavaScript in simple_yaml_editor.py template
let saveTimeout;
const SAVE_DELAY = 1500;  // Change delay in milliseconds
```

### Theme Selection
```yaml
# In your YAML file, change the theme:
design:
  theme: engineeringresumes  # or sb2nov, classic, etc.
```

## Integration with Resume Agent

### Workflow Integration
1. **AI Tailoring** → Run `python run.py`
2. **Manual Refinement** → Use Simple YAML Editor for fine-tuning
3. **Final Review** → Preview and download final PDF

### File Compatibility
- **Input**: Any RenderCV-compatible YAML file
- **Output**: Standard `working_CV.yaml` format
- **Formats**: PDF, HTML, PNG via RenderCV rendering

### Best Practices
- Use AI tailoring first for major changes
- Use Simple Editor for minor adjustments and formatting
- Always preview before finalizing
- Keep backups of important versions

## Comparison to Other Tools

| Feature | Simple Editor | Full AI Agent |
|---------|---------------|---------------|
| **Speed** | ⚡ Instant | 🔄 2-3 minutes |
| **Control** | 🎯 Complete | 🤖 AI-driven |
| **Learning** | 📚 Hands-on | 🎓 Observational |
| **Use Case** | Fine-tuning | Full tailoring |

### When to Use Simple Editor
- ✅ Quick formatting fixes
- ✅ Manual content adjustments  
- ✅ Learning YAML structure
- ✅ Working without AI/internet
- ✅ Precise control over output

### When to Use AI Agent
- ✅ Major content restructuring
- ✅ Job-specific tailoring
- ✅ Content optimization
- ✅ Skill matching
- ✅ Professional summary updates

## Technical Details

### Architecture
```
Flask App
├── Web Interface (HTML/CSS/JS)
├── YAML Editor (CodeMirror)
├── File System Integration
├── RenderCV Integration
└── Auto-Save System
```

### Dependencies
- **Flask**: Web application framework
- **RenderCV**: Professional resume rendering
- **PyYAML**: YAML file processing
- **Jinja2**: Template rendering (included with Flask)

### File Structure
```
temp_renders/
├── render_YYYYMMDD_HHMMSS/
│   ├── temp_cv.yaml
│   ├── temp_cv.pdf
│   └── temp_cv.html
└── (auto-cleaned old renders)
```

## Security & Privacy

### Local Operation
- **No External Servers**: Runs entirely on your local machine
- **No Data Upload**: Your CV data never leaves your computer
- **Private Files**: All files stored locally in your project directory

### File Safety
- **Auto-Backup**: Previous versions preserved in temp directories
- **Error Recovery**: Graceful handling of corruption or errors
- **Version Control**: Compatible with Git for version tracking

---

## Support

- 🔧 **Issues**: Check browser console and terminal output
- 📖 **Documentation**: This README and inline code comments
- 🌐 **RenderCV Docs**: [Official RenderCV documentation](https://rendercv.com/)
- 🐛 **Debugging**: Use browser developer tools for web interface issues

---

**💡 Tip**: The Simple YAML Editor is perfect for the final polish on your AI-tailored resume. Use it to make those last-minute adjustments that ensure your CV is exactly how you want it!

*Part of the Resume Agent ecosystem - combining AI intelligence with human control for the perfect resume.* 