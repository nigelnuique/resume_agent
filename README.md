# Resume Agent - AI-Powered Resume Tailoring System

An intelligent resume tailoring system that automatically customizes your CV based on job advertisements using LangGraph and OpenAI's GPT-4.

## Overview

Resume Agent uses a multi-step AI workflow to analyze job advertisements and tailor your resume accordingly, ensuring maximum relevance and impact while maintaining accuracy and professionalism.

## Features

- **Job Advertisement Analysis**: Extracts key requirements, technologies, and company culture from job postings
- **Section Reordering**: Prioritizes resume sections based on job requirements
- **Content Tailoring**: Customizes professional summary, experience, projects, education, and skills
- **Cross-Reference Validation**: Ensures consistency and eliminates unsupported claims
- **Grammar & Tone Optimization**: Polishes language to match company culture
- **Australian English Conversion**: Standardizes spelling for Australian job market
- **YAML Validation**: Ensures RenderCV compatibility
- **Automated Rendering**: Generates PDF, HTML, and other formats using RenderCV

## System Architecture

```
Resume Agent/
├── nodes/                    # Processing nodes
│   ├── parse_job_ad.py      # Job advertisement analysis
│   ├── reorder_sections.py  # Section prioritization
│   ├── update_summary.py    # Professional summary tailoring
│   ├── tailor_experience.py # Experience section optimization
│   ├── tailor_projects.py   # Projects section customization
│   ├── tailor_education.py  # Education section tailoring
│   ├── tailor_skills.py     # Skills section optimization
│   ├── cross_reference_check.py    # Consistency validation
│   ├── resolve_inconsistencies.py # Automatic inconsistency resolution
│   ├── grammar_tone_check.py       # Language optimization
│   ├── convert_au_english.py    # Spelling standardization
│   └── validate_yaml.py         # RenderCV compatibility check
├── state.py                 # Shared state management
├── run.py                   # Main orchestration script
├── master_CV.yaml          # Your master resume
├── job_advertisement.txt   # Target job posting
├── working_CV.yaml        # Generated tailored resume
└── rendercv_output/       # Rendered resume files
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Resume_Agent.git
   cd Resume_Agent
   ```
   
   **Or create a new project directory**:
   ```bash
   mkdir Resume_Agent
   cd Resume_Agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   **Note:** The requirements now specify `rendercv[full]` to ensure all rendering features are available. If you install manually, use:
   ```bash
   pip install "rendercv[full]"
   ```

3. **Set up OpenAI API key**:
   ```bash
   # Option 1: Use the setup script (recommended)
   python setup_env.py
   
   # Then edit .env file and add your actual API key
   
   # Option 2: Manual setup
   cp env_template.txt .env
   # Edit .env file and replace 'your-openai-api-key-here' with your actual key
   
   # Option 3: Environment variable (traditional method)
   export OPENAI_API_KEY='your-openai-api-key-here'
   ```
   
   Get your OpenAI API key from: https://platform.openai.com/api-keys

## Usage

1. **Prepare your master resume**:
   ```bash
   # Copy the template and customize it with your information
   cp master_CV_template.yaml master_CV.yaml
   # Edit master_CV.yaml with your complete professional information
   ```
   - Use the provided template as a guide
   - Ensure all dates, companies, and achievements are accurate

2. **Add the job advertisement**:
   ```bash
   # Copy the template and add your target job posting
   cp job_advertisement_template.txt job_advertisement.txt
   # Edit job_advertisement.txt with the actual job posting
   ```
   - Include all relevant details (requirements, responsibilities, company culture)

3. **Run the tailoring process**:
   ```bash
   python run.py
   ```

4. **Review outputs**:
   - `working_CV.yaml`: Your tailored resume in YAML format
   - `rendercv_output/`: Rendered files (PDF, HTML, etc.)

## Workflow Steps

1. **Parse Job Advertisement**: Extracts requirements, technologies, and cultural indicators
2. **Reorder Sections**: Prioritizes sections based on job emphasis
3. **Update Summary**: Tailors professional summary to match role
4. **Tailor Experience**: Reorders and optimizes experience entries
5. **Tailor Projects**: Emphasizes relevant project experience
6. **Tailor Education**: Highlights relevant academic achievements
7. **Tailor Skills**: Matches skill terminology and removes irrelevant items
8. **Cross-Reference Check**: Validates consistency across sections
9. **Resolve Inconsistencies**: Automatically fixes unsupported claims and inconsistencies
10. **Grammar & Tone Check**: Polishes language and tone
11. **Convert to Australian English**: Standardizes spelling
12. **Validate YAML**: Ensures RenderCV compatibility

## Configuration

### Environment Variables (.env file)
Create a `.env` file in the project root with the following variables:

- `OPENAI_API_KEY`: Required for AI-powered content generation
- `OPENAI_MODEL`: Optional, defaults to 'gpt-4'
- `OPENAI_TEMPERATURE`: Optional, controls AI response randomness (0.0-1.0)
- `DEBUG`: Optional, enables debug mode (true/false)

**Quick Setup:**
```bash
python setup_env.py  # Creates .env from template
# Then edit .env and add your actual API key
```

### Customization Options
- Modify node logic in `nodes/` directory for custom tailoring rules
- Adjust workflow sequence in `run.py` for different processing orders
- Update `master_CV.yaml` template structure as needed

## Best Practices

1. **Master Resume Quality**: Ensure your master resume is comprehensive and accurate
2. **Job Advertisement Detail**: Include complete job postings for better analysis
3. **Review Generated Content**: Always review AI-generated changes before submission
4. **Maintain Truthfulness**: The system emphasizes accuracy over embellishment
5. **Regular Updates**: Keep your master resume current with new experiences

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**:
   - Verify API key is set correctly
   - Check API usage limits and billing
   - Ensure internet connectivity

2. **YAML Validation Errors**:
   - Check for proper indentation in master_CV.yaml
   - Ensure required fields are present
   - Validate YAML syntax

3. **RenderCV Rendering Issues**:
   - Verify RenderCV installation: `python -m rendercv --version` (use this instead of `rendercv --version` if the command is not found)
   - If you see a message about partial installation, run: `pip install "rendercv[full]"`
   - Check for unsupported characters or formatting
   - Review generated working_CV.yaml for issues

### Debug Mode
Run with detailed logging:
```bash
python -u run.py 2>&1 | tee tailoring.log
```

## Output Files

- **working_CV.yaml**: Tailored resume in RenderCV format
- **rendercv_output/**: Directory containing:
  - PDF version of your tailored resume
  - HTML version for web viewing
  - PNG images of resume pages
  - Markdown version for further editing

## Technical Details

### Dependencies
- **LangGraph**: Workflow orchestration and state management
- **OpenAI**: GPT-4 for most nodes; `parse_job_ad` uses GPT-3.5-turbo
- **RenderCV**: Professional resume rendering
- **PyYAML**: YAML file processing

### AI Model Usage
- **GPT-4**: Default model for resume tailoring and optimization
- **GPT-3.5-turbo**: Used by `parse_job_ad` for job ad analysis
- **Temperature Settings**: Optimized for consistent, professional output
- **Token Management**: Efficient prompting to minimize API costs

## Contributing

To extend the system:

1. **Add new nodes**: Create new processing steps in `nodes/` directory
2. **Modify workflow**: Update `run.py` to include new nodes
3. **Enhance validation**: Add new checks to `validate_yaml.py`
4. **Improve templates**: Customize resume templates in RenderCV themes

## License

This project is provided as-is for educational and professional use. Please respect OpenAI's usage policies when using the API.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review error messages in the console output
3. Validate your master_CV.yaml file structure
4. Ensure all dependencies are properly installed

## Contributing to GitHub

If you want to share your improvements or fork this project:

### **Setting Up Your Own Repository**

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Resume Agent"
   ```

2. **Create a GitHub repository** and push:
   ```bash
   # Create repository on GitHub first, then:
   git remote add origin https://github.com/yourusername/Resume_Agent.git
   git branch -M main
   git push -u origin main
   ```

### **Files Automatically Excluded**

The `.gitignore` file automatically excludes:
- ✅ **`.env`** - Your API keys (never committed)
- ✅ **`master_CV.yaml`** - Your personal resume data
- ✅ **`job_advertisement.txt`** - Your target job postings
- ✅ **`working_CV.yaml`** - Generated tailored resumes
- ✅ **`rendercv_output/`** - All rendered PDF/HTML files
- ✅ **Python cache files** and other temporary files

### **Template Files Included**

These files **are** included for other users:
- ✅ **`master_CV_template.yaml`** - Resume template for users to copy
- ✅ **`job_advertisement_template.txt`** - Job posting template
- ✅ **`env_template.txt`** - Environment variables template
- ✅ **All source code files** - The complete Resume Agent system

### **Before Pushing to GitHub**

```bash
# Verify what will be committed (should not show personal files)
git status

# Should NOT show:
# - .env
# - master_CV.yaml  
# - job_advertisement.txt
# - working_CV.yaml
# - rendercv_output/

# Should show:
# - All .py files
# - Template files
# - README.md
# - requirements.txt
# - .gitignore
```

---

**Note**: This system is designed to assist with resume tailoring, not replace human judgment. Always review and verify the generated content before submitting applications. 