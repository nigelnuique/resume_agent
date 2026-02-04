"""
Combined summary and skills tailoring to ensure perfect alignment.
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

def validate_summary_skills_alignment(summary: List[str], skills: List[str]) -> List[str]:
    """
    Validate that every technical skill mentioned in the summary exists in the skills section.
    
    Args:
        summary: List of summary sentences
        skills: List of skills
        
    Returns:
        List of alignment issues found (empty if perfect alignment)
    """
    import re
    
    # Combine summary into single text
    summary_text = ' '.join(summary) if isinstance(summary, list) else str(summary)
    summary_text = summary_text.lower()
    
    # Combine skills into single text for matching
    skills_text = ' '.join(skills) if isinstance(skills, list) else str(skills)
    skills_text = skills_text.lower()
    
    # Common technical terms that should be validated
    technical_patterns = [
        r'\bpython\b', r'\bjava\b', r'\bc#\b', r'\bc\+\+\b', r'\bjavascript\b', r'\btypescript\b',
        r'\breact\b', r'\bangular\b', r'\bvue\b', r'\bnode\.?js\b', r'\bexpress\b',
        r'\bsql\b', r'\bmysql\b', r'\bpostgresql\b', r'\bmongodb\b', r'\bredis\b',
        r'\baws\b', r'\bazure\b', r'\bgcp\b', r'\bgoogle cloud\b',
        r'\bdocker\b', r'\bkubernetes\b', r'\bgit\b', r'\blinux\b',
        r'\btensorflow\b', r'\bpytorch\b', r'\bscikit-learn\b', r'\bpandas\b', r'\bnumpy\b',
        r'\bspark\b', r'\bhadoop\b', r'\bkafka\b', r'\belasticsearch\b',
        r'\bmachine learning\b', r'\bdeep learning\b', r'\bdata science\b',
        r'\bapi\b', r'\brest\b', r'\bgraphql\b', r'\bmicroservices\b',
        r'\bci/cd\b', r'\bjenkins\b', r'\bterraform\b', r'\bansible\b'
    ]
    
    issues = []
    
    for pattern in technical_patterns:
        matches = re.findall(pattern, summary_text)
        for match in matches:
            # Check if this skill appears in the skills section
            if not re.search(re.escape(match), skills_text):
                issues.append(f"'{match}' mentioned in summary but not found in skills section")
    
    # Additional check for common programming language patterns
    prog_lang_pattern = r'\b(\w+)\s+programming\b'
    prog_matches = re.findall(prog_lang_pattern, summary_text)
    for lang in prog_matches:
        if not re.search(re.escape(lang.lower()), skills_text):
            issues.append(f"'{lang}' programming mentioned in summary but '{lang}' not found in skills section")
    
    return issues


def tailor_summary_and_skills(state: ResumeState) -> ResumeState:
    """
    Tailor both professional summary and skills sections together to ensure perfect alignment.
    This ensures the summary only mentions skills that are prominently featured in the tailored skills section.
    """
    print("📝🔧 Tailoring professional summary and skills together...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        current_summary = state['working_cv']['cv']['sections'].get('professional_summary', [])
        current_skills = state['working_cv']['cv']['sections'].get('skills', [])
        job_requirements = state['job_requirements']
        
        # Get Australian English instruction if enabled
        au_english_instruction = get_australian_english_instruction() if UTILS_AVAILABLE else ""
        
        prompt = f"""
You are simultaneously tailoring the *Professional Summary* and *Skills* sections of a MASTER résumé
to create a *Targeted Résumé* for ONE specific job. These sections must be perfectly aligned.{au_english_instruction}

### Context
• The master CV covers the candidate's actual background and experience
• The target role is described below – highlight what matters and downplay what doesn't
• The summary should ONLY mention skills that are prominently featured in the tailored skills section

### Inputs
CURRENT_SUMMARY = {current_summary}
CURRENT_SKILLS = {current_skills}
JOB_REQUIREMENTS = {{
  "role_focus": {job_requirements.get('role_focus', [])},
  "industry_domain": "{job_requirements.get('industry_domain', 'General')}",
  "key_technologies": {job_requirements.get('key_technologies', [])},
  "essential_requirements": {job_requirements.get('essential_requirements', [])},
  "certifications_required": {job_requirements.get('certifications_required', [])},
  "technical_expertise": {job_requirements.get('technical_expertise', [])},
  "professional_qualifications": {job_requirements.get('professional_qualifications', [])}
}}

### What to do

#### 1. SKILLS SECTION TAILORING:
- **Reorder skills** to put the most job-relevant ones first
- **Group related skills** together for better readability
- **Emphasize key technologies** mentioned in the job requirements
- **Keep all existing skills** but prioritize the most relevant ones
- **Maintain the original skill categories/structure** if they exist

#### 2. SUMMARY SECTION TAILORING:
- **Analyze the candidate's actual background** from their experience and education
- **Match to job requirements** by highlighting relevant experience and skills
- **Be honest about experience level** - don't inflate or invent experience
- **Structure**: 50-60 words, 2-3 sentences with varied openings
- **CRITICAL**: Only mention skills that appear in your tailored skills section

#### 3. ALIGNMENT RULES (CRITICAL):
- **Perfect sync**: Every technical skill mentioned in the summary MUST appear prominently in the tailored skills section
- **Priority matching**: Skills mentioned in summary should be in the top tier of the tailored skills section
- **No hallucination**: Never mention skills not present in the original skills list
- **Consistency**: Use the same terminology for skills in both sections
- **Validation requirement**: Before finalizing, cross-check every technical term in summary against skills list
- **Zero tolerance**: If a skill is mentioned in summary, it MUST be findable in the skills section

### CRITICAL RULES:
- Base everything on the candidate's ACTUAL experience in the master CV
- Do NOT invent experience they don't have or inflate experience they do have
- Be honest about their background and transitions
- Focus on transferable skills and genuine qualifications
- Match the tone to the job requirements and company culture
- AVOID generic phrases like "Technical professional", "Experienced professional", "Skilled professional"
- Use specific, varied language that reflects the candidate's actual background
- NEVER use vague headers like "Technical Professional." Use the exact role title from the job ad, or substitute "[industry] professional," e.g., "Data Professional."
- If mentioning education, always highlight the most recent and highest degree (e.g., MS over BS)

### ANTI-HALLUCINATION RULES (MANDATORY):
- **ONLY mention programming languages, tools, or technologies that are EXPLICITLY listed in the original skills section**
- **NEVER mention skills like Java, C#, .NET, Angular, React, etc. unless they are actually in the original skills list**
- **If the job requires skills the candidate doesn't have, focus on transferable skills they DO have**
- **Cross-reference every technical skill mentioned in your summary against the tailored skills list**
- **When in doubt about a skill, omit it rather than risk hallucination**
- **Focus on the candidate's genuine strengths rather than trying to match every job requirement**
- **FINAL CHECK**: Before outputting, verify every technical term in summary exists in skills section
- **ABSOLUTE RULE**: Summary can only mention skills that will be prominently featured in your tailored skills output

### Output (MUST be strict JSON):
{{
  "tailored_summary": [
    "A single paragraph (50-60 words) that flows naturally from the candidate's background to their relevant skills and enthusiasm for the role. Use varied, specific language and avoid generic openings. ONLY mention skills that appear prominently in the tailored_skills section."
  ],
  "tailored_skills": [
    "Reordered and grouped skills list that prioritizes job-relevant skills first. Maintain all original skills but reorder for maximum impact. Group related skills together."
  ],
  "summary_changes": "Brief description of what was changed in the summary and why",
  "skills_changes": "Brief description of how skills were reordered/grouped and why",
  "alignment_notes": "Explanation of how the summary and skills sections are aligned"
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": "You are an expert resume writer who prioritizes TRUTHFULNESS and PERFECT ALIGNMENT between summary and skills sections. You must carefully analyze the candidate's actual work history and never claim professional experience in domains where they only have academic/project experience. Be honest about career transitions. CRITICAL: Ensure every technical skill mentioned in the summary appears prominently in the tailored skills section. NEVER mention programming languages, tools, or technologies that are not explicitly listed in the original skills section. Cross-reference every technical skill against their actual skills list. When in doubt, omit the skill rather than risk hallucination."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content or "", "tailor_summary_and_skills")
        
        if result is None:
            fallback_data = {
                'tailored_summary': current_summary,
                'tailored_skills': current_skills,
                'summary_changes': "Summary and skills update failed - using original",
                'skills_changes': "Summary and skills update failed - using original",
                'alignment_notes': "Fallback - no changes made"
            }
            result = create_fallback_response("tailor_summary_and_skills", fallback_data)
        
        new_summary = result.get('tailored_summary', current_summary)
        new_skills = result.get('tailored_skills', current_skills)
        summary_changes = result.get('summary_changes', "No specific changes documented")
        skills_changes = result.get('skills_changes', "No specific changes documented")
        alignment_notes = result.get('alignment_notes', "No alignment notes provided")
        
        # Validate summary-skills alignment
        alignment_issues = validate_summary_skills_alignment(new_summary, new_skills)
        if alignment_issues:
            print(f"   ⚠️ Summary-Skills alignment issues found:")
            for issue in alignment_issues:
                print(f"     - {issue}")
            
            # Add alignment issues to warnings
            state['warnings'].extend([f"Summary-Skills alignment: {issue}" for issue in alignment_issues])
        else:
            print("   ✅ Perfect summary-skills alignment verified")
        
        # Validate summary constraints if utils available
        if UTILS_AVAILABLE and new_summary:
            validation_result = validate_summary_constraints(new_summary)
            actual_word_count = validation_result['words']
            actual_sentence_count = validation_result['sentences']
            
            print(f"   📊 Summary length validation:")
            print(f"     - {actual_word_count} words, {actual_sentence_count} sentences")
            
            if not validation_result['valid']:
                print(f"   ⚠️ Summary constraint violations:")
                for issue in validation_result['issues']:
                    print(f"     - {issue}")
                
                # If constraints are significantly violated, try to fix
                if actual_word_count > 80 or actual_sentence_count > 5:
                    print("   🔄 Attempting to fix summary constraint violations...")
                    if len(new_summary) > 3:
                        new_summary = new_summary[:3]
                    
                    validation_result = validate_summary_constraints(new_summary)
                    actual_word_count = validation_result['words']
                    actual_sentence_count = validation_result['sentences']
                    print(f"   📊 After trimming: {actual_word_count} words, {actual_sentence_count} sentences")
        else:
            # Fallback counting if utils not available
            full_text = ' '.join(new_summary) if isinstance(new_summary, list) else str(new_summary)
            actual_word_count = len(full_text.split())
            actual_sentence_count = len(new_summary) if isinstance(new_summary, list) else 1
        
        # Apply the updated sections
        state['working_cv']['cv']['sections']['professional_summary'] = new_summary
        state['working_cv']['cv']['sections']['skills'] = new_skills
        state['summary_updated'] = True
        state['skills_tailored'] = True
        
        print("✅ Professional summary and skills tailored successfully")
        print(f"   📊 Summary metrics: {actual_word_count} words, {actual_sentence_count} sentences")
        print("   📝 Summary changes:")
        print(f"     - {summary_changes}")
        print("   🔧 Skills changes:")
        print(f"     - {skills_changes}")
        print("   🔗 Alignment:")
        print(f"     - {alignment_notes}")
        
        # Show constraint compliance
        if UTILS_AVAILABLE:
            if 40 <= actual_word_count <= 70 and 2 <= actual_sentence_count <= 4:
                print("   ✅ All summary constraints satisfied")
            else:
                print("   ⚠️ Some summary constraints may not be fully satisfied")
        
        return state
        
    except Exception as e:
        error_msg = f"Error in combined summary and skills tailoring: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        print("   Keeping original summary and skills...")
        state['summary_updated'] = True
        state['skills_tailored'] = True
        return state 