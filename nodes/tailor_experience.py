from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

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
        
        # Check if this is a technical/senior role that should filter out irrelevant positions
        is_technical_role = any(tech in str(job_requirements).lower() for tech in [
            'engineering', 'developer', 'data', 'analytics', 'ml', 'machine learning', 
            'python', 'sql', 'technical', 'software', 'senior'
        ])
        
        filter_instruction = ""
        if is_technical_role:
            filter_instruction = """
        FILTERING INSTRUCTION:
        For technical/senior roles, EXCLUDE the following types of irrelevant positions from the final experience list:
        - Retail/service positions (Personal Shopper, Event Staff, etc.)
        - Basic administrative roles (Property Audit Assistant, etc.) 
        - Entry-level service jobs that don't demonstrate technical skills
        Keep only positions that demonstrate technical competence, leadership, or directly relevant experience.
        Aim for 3-5 most relevant positions maximum.
        """
        
        prompt = f"""
        Tailor the experience section for this job application by reordering experiences and optimizing content.

        Current Experience:
        {current_experience}

        Job Requirements:
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Experience Level: {job_requirements.get('experience_level', 'Not specified')}

        {filter_instruction}

        CRITICAL INSTRUCTIONS:
        1. Reorder experiences to put most relevant ones first
        2. For each experience, optimize highlights to emphasize relevant skills and achievements
        3. Use keywords from job requirements naturally BUT ONLY if they are genuinely relevant to the role
        4. Quantify achievements where possible
        5. Focus on impact and results
        6. Keep all factual information accurate (companies, positions, dates, locations)
        
        CRITICAL WRITING STYLE GUIDELINES:
        - Avoid AI-sounding language patterns like "demonstrating...", "showcasing...", "highlighting..."
        - Let achievements speak for themselves - don't explicitly state what they demonstrate
        - Use direct, concise language focused on actions and results
        - Example: Instead of "Led 10 projects, demonstrating leadership skills" → "Led 10 projects, releasing 40 setups"
        - Example: Instead of "Developed solutions, showcasing technical expertise" → "Developed test solutions for 4 new IC products"
        
        IMPORTANT CONSTRAINTS:
        - DO NOT ADD data engineering, SQL, Python, or machine learning content to hardware testing roles (Test Development Engineer, Test Systems Development)
        - DO NOT ADD technical data skills to service roles (Personal Shopper, Event Staff, Property Audit)
        - Only mention technologies and skills that were genuinely used in each specific role
        - Hardware testing roles should focus on IC testing, test development, hardware, qualifications, and production support
        - Service roles should focus on customer service, coordination, problem-solving, and operational efficiency
        
        Return a JSON object with:
        - "experiences": list of reordered and optimized experience entries (filtered if appropriate)
        - "changes_summary": brief explanation of changes made, including any positions removed
        - "positions_removed": number of positions removed (if any)
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Optimize experience sections while maintaining factual accuracy. For technical roles, prioritize relevant experience and filter out irrelevant service positions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content, "tailor_experience")
        
        if result is None:
            print("   ⚠️ Could not parse experience optimization - keeping original")
            state['experience_tailored'] = True
            return state
        
        experiences = result.get('experiences', current_experience)
        changes_summary = result.get('changes_summary', 'No changes summary available')
        positions_removed = result.get('positions_removed', 0)
        
        # Update the experience section
        state['working_cv']['cv']['sections']['experience'] = experiences
        state['experience_tailored'] = True
        
        print("✅ Experience section tailored successfully")
        if positions_removed > 0:
            print(f"   🗑️ Removed {positions_removed} irrelevant position(s)")
        print(f"   📊 Final experience count: {len(experiences)}")
        print(f"   Summary: {changes_summary}")
        
    except Exception as e:
        error_msg = f"Error tailoring experience section: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        # Don't fail the entire process if experience tailoring fails
        state['experience_tailored'] = True
    
    return state
