from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response
import re

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
• The master CV covers multiple fields (data science, electronics,
  IT support, customer success, etc.).
• The target role is described below – highlight what matters and
  downplay / delete what doesn't.

### Inputs
CURRENT_SKILLS  = {valid_skills}
JOB_REQUIREMENTS = {{
  "role_focus": {job_requirements.get('role_focus', [])},
  "industry_domain": "{job_requirements.get('industry_domain', 'General')}",
  "key_technologies": {job_requirements.get('key_technologies', [])},
  "essential_requirements": {job_requirements.get('essential_requirements', [])}
}}

### What to do
1. **Relevance Test**
   - *Must keep*: skills that map directly to essential requirements
     or obvious ATS keywords in the ad.
   - *Nice to keep*: transferable or supporting skills (keep only the
     top 3-5 that strengthen the application).
   - *Remove/merge*: clearly off-topic or niche stacks that dilute focus.

2. **Re-categorise & Order**
   - Max 5 categories. Within each, max 6 comma-separated items.
   - Put the most critical category first (e.g., "Programming" for a
     software role, "Tools" for a support role).
   - Each skill entry MUST have 'label' and 'details' fields.
   - **CRITICAL**: You MUST include ALL legitimate skills from the input.
     Do not drop any skills that exist in the original master CV.

3. **ATS Keyword Alignment**
   - Where a skill can be labelled two ways, choose the phrasing used
     in the job ad (e.g., "Windows Admin" over "Microsoft OS" if that
     matches the posting).

4. **Soft Skills (ONLY if relevant)**
   - If the role mentions customer onboarding, training, stakeholder
     communication, etc., add ONE concise soft-skill line.
   - Use specific skills like "Technical communication & end-user training"
   - DO NOT use generic phrases like "Prior experience in..." or list job titles.

5. **Preserve truthfulness**
   - Do **not** invent new technologies; only reorder, rename,
     or merge existing items.
   - Maintain the exact same skill names from the input.
   - Skills should be specific technologies, tools, or methodologies.
   - **IMPORTANT**: If you remove a category, make sure to redistribute
     its legitimate skills to other appropriate categories.

### CRITICAL RULES:
- Skills must be specific technologies, tools, or methodologies
- DO NOT use phrases like "Prior experience in..." or "Experience with..."
- DO NOT list job titles or roles (e.g., "IT Support", "technical support")
- DO NOT create generic categories like "IT Support & Customer Success"
- If you can't create a proper soft skills category, don't create one at all
- **NEVER drop legitimate skills from the original master CV**

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
                {"role": "system", "content": "You are an expert resume writer. Always return valid JSON with the exact structure requested. Each skill must be a dictionary with 'label' and 'details' fields."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_skills")
        
        if result is None:
            # Provide fallback behavior - keep original skills
            fallback_data = {
                'tailored_skills': valid_skills,
                'changes_summary': 'No changes made due to parsing error - original skills retained'
            }
            result = create_fallback_response("tailor_skills", fallback_data)
        
        tailored_skills = result.get('tailored_skills', valid_skills)
        changes_summary = result.get('changes_summary', 'No changes summary available')
        
        # Validate that the tailored skills maintain the correct format
        validated_skills = []
        original_skill_names = set()
        
        # Extract all skill names from the original master CV
        for skill in valid_skills:
            if 'details' in skill:
                skill_names = smart_split_skills(skill['details'])
                original_skill_names.update(skill_names)
        
        def is_valid_skill_variation(skill_name: str, original_skills: set) -> bool:
            """Check if a skill name is a valid variation of an original skill."""
            # Direct match
            if skill_name in original_skills:
                return True
            
            # Check for common variations
            for original_skill in original_skills:
                # Handle cases like "OpenAI" vs "OpenAI SDK" - only if the base name matches
                if skill_name.startswith(original_skill + " ") or original_skill.startswith(skill_name + " "):
                    return True
                # Handle cases with different spacing or punctuation
                if skill_name.replace(' ', '').replace('-', '').replace('_', '') == original_skill.replace(' ', '').replace('-', '').replace('_', ''):
                    return True
                # Handle cases like "AWS" vs "AWS (basic)" - only if the base name is the same
                if skill_name == original_skill.split('(')[0].strip() or original_skill == skill_name.split('(')[0].strip():
                    return True
            
            return False
        
        for skill in tailored_skills:
            if isinstance(skill, dict) and 'label' in skill and 'details' in skill:
                # Check if all skills in this entry exist in the original
                skill_names = smart_split_skills(skill['details'])
                valid_skill_names = []
                
                for skill_name in skill_names:
                    if is_valid_skill_variation(skill_name, original_skill_names):
                        valid_skill_names.append(skill_name)
                    else:
                        print(f"   ⚠️ Removed hallucinated skill: {skill_name}")
                
                if valid_skill_names:
                    skill_copy = skill.copy()
                    skill_copy['details'] = ', '.join(valid_skill_names)
                    validated_skills.append(skill_copy)
                else:
                    print(f"   ⚠️ Removed entire skill category due to hallucination: {skill['label']}")
            else:
                print(f"   ⚠️ LLM returned invalid skill format: {skill}")
        
        if not validated_skills:
            print("   ⚠️ No valid tailored skills, keeping original")
            validated_skills = valid_skills
            changes_summary = "No changes made - LLM response validation failed"
        
        # Fallback: Check if any legitimate skills were lost and redistribute them
        original_skill_names = set()
        for skill in valid_skills:
            if 'details' in skill:
                skill_names = smart_split_skills(skill['details'])
                original_skill_names.update(skill_names)
        
        validated_skill_names = set()
        for skill in validated_skills:
            if 'details' in skill:
                skill_names = smart_split_skills(skill['details'])
                validated_skill_names.update(skill_names)
        
        # Find missing legitimate skills
        missing_skills = original_skill_names - validated_skill_names
        
        # Filter missing skills to only include relevant ones for the job
        relevant_missing_skills = set()
        job_keywords = set()
        
        # Extract keywords from job requirements for relevance checking
        for req in job_requirements.get('essential_requirements', []):
            job_keywords.update(req.lower().split())
        for tech in job_requirements.get('key_technologies', []):
            job_keywords.update(tech.lower().split())
        for focus in job_requirements.get('role_focus', []):
            job_keywords.update(focus.lower().split())
        
        # Check each missing skill for relevance
        for skill_name in missing_skills:
            skill_lower = skill_name.lower()
            
            # Skip obviously irrelevant skills based on common patterns
            irrelevant_patterns = [
                # Electronics/hardware (for software/tech roles)
                'circuit', 'oscilloscope', 'signal generator', 'microcontroller', 
                'arduino', 'stm32', 'pcb', 'altium', 'breadboard', 'soldering',
                # Manufacturing/mechanical (for software/tech roles)
                'cnc', 'lathe', 'welding', 'machining', 'assembly line',
                # Medical/healthcare specific (unless job is in healthcare)
                'patient', 'diagnosis', 'treatment', 'medical device',
                # Legal specific (unless job is in legal)
                'litigation', 'contract', 'legal research', 'case law',
                # Finance specific (unless job is in finance)
                'trading', 'portfolio', 'investment', 'financial modeling'
            ]
            
            # Check if skill matches job keywords
            matches_job_keywords = any(keyword in skill_lower for keyword in job_keywords)
            
            # Check if skill is in irrelevant patterns
            is_irrelevant = any(pattern in skill_lower for pattern in irrelevant_patterns)
            
            # For electronics skills, be extra strict - only include if explicitly mentioned in job
            if is_irrelevant:
                # Check if the job specifically mentions electronics/hardware
                electronics_job_keywords = ['electronics', 'hardware', 'circuit', 'embedded', 'iot', 'microcontroller', 'arduino']
                job_mentions_electronics = any(elec_keyword in ' '.join(job_keywords) for elec_keyword in electronics_job_keywords)
                
                if not job_mentions_electronics:
                    print(f"   ⚠️ Skipping irrelevant skill for this role: {skill_name}")
                    continue
            
            # Include skill if it matches job keywords or doesn't match irrelevant patterns
            relevant_missing_skills.add(skill_name)
        
        if relevant_missing_skills:
            print(f"   ⚠️ Found missing relevant skills: {relevant_missing_skills}")
            # Intelligently redistribute missing skills based on their content
            for skill_name in relevant_missing_skills:
                skill_lower = skill_name.lower()
                
                # Determine appropriate category based on skill content analysis
                if any(cloud_term in skill_lower for cloud_term in ['aws', 'azure', 'google cloud', 'cloud', 'gcp', 'ec2', 'lambda', 's3', 'bigquery']):
                    # Cloud category
                    cloud_category = next((s for s in validated_skills if s['label'].lower() in ['cloud', 'cloud platforms', 'infrastructure']), None)
                    if cloud_category:
                        cloud_category['details'] += f", {skill_name}"
                    else:
                        validated_skills.append({'label': 'Cloud', 'details': skill_name})
                elif any(prog_term in skill_lower for prog_term in ['python', 'java', 'javascript', 'sql', 'git', 'html', 'css', 'react', 'node', 'flask', 'django', 'programming', 'coding']):
                    # Programming category
                    prog_category = next((s for s in validated_skills if s['label'].lower() in ['programming', 'languages', 'development']), None)
                    if prog_category:
                        prog_category['details'] += f", {skill_name}"
                    else:
                        validated_skills.append({'label': 'Programming', 'details': skill_name})
                elif any(ai_term in skill_lower for ai_term in ['ai', 'ml', 'machine learning', 'deep learning', 'neural', 'tensorflow', 'pytorch', 'scikit', 'llm', 'openai', 'huggingface']):
                    # AI & ML category
                    ai_category = next((s for s in validated_skills if s['label'].lower() in ['ai & ml', 'machine learning', 'artificial intelligence', 'ai/ml']), None)
                    if ai_category:
                        ai_category['details'] += f", {skill_name}"
                    else:
                        validated_skills.append({'label': 'AI & ML', 'details': skill_name})
                elif any(viz_term in skill_lower for viz_term in ['tableau', 'plotly', 'matplotlib', 'seaborn', 'visualization', 'dashboard', 'chart', 'power bi', 'powerbi']):
                    # Visualization category
                    viz_category = next((s for s in validated_skills if s['label'].lower() in ['visualization', 'visualisation', 'dashboards']), None)
                    if viz_category:
                        # Normalize Power BI spelling for consistency
                        if skill_name.lower() in ['powerbi']:
                            skill_name = 'Power BI'
                        viz_category['details'] += f", {skill_name}"
                    else:
                        # Normalize Power BI spelling for consistency
                        if skill_name.lower() in ['powerbi']:
                            skill_name = 'Power BI'
                        validated_skills.append({'label': 'Visualization', 'details': skill_name})
                else:
                    # Tools/Other category as fallback
                    tools_category = next((s for s in validated_skills if s['label'].lower() in ['tools', 'technologies', 'software', 'platforms']), None)
                    if tools_category:
                        tools_category['details'] += f", {skill_name}"
                    else:
                        validated_skills.append({'label': 'Tools', 'details': skill_name})
            print(f"   ✅ Redistributed {len(relevant_missing_skills)} relevant missing skills")
        elif missing_skills:
            print(f"   ℹ️ Skipped {len(missing_skills)} potentially irrelevant missing skills for this role")
        
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