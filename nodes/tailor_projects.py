from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def tailor_projects(state: ResumeState) -> ResumeState:
    """
    Tailor projects section by selecting top 4 most relevant projects and optimizing their content.
    """
    print("🚀 Tailoring projects section (limiting to 4 most relevant)...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_projects = state['working_cv']['cv']['sections'].get('projects', [])
        job_requirements = state['job_requirements']
        
        prompt = f"""
You are optimising the *Projects* section of a MASTER résumé
to create a *Targeted Résumé* for ONE specific job.

### Context
• The master CV contains the candidate's actual projects
• The target role is described below – highlight what matters and
  downplay what doesn't.

### Inputs
CURRENT_PROJECTS = {current_projects}
JOB_REQUIREMENTS = {{
  "role_focus": {job_requirements.get('role_focus', [])},
  "industry_domain": "{job_requirements.get('industry_domain', 'General')}",
  "key_technologies": {job_requirements.get('key_technologies', [])},
  "essential_requirements": {job_requirements.get('essential_requirements', [])}
}}

### What to do
1. **Project Selection**
   - Select the most relevant projects (max 4-5)
   - Prioritize projects that demonstrate skills required for the job
   - Remove projects that don't align with the role requirements

2. **Content Optimization**
   - Emphasize technologies and skills relevant to the job
   - Highlight quantifiable results and impact
   - Focus on problem-solving and technical implementation
   - Keep descriptions concise and impactful

3. **Technology Accuracy**
   - Only mention technologies that were actually used in the project
   - Do NOT add technologies that weren't part of the original project
   - If original project used only SQL, do NOT add Python, pandas, or other technologies
   - Example: If original says "using SQL", do NOT change to "using SQL, Python, and pandas"

4. **Project Types**
   - Technical projects: Emphasize technical skills, algorithms, and problem-solving
   - Data projects: Emphasize data analysis, visualization, and insights
   - Web projects: Emphasize full-stack development, user experience, and deployment
   - Research projects: Emphasize methodology, analysis, and findings

### CRITICAL RULES:
- Base everything on the candidate's ACTUAL projects
- Do NOT invent new projects or technologies
- Maintain factual accuracy about what was actually built
- Focus on transferable skills and genuine achievements
- Keep project links and names intact

### Output (MUST be strict JSON):
{{
  "tailored_projects": [
    {{"name": "...", "end_date": "...", "summary": "...", "highlights": ["...", "..."], "link": "..."}},
    ...
  ],
  "projects_removed": ["List of removed projects"],
  "changes_summary": "Brief description of what was changed and why"
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": "You are an expert resume writer who prioritizes TRUTHFULNESS. Never add inflated claims about professional collaboration or production deployment for academic/personal projects. Focus on actual technical skills demonstrated."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse the response
        result = safe_json_parse(response.choices[0].message.content, "tailor_projects")
        
        if result is None:
            # Provide fallback behavior - keep original projects
            fallback_data = {
                'tailored_projects': current_projects,
                'projects_removed': [],
                'changes_summary': 'No changes made due to parsing error - original projects retained'
            }
            result = create_fallback_response("tailor_projects", fallback_data)
        
        tailored_projects = result.get('tailored_projects', current_projects)
        changes_summary = result.get('changes_summary', 'No changes summary available')
        projects_removed = result.get('projects_removed', [])
        
        # Update the projects section
        state['working_cv']['cv']['sections']['projects'] = tailored_projects
        state['projects_tailored'] = True
        
        print("✅ Projects section tailored successfully")
        print(f"   - Projects selected: {len(tailored_projects)}")
        if projects_removed:
            print(f"   - Projects removed: {len(projects_removed)}")
            print(f"   - Removed: {', '.join(projects_removed)}")
        print(f"   - Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring projects section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
