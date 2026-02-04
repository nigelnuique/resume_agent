from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

# Import utility for Australian English instruction
try:
    from utils import get_australian_english_instruction
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

def tailor_experience(state: ResumeState) -> ResumeState:
    """
    Tailor experience section by reordering and emphasizing relevant experience.
    """
    print("💼 Tailoring experience section...")
    
    try:
        current_experience = state['working_cv']['cv']['sections'].get('experience', [])
        
        if not current_experience:
            print("   ℹ️ No experience section found, skipping...")
            state['experience_tailored'] = True
            return state

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        job_requirements = state['job_requirements']
        
        # Get Australian English instruction if enabled
        au_english_instruction = get_australian_english_instruction() if UTILS_AVAILABLE else ""
        
        prompt = f"""
You are optimising the *Experience* section of a MASTER résumé
to create a *Targeted Résumé* for ONE specific job.{au_english_instruction}

### Context
• The master CV covers the candidate's actual work experience
• The target role is described below – highlight what matters and
  downplay what doesn't.

### Inputs
CURRENT_EXPERIENCE = {current_experience}
JOB_REQUIREMENTS = {{
  "role_focus": {job_requirements.get('role_focus', [])},
  "industry_domain": "{job_requirements.get('industry_domain', 'General')}",
  "key_technologies": {job_requirements.get('key_technologies', [])},
  "essential_requirements": {job_requirements.get('essential_requirements', [])}
}}

### What to do
1. **Relevance Assessment**
   - *Keep*: Roles directly related to the job requirements
   - *Modify*: Roles with transferable skills that can be emphasized
   - *Remove*: Clearly irrelevant roles that don't add value

2. **Content Optimization**
   - Emphasize achievements and skills relevant to the target role
   - Highlight transferable skills (leadership, problem-solving, etc.)
   - Quantify results where possible
   - Focus on impact and outcomes

3. **Role-Specific Guidelines**
   - For technical roles: Emphasize technical skills, projects, and problem-solving
   - For management roles: Emphasize leadership, team management, and strategic thinking
   - For service roles: Emphasize customer service, communication, and problem resolution
   - For creative roles: Emphasize creativity, innovation, and project outcomes

4. **Content Restrictions**
   - DO NOT ADD technical skills to non-technical roles unless they were actually used
   - DO NOT ADD data engineering, SQL, Python, or machine learning content to hardware/testing roles
   - DO NOT ADD software development claims to service/retail roles
   - Hardware/testing roles should focus on testing, quality assurance, and production support
   - Service roles should focus on customer service, communication, and operational tasks

### CRITICAL RULES:
- Base everything on the candidate's ACTUAL experience
- Do NOT invent or inflate responsibilities
- Be honest about the nature of each role
- Focus on transferable skills and genuine achievements
- Maintain chronological order unless reordering improves relevance

### Output (MUST be strict JSON):
{{
  "tailored_experience": [
    {{"company": "...", "position": "...", "start_date": "...", "end_date": "...", "location": "...", "highlights": ["...", "..."]}},
    ...
  ],
  "removed_positions": ["List of removed positions"],
  "changes_summary": "Brief description of what was changed and why"
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Optimize the experience section while maintaining factual accuracy and removing obviously irrelevant positions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content or "", "tailor_experience")
        
        if result is None:
            print("   ⚠️ Could not parse experience optimization - keeping original")
            state['experience_tailored'] = True
            return state
        
        experiences = result.get('tailored_experience', current_experience)
        changes_summary = result.get('changes_summary', 'No changes summary available')
        positions_removed = result.get('removed_positions', [])
        
        # Update the experience section
        state['working_cv']['cv']['sections']['experience'] = experiences
        state['experience_tailored'] = True
        
        print("✅ Experience section tailored successfully")
        if positions_removed:
            print(f"   🗑️ Removed positions: {', '.join(positions_removed)}")
        print(f"   📊 Final experience count: {len(experiences)}")
        print(f"   Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring experience section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Don't fail the entire process if experience tailoring fails
        state['experience_tailored'] = True
    
    return state
