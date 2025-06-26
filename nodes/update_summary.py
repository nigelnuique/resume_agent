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
        
        prompt = f"""
You are updating the *Professional Summary* section of a MASTER résumé
to create a *Targeted Résumé* for ONE specific job.

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
  "essential_requirements": {job_requirements.get('essential_requirements', [])}
}}

### What to do
1. **Analyze the candidate's actual background**
   - Review their real professional experience and education
   - Identify their genuine strengths and relevant skills
   - Understand their career progression and transitions

2. **Match to job requirements**
   - Highlight experience that directly relates to the role
   - Emphasize transferable skills that apply to the position
   - Connect their background to the job's needs

3. **Be honest about experience level**
   - If main professional experience is in different field, be honest about this
   - Distinguish between professional experience and academic/project experience
   - Don't inflate experience in areas where they have limited professional background
   - Example: If someone has 3 years in one field + MS in another field, say "Professional transitioning to [new field]" NOT "3+ years in [new field]"

4. **Structure the summary**
   - 50-60 words, 2-3 sentences
   - Lead with most relevant experience
   - Include key skills that match job requirements
   - End with enthusiasm for the role

### CRITICAL RULES:
- Base everything on the candidate's ACTUAL experience in the master CV
- Do NOT invent or inflate experience they don't have
- Be honest about their background and transitions
- Focus on transferable skills and genuine qualifications
- Match the tone to the job requirements and company culture
- Do not describe the candidate with a generic title, use a title based on the job ad

### Output (MUST be strict JSON):
{{
  "tailored_summary": [
    "A single paragraph (50-60 words) that flows naturally from the candidate's background to their relevant skills and enthusiasm for the role. This should be written as one continuous paragraph that will be displayed as a single block of text."
  ],
  "changes_made": "Brief description of what was changed and why"
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer who prioritizes TRUTHFULNESS above all else. You must carefully analyze the candidate's actual work history and never claim professional experience in domains where they only have academic/project experience. Be honest about career transitions and distinguish clearly between professional work experience vs academic background."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content, "update_summary")
        
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
