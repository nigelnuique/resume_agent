# YAML CV Editor

A modern, split-screen web application for editing the `working_CV.yaml` file with live PDF preview using RenderCV.

## Features

- **Split-screen Interface**: Left side for YAML editing, right side for PDF preview
- **Syntax Highlighting**: Full YAML syntax highlighting with CodeMirror
- **Live Preview**: Real-time PDF rendering as you edit
- **Watch Mode**: RenderCV v2 watch mode for automatic PDF updates
- **Auto-save**: Optional auto-save functionality with visual indicators
- **Validation**: Built-in YAML syntax validation
- **Responsive Design**: Works on desktop and mobile devices
- **Keyboard Shortcuts**: Quick access to common actions

## Screenshots

The editor provides a clean, modern interface with:
- Dark theme for comfortable editing
- Syntax highlighting for YAML
- Live PDF preview
- Status indicators for all operations
- Auto-save functionality

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install RenderCV** (if not already installed):
   ```bash
   pip install rendercv
   ```

3. **Generate working_CV.yaml** (if not exists):
   ```bash
   python run.py
   ```

## Usage

### Starting the Editor

**Option 1: Use the startup script (recommended)**
```bash
python start_editor.py
```

**Option 2: Run directly**
```bash
python yaml_editor_app.py
```

### Accessing the Editor

1. Open your web browser
2. Navigate to: `http://localhost:5001`
3. The editor will load with the current `working_CV.yaml` content

### Editor Features

#### Left Panel - YAML Editor
- **Syntax Highlighting**: YAML syntax is highlighted in real-time
- **Line Numbers**: Easy navigation with line numbers
- **Auto-completion**: Basic YAML structure assistance
- **Error Detection**: Visual indicators for syntax errors

#### Right Panel - PDF Preview
- **Live Rendering**: PDF updates automatically when you save
- **Full-screen Preview**: PDF displays in full size
- **Error Handling**: Clear error messages if rendering fails

#### Header Controls
- **Toggle Auto-save**: Enable/disable automatic saving
- **Watch Mode**: Start/stop RenderCV v2 watch mode for real-time PDF updates
- **Render PDF**: Manually trigger PDF generation
- **Validate**: Check YAML syntax
- **Cleanup**: Remove old temporary files

### Keyboard Shortcuts

- `Ctrl+S` / `Cmd+S`: Save YAML
- `Ctrl+R` / `Cmd+R`: Render PDF
- `Ctrl+V` / `Cmd+V`: Validate YAML
- `Ctrl+W` / `Cmd+W`: Toggle Watch Mode

### Auto-save Feature

The auto-save feature:
- Saves changes automatically after 2 seconds of inactivity
- Shows visual indicators (saving, saved, error)
- Automatically triggers PDF re-rendering (when watch mode is off)
- Can be toggled on/off

### Watch Mode Feature

The watch mode feature (RenderCV v2):
- Automatically re-renders PDF when YAML file changes
- Uses RenderCV's built-in `--watch` flag
- Provides real-time updates without manual intervention
- Can be started/stopped with a single click

## File Structure

```
Resume_Agent/
├── yaml_editor_app.py      # Main Flask application
├── start_editor.py         # Startup script with dependency checks
├── templates/
│   └── editor.html         # HTML template for the editor
├── temp_renders/           # Temporary PDF files (auto-created)
├── working_CV.yaml         # The YAML file being edited
└── rendercv_output/        # Final rendered files
```

## API Endpoints

The editor provides several REST API endpoints:

- `GET /api/yaml` - Get current YAML content
- `POST /api/yaml` - Save YAML content
- `POST /api/render` - Render PDF
- `GET /api/pdf/<filename>` - Serve generated PDF
- `POST /api/validate` - Validate YAML syntax
- `POST /api/cleanup` - Clean up temporary files

## Configuration

### Environment Variables

The app uses the following configuration:

- `WORKING_CV_FILE`: Path to the YAML file (default: "working_CV.yaml")
- `RENDERCV_OUTPUT_DIR`: Output directory for rendered files (default: "rendercv_output")
- `TEMP_DIR`: Temporary directory for renders (default: "temp_renders")

### Customization

You can modify the app by editing `yaml_editor_app.py`:

1. **Change Port**: Modify the port in the `app.run()` call
2. **Change Theme**: Update the CodeMirror theme in `editor.html`
3. **Add Features**: Extend the YAMLEditor class with new functionality

## Troubleshooting

### Common Issues

1. **RenderCV not found**
   ```
   Error: RenderCV not found. Please install it first.
   ```
   **Solution**: Install RenderCV with `pip install rendercv`

2. **working_CV.yaml not found**
   ```
   Error: Working CV file not found
   ```
   **Solution**: Run the resume agent first or create the file manually

3. **PDF rendering fails**
   ```