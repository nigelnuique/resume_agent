"""
Professional summary updating with library-based constraint validation.
"""

import os
from typing import Dict, Any, List
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

# Import library-based utilities for validation
try:
    from utils.text_utils import count_words_sentences, validate_summary_constraints
    from utils import get_australian_english_instruction
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    print("⚠️ Summary validation utilities not available")

def update_summary(state: ResumeState) -> ResumeState:
    """
    Update professional summary to align with job requirements.
    CONSTRAINT: 2-4 concise sentences or 40-70 words total.
    """
    print("📝 Updating professional summary...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_summary = state['working_cv']['cv']['sections'].get('professional_summary', [])
        job_requirements = state['job_requirements']
        
        # Get Australian English instruction if enabled
        au_english_instruction = get_australian_english_instruction() if UTILS_AVAILABLE else ""
        
        prompt = f"""
You are updating the *Professional Summary* section of a MASTER résumé
to create a *Targeted Résumé* for ONE specific job.{au_english_instruction}

### Context
• The master CV covers the candidate's actual background and experience
• The target role is described below – highlight what matters and
  downplay what doesn't.

### Inputs
CURRENT_SUMMARY = {current_summary}
JOB_REQUIREMENTS = {{
  "role_focus": {job_requirements.get('role_focus', [])},
  "industry_domain": "{job_requirements.get('industry_domain', 'General')}",
  "key_technologies": {job_requirements.get('key_technologies', [])},
  "essential_requirements": {job_requirements.get('essential_requirements', [])},
  "certifications_required": {job_requirements.get('certifications_required', [])},
  "technical_expertise": {job_requirements.get('technical_expertise', [])},
  "professional_qualifications": {job_requirements.get('professional_qualifications', [])}
}}

### CANDIDATE'S ACTUAL SKILLS (ONLY MENTION THESE):
{state['working_cv']['cv']['sections'].get('skills', [])}

### What to do
1. **Analyze the candidate's actual background**
   - Review their real professional experience and education
   - Identify their genuine strengths and relevant skills
   - Understand their career progression and transitions

2. **Match to job requirements**
   - Highlight experience that directly relates to the role
   - Emphasize transferable skills that apply to the position
   - Connect their background to the job's needs
   - Pay special attention to technical expertise and professional qualifications mentioned in job requirements

3. **Be honest about experience level**
   - If main professional experience is in different field, be honest about this
   - Distinguish between professional experience and academic/project experience
   - Don't inflate experience in areas where they have limited professional background
   - Example: If someone has 3 years in one field + MS in another field, say "Professional transitioning to [new field]" NOT "3+ years in [new field]"

4. **Structure the summary with varied openings**
   - 50-60 words, 2-3 sentences
<<<<<<< HEAD
   - Use natural, varied sentence starters (avoid "Technical professional" or similar generic phrases)
   - Examples of good openings:
     * "Data scientist with experience in..."
     * "Experienced in Python programming and..."
     * "Skilled at building predictive models..."
     * "Passionate about leveraging data to..."
     * "Background in [specific field] with expertise in..."
   - Lead with most relevant experience or skills
   - Include key skills that match job requirements
   - End with enthusiasm for the role
   - If mentioning education, always highlight the most recent and highest degree (e.g., MS over BS).

### CRITICAL RULES:
- Base everything on the candidate's ACTUAL experience in the master CV
- Do NOT invent experience they don't have or inflate experience they do have
- Be honest about their background and transitions
- Focus on transferable skills and genuine qualifications
- Match the tone to the job requirements and company culture
<<<<<<< HEAD
- AVOID generic phrases like "Technical professional", "Experienced professional", "Skilled professional"
- Use specific, varied language that reflects the candidate's actual background
- NEVER use vague headers like "Technical Professional." Use the exact role title from the job ad, or—if that title doesn't match the candidate's background—substitute "[industry] professional," e.g., "Data Professional."
- If the job emphasizes "technical and professional expertise," highlight the candidate's actual technical skills and professional qualifications
- Emphasize relevant certifications, technical skills, and professional credentials that align with the role
- ALTERNATIVES to "Technical Professional": Use specific terms like "Data Science Professional," "Cloud Technology Professional," "Technology Sales Professional," or start with the specific role title from the job advertisement
- If mentioning education, always highlight the most recent and highest degree (e.g., MS over BS).

### ANTI-HALLUCINATION RULES:
- **ONLY mention programming languages, tools, or technologies that are EXPLICITLY listed in the candidate's skills section**
- **NEVER mention skills like Java, C#, .NET, Angular, React, etc. unless they are actually in the skills list**
- **If the job requires skills the candidate doesn't have, focus on transferable skills they DO have**
- **Cross-reference every technical skill mentioned in your summary against the actual skills list**
- **When in doubt about a skill, omit it rather than risk hallucination**
- **Focus on the candidate's genuine strengths rather than trying to match every job requirement**

### Output (MUST be strict JSON):
{{
  "tailored_summary": [
    "A single paragraph (50-60 words) that flows naturally from the candidate's background to their relevant skills and enthusiasm for the role. Use varied, specific language and avoid generic openings."
  ],
  "changes_made": "Brief description of what was changed and why"
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer who prioritizes TRUTHFULNESS above all else. You must carefully analyze the candidate's actual work history and never claim professional experience in domains where they only have academic/project experience. Be honest about career transitions and distinguish clearly between professional work experience vs academic background. CRITICAL: NEVER use 'Technical Professional' as a vague header. Use specific terms like 'Data Science Professional,' 'Cloud Technology Professional,' or the exact job title from the advertisement. If mentioning education, always highlight the most recent and highest degree (e.g., MS over BS). MOST IMPORTANT: NEVER mention programming languages, tools, or technologies that are not explicitly listed in the candidate's skills section. Cross-reference every technical skill against their actual skills list. When in doubt, omit the skill rather than risk hallucination."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content or "", "update_summary")
        
        if result is None:
            fallback_data = {
                'tailored_summary': current_summary,
                'changes_made': "Summary update failed - using original"
            }
            result = create_fallback_response("update_summary", fallback_data)
        
        new_summary = result.get('tailored_summary', current_summary)
        changes_made = result.get('changes_made', "No specific changes documented")
        llm_word_count = result.get('word_count', 0)
        llm_sentence_count = result.get('sentence_count', 0)
        
        # Use library-based validation if available
        if UTILS_AVAILABLE and new_summary:
            validation_result = validate_summary_constraints(new_summary)
            actual_word_count = validation_result['words']
            actual_sentence_count = validation_result['sentences']
            
            print(f"   📊 Length validation:")
            print(f"     - LLM estimated: {llm_word_count} words, {llm_sentence_count} sentences")
            print(f"     - Actual count: {actual_word_count} words, {actual_sentence_count} sentences")
            
            if not validation_result['valid']:
                print(f"   ⚠️ Constraint violations:")
                for issue in validation_result['issues']:
                    print(f"     - {issue}")
                
                # If constraints are significantly violated, try a simpler approach
                if actual_word_count > 80 or actual_sentence_count > 5:
                    print("   🔄 Attempting to fix constraint violations...")
                    # Take first 2-3 sentences and trim if needed
                    if len(new_summary) > 3:
                        new_summary = new_summary[:3]
                    
                    # Re-validate
                    validation_result = validate_summary_constraints(new_summary)
                    actual_word_count = validation_result['words']
                    actual_sentence_count = validation_result['sentences']
                    print(f"   📊 After trimming: {actual_word_count} words, {actual_sentence_count} sentences")
        else:
            # Fallback counting if utils not available
            full_text = ' '.join(new_summary) if isinstance(new_summary, list) else str(new_summary)
            actual_word_count = len(full_text.split())
            actual_sentence_count = len(new_summary) if isinstance(new_summary, list) else 1
        
        # Apply the updated summary
        state['working_cv']['cv']['sections']['professional_summary'] = new_summary
        state['summary_updated'] = True
        
        print("✅ Professional summary updated successfully")
        print(f"   📊 Final metrics: {actual_word_count} words, {actual_sentence_count} sentences")
        print("   📝 Changes made:")
        print(f"     - {changes_made}")
        
        # Show constraint compliance
        if UTILS_AVAILABLE:
            if 40 <= actual_word_count <= 70 and 2 <= actual_sentence_count <= 4:
                print("   ✅ All constraints satisfied")
            else:
                print("   ⚠️ Some constraints may not be fully satisfied")
        
        return state
        
    except Exception as e:
        print(f"❌ Summary update failed: {str(e)}")
        print("   Keeping original summary...")
        state['summary_updated'] = True
        return state
