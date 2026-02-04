"""AI-based section ordering using OpenAI."""

import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse

# Import utility for Australian English instruction
try:
    from utils import get_australian_english_instruction
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

def reorder_sections(state: ResumeState) -> ResumeState:
    """Reorder CV sections with help from GPT-4."""
    print("📋 Reordering CV sections using AI...")

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        current_sections = state['working_cv']['cv'].get('sections', {})
        job_requirements = state.get('job_requirements', {})

        # Get Australian English instruction if enabled
        au_english_instruction = get_australian_english_instruction() if UTILS_AVAILABLE else ""

        prompt = f"""
You are reordering and filtering resume sections to match job requirements.

TASK: Analyze the resume sections and job requirements, then return a JSON response with:
1. optimized_sections: List of section names in optimal order (keep relevant sections)
2. removed_sections: List of section names to remove (irrelevant sections)
3. reasoning: Object explaining why each section was kept/removed/reordered

RULES:
- Remove sections not relevant to the role
- For extracurricular section check first if any of them are relevant. If not, remove the section.
- Keep sections that demonstrate relevant skills and experience
- Order sections by importance to the job requirements
- Be specific about why each section is kept, removed, or reordered

{au_english_instruction}

RESUME SECTIONS: {list(current_sections.keys())}
JOB REQUIREMENTS: {job_requirements}

RESPONSE FORMAT (return ONLY valid JSON):
{{
  "optimized_sections": ["section1", "section2", "section3"],
  "removed_sections": ["irrelevant_section"],
  "reasoning": {{
    "section1": "Explanation of why this section is kept/positioned",
    "section2": "Explanation of why this section is kept/positioned",
    "irrelevant_section": "Explanation of why this section was removed"
  }}
}}

IMPORTANT: Return ONLY the JSON object. No text before or after.
"""
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are an expert resume editor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        result = safe_json_parse(response.choices[0].message.content or "", "reorder_sections")
        if result:
            optimized_order = result.get('optimized_sections', list(current_sections.keys()))
            removed_sections = result.get('removed_sections', [])
            
            # Create new sections dictionary with reordered content
            reordered_sections = {}
            for section_name in optimized_order:
                if section_name in current_sections:
                    reordered_sections[section_name] = current_sections[section_name]
            
            # Add any sections that weren't in the optimized order
            for section_name, section_content in current_sections.items():
                if section_name not in reordered_sections and section_name not in removed_sections:
                    reordered_sections[section_name] = section_content
            
            state['working_cv']['cv']['sections'] = reordered_sections
            state['removed_sections'] = removed_sections
            reasoning = result.get('reasoning', {})
            if reasoning:
                print("   📝 Reasoning:")
                for sec, reason in reasoning.items():
                    print(f"     - {sec}: {reason}")
            
            if removed_sections:
                print(f"   🗑️ Removed sections: {', '.join(removed_sections)}")
            print(f"   📊 Final section order: {list(reordered_sections.keys())}")
        else:
            # Fallback: keep all sections in original order
            print("   ⚠️ Using fallback: keeping all sections in original order")
            state['removed_sections'] = []
        
        state['sections_reordered'] = True
        print("✅ Section reordering completed")
        return state

    except Exception as e:
        print(f"❌ Section reordering failed: {e}")
        state['errors'].append(str(e))
        state['sections_reordered'] = True
        return state
