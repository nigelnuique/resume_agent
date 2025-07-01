# Resume Agent Web UI - Usage Guide

## Quick Start

1. **Launch the UI**:
   ```bash
   python start_ui.py
   ```
   Or double-click `start_ui.bat` on Windows.

2. **Open your browser**: Go to `http://localhost:5000`

3. **Follow the 2-step workflow**:
   - **Step 1**: Input your data
   - **Step 2**: Make final edits

## Step-by-Step Workflow

### Step 1: Input Your Data

1. **Master CV**: Upload your CV file (.yaml/.yml) or paste YAML content directly
2. **Job Advertisement**: Copy and paste the complete job posting
3. **Click "Process with AI"**: The system will analyze and tailor your resume

### AI Processing (Automatic)

Watch the progress bar as the AI:
- Analyzes job requirements
- Optimizes section order
- Updates professional summary
- Tailors experience, projects, education
- Validates final output

### Step 2: Final Editing

Once AI processing completes:
- **Left Panel**: Edit your resume YAML directly
- **Right Panel**: Live PDF preview updates automatically
- **Auto-save**: Changes save after 1.5 seconds of inactivity
- **Download**: Get your final resume in YAML and PDF formats

## Key Features

### 🔄 Real-time Updates
- PDF preview refreshes as you type
- Syntax highlighting for YAML
- Error detection and highlighting

### 📁 File Management
- Upload CV files directly
- Download tailored resume files
- Auto-save prevents data loss

### 🎯 AI-Powered Tailoring
- Job requirement analysis
- Section prioritization
- Content optimization
- Skills alignment

## Tips for Best Results

### Master CV Preparation
- Use the provided `master_CV_template.yaml` as a starting point
- Include all your skills, experience, and achievements
- Keep content accurate and comprehensive

### Job Advertisement Input
- Copy the complete job posting (not just requirements)
- Include company information if available
- Don't edit or summarize the job ad

### Final Editing
- Review AI changes carefully
- Adjust content for better flow
- Ensure accuracy of all information
- Check for any remaining placeholders

## Troubleshooting

### Common Issues

**"OpenAI API key not found"**
- Create a `.env` file in the project directory
- Add: `OPENAI_API_KEY=your-key-here`
- Get your key from: https://platform.openai.com/api-keys

**"PDF rendering failed"**
- Check YAML syntax (left panel will show errors)
- Ensure all required CV sections are present
- Try refreshing the page

**"Workflow failed"**
- Check your internet connection
- Verify your OpenAI API key is valid
- Ensure you have API credits available

### Getting Help

1. Check the console for error messages
2. Verify all requirements are installed: `pip install -r requirements.txt`
3. Make sure you're using Python 3.7+
4. Check the main README.md for detailed troubleshooting

## Advanced Usage

### Custom Templates
- Modify `master_CV_template.yaml` for your industry
- Add custom sections as needed
- Follow RenderCV format specifications

### Multiple Jobs
- Save different versions of your tailored resumes
- Use descriptive filenames
- Keep track of which resume was sent where

### API Limits
- OpenAI has usage limits and costs
- Monitor your API usage at platform.openai.com
- Consider using GPT-3.5-turbo for cost savings (change in .env file)

## File Structure After Use

```
resume_agent/
├── master_CV.yaml          # Your original CV
├── job_advertisement.txt   # Job posting text
├── working_CV.yaml         # AI-tailored version
├── temp_renders/           # Temporary PDF files
└── rendercv_output/        # Final output files
```

## Next Steps

- Review the tailored resume carefully
- Compare with the original job posting
- Make final adjustments as needed
- Save your work and apply with confidence!

---

💡 **Pro Tip**: Keep your master CV updated with new skills and experiences to get better tailoring results for future applications. 