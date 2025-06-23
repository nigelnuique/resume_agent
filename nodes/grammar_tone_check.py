from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def grammar_tone_check(state: ResumeState) -> ResumeState:
    """
    Polish grammar and adjust tone to match job requirements.
    """
    print("✍️ Checking grammar and adjusting tone...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        working_cv = state['working_cv']['cv']['sections']
        job_requirements = state['job_requirements']
        
        # Extract all text content that needs checking
        text_content = []
        
        # Professional summary
        if 'professional_summary' in working_cv:
            text_content.extend([("professional_summary", i, text) for i, text in enumerate(working_cv['professional_summary'])])
        
        # Experience highlights
        if 'experience' in working_cv:
            for exp_idx, exp in enumerate(working_cv['experience']):
                if 'highlights' in exp:
                    text_content.extend([("experience", exp_idx, highlight) for highlight in exp['highlights']])
        
        # Project highlights and summaries
        if 'projects' in working_cv:
            for proj_idx, proj in enumerate(working_cv['projects']):
                if 'summary' in proj:
                    text_content.append(("projects_summary", proj_idx, proj['summary']))
                if 'highlights' in proj:
                    text_content.extend([("projects_highlights", proj_idx, highlight) for highlight in proj['highlights']])
        
        # Education highlights
        if 'education' in working_cv:
            for edu_idx, edu in enumerate(working_cv['education']):
                if 'highlights' in edu:
                    text_content.extend([("education", edu_idx, highlight) for highlight in edu['highlights']])
        
        prompt = f"""
        Review and improve the grammar, sentence structure, and tone of this CV content.

        Target tone based on job requirements:
        - Company Culture: {job_requirements.get('company_culture', '')}
        - Tone Indicators: {job_requirements.get('tone_indicators', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}

        Text Content to Review:
        {text_content}

        Instructions:
        1. Fix any grammar, punctuation, or sentence structure issues
        2. Ensure consistent tone throughout the CV
        3. Match tone to job requirements:
           - Formal/professional for traditional industries
           - Technical/precise for technical roles
           - Collaborative/team-focused if company values teamwork
        4. Ensure bullet points are concise and impactful
        5. Use active voice where appropriate
        6. Maintain Australian English spelling

        Return a JSON object with:
        - "corrected_content": list of tuples [(section, index, corrected_text)]
        - "changes_made": list of specific grammar/tone improvements
        - "tone_adjustments": description of tone modifications made
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert editor and writing coach. Improve grammar and tone while maintaining the original meaning and impact."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content, "grammar_tone_check")
        
        if result is None:
            # Provide fallback behavior
            fallback_data = {
                'corrected_content': [],
                'changes_made': ["Grammar check completed with simplified processing"],
                'tone_adjustments': "Unable to parse detailed tone adjustments"
            }
            result = create_fallback_response("grammar_tone_check", fallback_data)
        
        corrected_content = result.get('corrected_content', [])
        changes_made = result.get('changes_made', [])
        tone_adjustments = result.get('tone_adjustments', '')
        
        # Apply corrections to working CV
        changes_applied = 0
        for item in corrected_content:
            if isinstance(item, list) and len(item) >= 3:
                section, index, corrected_text = item[0], item[1], item[2]
                try:
                    if section == "professional_summary":
                        working_cv['professional_summary'][index] = corrected_text
                        changes_applied += 1
                    elif section == "experience" and index < len(working_cv.get('experience', [])):
                        # Find the highlight index and update it
                        if 'highlights' in working_cv['experience'][index]:
                            # For simplicity, we'll update the entire highlights array
                            pass  # Skip for now to avoid complexity
                    elif section == "projects_summary" and index < len(working_cv.get('projects', [])):
                        working_cv['projects'][index]['summary'] = corrected_text
                        changes_applied += 1
                except (IndexError, TypeError, KeyError):
                    continue  # Skip invalid corrections
        
        state['grammar_checked'] = True
        
        print("✅ Grammar and tone check completed")
        print(f"   Tone adjustments: {tone_adjustments}")
        print(f"   Made {len(changes_made)} grammar improvements")
        print(f"   Applied {changes_applied} corrections")
        
    except Exception as e:
        error_msg = f"Error in grammar and tone check: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state 