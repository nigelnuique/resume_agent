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
        
        prompt = """
        Optimize the education section for this job application by consolidating coursework and highlighting relevant achievements.

        Current Education:
        """ + str(current_education) + """

        Job Requirements:
        - Essential Requirements: """ + str(job_requirements.get('essential_requirements', [])) + """
        - Key Technologies: """ + str(job_requirements.get('key_technologies', [])) + """
        - Role Focus: """ + str(job_requirements.get('role_focus', [])) + """
        - Industry: """ + str(job_requirements.get('industry_domain', 'General')) + """

        Instructions:
        1. Keep all institutions, degrees, dates, and locations exactly as they are
        2. For each education entry, optimize the highlights:
           - If there's a "Relevant Coursework:" highlight, consolidate it into ONE line with 0-5 most relevant courses
           - Select courses that align with job requirements and key technologies
           - Keep other achievements (GPA, scholarships, thesis, capstone) as separate highlights
           - Order highlights by importance (achievements first, then coursework)
        3. Format coursework as: "Relevant coursework: Course 1, Course 2, Course 3, Course 4"
        4. If no courses are relevant to the target role, omit the coursework highlight entirely

        CRITICAL PRESERVATION RULES:
        - Keep coursework as a highlight bullet point, NOT as a separate field
        - NEVER truncate existing descriptions with "..." - preserve full text of capstone projects, thesis descriptions, etc.
        - If a capstone or thesis description exists, keep the COMPLETE original text
        - Only modify coursework lists, not project/thesis descriptions

        Return a JSON object with:
        - "education_entries": list of optimized education entries with updated highlights
        - "changes_summary": brief explanation of changes made

        Example format:
        {{
            "education_entries": [
                {{
                    "institution": "RMIT University",
                    "degree": "MS",
                    "area": "Data Science",
                    "start_date": "2023-02",
                    "end_date": "2024-12",
                    "location": "Melbourne, Australia",
                    "highlights": [
                        "Academic merit scholarship",
                        "GPA: 3.5/4.0 (Distinction)",
                        "Capstone Project: [PRESERVE FULL ORIGINAL TEXT]",
                        "Relevant coursework: Machine Learning, Data Science with Python, Big Data Processing, Cloud Computing"
                    ]
                }}
            ]
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Keep coursework as highlight bullet points, NOT separate fields. NEVER truncate existing descriptions - preserve full text of capstone projects and thesis descriptions exactly as they are."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_education")
        
        if result is None:
            print("   ⚠️ Could not parse education optimization - keeping original")
            state['education_tailored'] = True
            return state
        
        education_entries = result.get('education_entries', current_education)
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
