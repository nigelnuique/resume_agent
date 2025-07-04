from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def smart_split_skills(details: str) -> list:
    """Split a comma-separated skill string, but not inside parentheses."""
    skills = []
    current = ''
    paren_level = 0
    for char in details:
        if char == ',' and paren_level == 0:
            skills.append(current.strip())
            current = ''
        else:
            current += char
            if char == '(':
                paren_level += 1
            elif char == ')':
                paren_level = max(paren_level - 1, 0)
    if current.strip():
        skills.append(current.strip())
    return skills

def tailor_skills(state: ResumeState) -> ResumeState:
    """
    Tailor skills section by reordering and emphasizing relevant skills.
    """
    print("🛠️ Tailoring skills section...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_skills = state['working_cv']['cv']['sections'].get('skills', [])
        job_requirements = state['job_requirements']
        
        # Ensure current_skills is in the correct format
        if not isinstance(current_skills, list):
            print("   ⚠️ Skills section is not a list, skipping tailoring")
            return state
        
        # Validate that skills are in dictionary format
        valid_skills = []
        for skill in current_skills:
            if isinstance(skill, dict) and 'label' in skill and 'details' in skill:
                valid_skills.append(skill)
            else:
                print(f"   ⚠️ Skipping invalid skill entry: {skill}")
        
        if not valid_skills:
            print("   ⚠️ No valid skills found, keeping original format")
            return state
        
        prompt = f"""
You are optimising the *Skills* section of a MASTER résumé
to create a *Targeted Résumé* for ONE specific job.

### Context
• The master CV covers multiple fields (data science, electronics, IT support, customer success, etc.)
• The target role is described below – highlight what matters and downplay/delete what doesn't

### Inputs
CURRENT_SKILLS  = {valid_skills}
JOB_REQUIREMENTS = {{
  "role_focus": {job_requirements.get('role_focus', [])},
  "industry_domain": "{job_requirements.get('industry_domain', 'General')}",
  "key_technologies": {job_requirements.get('key_technologies', [])},
  "essential_requirements": {job_requirements.get('essential_requirements', [])}
}}

### Instructions
1. **Relevance Test**
   - *Must keep*: skills that map directly to essential requirements or ATS keywords
   - *Nice to keep*: top 3-5 transferable/supporting skills that strengthen the application
   - *Remove*: irrelevant, off-topic, or niche skills that dilute focus

2. **Re-categorise & Order**
   - Max 5 categories, max 6 comma-separated items per category
   - Put most critical category first (e.g., "Programming" for software roles)
   - Each skill entry MUST have 'label' and 'details' fields
   - **CRITICAL**: Include ALL relevant skills from the input - do not drop any

3. **ATS Keyword Alignment**
   - Choose phrasing used in the job ad when possible (e.g., "Windows Admin" over "Microsoft OS")

4. **Soft Skills (ONLY if relevant)**
   - Add ONE concise soft-skill line only if role mentions customer onboarding, training, stakeholder communication, etc.
   - Convert trait descriptors to action-oriented capability nouns (e.g., "team player" → "collaboration")
   - Use specific skills like "Technical communication & end-user training"
   - **CRITICAL**: Only include soft skills explicitly mentioned in candidate's experience/education
   - DO NOT invent soft skills based on job requirements alone

5. **Preserve truthfulness**
   - Do NOT invent new technologies; only reorder, rename, or merge existing items
   - Maintain exact same skill names from input
   - Skills must be specific technologies, tools, or methodologies
   - If removing a category, redistribute its legitimate skills to other appropriate categories

### CRITICAL RULES:
- Skills must be specific technologies, tools, or methodologies
- DO NOT use phrases like "Prior experience in..." or "Experience with..."
- DO NOT list job titles or roles (e.g., "IT Support", "technical support")
- DO NOT create generic categories like "IT Support & Customer Success"
- **NEVER drop relevant skills from the original master CV**
- **NEVER invent skills that don't exist in the candidate's background**
- **NEVER create skills based on job requirements alone**

### Output (MUST be strict JSON):
{{
  "tailored_skills": [
    {{"label": "...", "details": "..."}},
    ...
  ],
  "changes_summary": "One- or two-sentence description of what was reordered, merged, or deleted."
}}

### Validation Rules:
- Each skill entry must be a dictionary with 'label' and 'details' fields
- Do not create empty or single-period bullet points
- Maintain factual accuracy - only reorder existing skills
- Skills must be specific technologies, not job descriptions
- All legitimate skills from the original must be preserved
"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Always return valid JSON with the exact structure requested. Each skill must be a dictionary with 'label' and 'details' fields. CRITICAL: Only use skills that actually exist in the candidate's background. NEVER invent or hallucinate skills based on job requirements alone."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        result = safe_json_parse(response.choices[0].message.content or "", "tailor_skills")
        
        if result is None:
            # Provide fallback behavior - keep original skills
            fallback_data = {
                'tailored_skills': valid_skills,
                'changes_summary': 'No changes made due to parsing error - original skills retained'
            }
            result = create_fallback_response("tailor_skills", fallback_data)
        
        tailored_skills = result.get('tailored_skills', valid_skills)
        changes_summary = result.get('changes_summary', 'No changes summary available')
        # Basic validation of the LLM output
        validated_skills = [s for s in tailored_skills if isinstance(s, dict) and 'label' in s and 'details' in s]
        if not validated_skills:
            print("   ⚠️ No valid tailored skills found, keeping original")
            validated_skills = valid_skills
            changes_summary = "No changes made - invalid format"

        
        
        # Update the skills section
        state['working_cv']['cv']['sections']['skills'] = validated_skills
        state['skills_tailored'] = True
        
        print("✅ Skills section tailored successfully")
        print(f"   Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring skills section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state 
