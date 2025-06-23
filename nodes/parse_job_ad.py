from typing import Dict, Any
import os
from openai import OpenAI
from state import ResumeState

def parse_job_ad(state: ResumeState) -> ResumeState:
    """
    Parse job advertisement to extract requirements, skills, and company culture.
    """
    print("🔍 Parsing job advertisement...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = f"""
        Analyze the following job advertisement and extract key information in JSON format:

        Job Advertisement:
        {state['job_advertisement']}

        Please extract the following information:
        1. essential_requirements: List of must-have skills and qualifications
        2. desirable_requirements: List of nice-to-have skills and qualifications
        3. key_technologies: List of specific technologies, tools, and platforms mentioned
        4. soft_skills: List of interpersonal and communication skills required
        5. company_culture: Description of company values and culture
        6. role_focus: Primary focus areas of the role
        7. experience_level: Required years of experience
        8. education_requirements: Required degree and field
        9. industry_domain: Industry or domain focus (e.g., healthcare, finance, tech)
        10. location: Job location
        11. work_arrangement: Remote, hybrid, or on-site
        12. tone_indicators: Formal/informal, technical/business-focused, etc.

        Return the response as a valid JSON object.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert job advertisement analyst. Extract key information and return it as valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse the JSON response
        import json
        job_requirements = json.loads(response.choices[0].message.content)
        
        # Update state
        state['job_requirements'] = job_requirements
        
        print("✅ Job advertisement parsed successfully")
        print(f"   - Found {len(job_requirements.get('essential_requirements', []))} essential requirements")
        print(f"   - Found {len(job_requirements.get('key_technologies', []))} key technologies")
        print(f"   - Industry focus: {job_requirements.get('industry_domain', 'Not specified')}")
        
    except Exception as e:
        error_msg = f"Error parsing job advertisement: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
