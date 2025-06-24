from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def tailor_education(state: ResumeState) -> ResumeState:
    """
    Tailor education section by consolidating coursework within highlights and emphasizing relevant achievements.
    """
    print("🎓 Tailoring education section (consolidating coursework into single highlight lines)...")
    
    try:
        current_education = state['working_cv']['cv']['sections'].get('education', [])
        
        if not current_education:
            print("   ℹ️ No education section found, skipping...")
            state['education_tailored'] = True
            return state
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        job_requirements = state['job_requirements']
        
        prompt = f"""
You are optimising the *Education* section of a MASTER résumé
to create a *Targeted Résumé* for ONE specific job.

### Context
• The master CV contains the candidate's actual education history
• The target role is described below – highlight what matters and
  downplay what doesn't.

### Inputs
CURRENT_EDUCATION = {current_education}
JOB_REQUIREMENTS = {{
  "role_focus": {job_requirements.get('role_focus', [])},
  "industry_domain": "{job_requirements.get('industry_domain', 'General')}",
  "key_technologies": {job_requirements.get('key_technologies', [])},
  "essential_requirements": {job_requirements.get('essential_requirements', [])}
}}

### What to do
1. **Coursework Selection**
   - Select the most relevant coursework (max 5 courses per institution)
   - Prioritize courses that align with job requirements
   - Remove irrelevant courses that don't add value

2. **Content Optimization**
   - Keep all factual information (institution, degree, dates, GPA, etc.)
   - Optimize coursework highlights to emphasize relevant skills
   - Maintain academic achievements and honors
   - Keep thesis/capstone project descriptions intact

3. **Relevance Guidelines**
   - Technical roles: Emphasize technical coursework, programming, algorithms
   - Business roles: Emphasize business, management, and analytical courses
   - Creative roles: Emphasize design, communication, and creative courses
   - Research roles: Emphasize research methodology, analysis, and specialized courses

### CRITICAL RULES:
- Base everything on the candidate's ACTUAL education
- Do NOT invent courses or institutions
- Maintain factual accuracy about degrees, dates, and achievements
- Keep all academic honors, GPA, and scholarships
- Preserve thesis and capstone project descriptions

### Output (MUST be strict JSON):
{{
  "tailored_education": [
    {{"institution": "...", "area": "...", "degree": "...", "start_date": "...", "end_date": "...", "location": "...", "highlights": ["...", "..."]}},
    ...
  ],
  "changes_summary": "Brief description of what was changed and why"
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Keep coursework as highlight bullet points, NOT separate fields. NEVER truncate existing descriptions - preserve full text of capstone projects and thesis descriptions exactly as they are. Only include relevant coursework if there are actually relevant courses (0-5 max). If no courses are relevant, omit the coursework highlight entirely."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_education")
        
        if result is None:
            print("   ⚠️ Could not parse education optimization - keeping original")
            state['education_tailored'] = True
            return state
        
        education_entries = result.get('tailored_education', current_education)
        changes_summary = result.get('changes_summary', 'No changes summary available')
        
        # Update the education section
        state['working_cv']['cv']['sections']['education'] = education_entries
        state['education_tailored'] = True
        
        print("✅ Education section tailored successfully")
        print(f"   - Education entries: {len(education_entries)}")
        print(f"   - Real institutions preserved: {', '.join([entry.get('institution', 'Unknown') for entry in education_entries])}")
        print(f"   - Coursework kept as highlight bullet points")
        print(f"   - Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring education section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Don't fail the entire process if education tailoring fails
        state['education_tailored'] = True
    
    return state
