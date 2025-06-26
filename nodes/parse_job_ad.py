from typing import Dict, Any
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

def parse_job_ad(state: ResumeState) -> ResumeState:
    """
    Parse job advertisement to extract key requirements and information.
    """
    print("🔍 Parsing job advertisement...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        job_ad = state['job_advertisement']
        
        prompt = f"""
        Analyze this job advertisement and extract key information for resume tailoring:

        Job Advertisement:
        {job_ad}

        Extract and return a JSON object with:
        - "essential_requirements": list of must-have skills/qualifications
        - "preferred_requirements": list of nice-to-have skills/qualifications  
        - "key_technologies": list of specific technologies, tools, frameworks mentioned
        - "soft_skills": list of soft skills and personal qualities mentioned
        - "role_focus": list of main responsibilities and focus areas
        - "industry_domain": the industry or business domain
        - "company_culture": any cultural aspects or values mentioned
        - "experience_level": required years of experience
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing job advertisements. Extract specific, actionable requirements for resume tailoring."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        job_requirements = safe_json_parse(response.choices[0].message.content, "parse_job_ad")
        
        if job_requirements is None:
            # Fallback with empty values to avoid hard-coded defaults
            print("   ⚠️ Using fallback job parsing")
            job_requirements = create_fallback_response("parse_job_ad", {
                'essential_requirements': [],
                'preferred_requirements': [],
                'key_technologies': [],
                'soft_skills': [],
                'role_focus': [],
                'industry_domain': '',
                'company_culture': '',
                'experience_level': ''
            })
        
        state['job_requirements'] = job_requirements
        state['job_parsed'] = True
        
        print("✅ Job advertisement parsed successfully")
        print(f"   - Found {len(job_requirements.get('essential_requirements', []))} essential requirements")
        print(f"   - Found {len(job_requirements.get('key_technologies', []))} key technologies")
        print(f"   - Industry focus: {job_requirements.get('industry_domain', 'Not specified')}")
        
    except Exception as e:
        error_msg = f"Error parsing job advertisement: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Set fallback job requirements to avoid breaking the pipeline
        state['job_requirements'] = {
            'essential_requirements': [],
            'preferred_requirements': [],
            'key_technologies': [],
            'soft_skills': [],
            'role_focus': [],
            'industry_domain': 'General',
            'company_culture': '',
            'experience_level': ''
        }
        state['job_parsed'] = True
    
    return state
