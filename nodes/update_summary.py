from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response

# Import library-based utilities for validation
try:
    from utils.grammar_checker import count_words_sentences, validate_summary_constraints
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
        Rewrite the professional summary to align with this job advertisement while staying truthful to the candidate's background.

        CRITICAL CONSTRAINTS:
        - MAXIMUM 2-4 sentences total
        - TOTAL word count: 40-70 words
        - Be concise and impactful - every word must add value
        - Focus on the most relevant skills and experience for this specific role

        Current Summary:
        {current_summary}

        Job Requirements Analysis:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Experience Level: {job_requirements.get('experience_level', 'Not specified')}

        Return ONLY a properly formatted JSON object with:
        - "new_summary": list of strings (each string is a sentence)
        - "changes_made": list of specific changes made
        - "word_count": estimated word count
        - "sentence_count": number of sentences

        Focus on:
        1. Quantifiable achievements relevant to the role
        2. Key technologies mentioned in job requirements
        3. Experience level and domain expertise
        4. Value proposition for this specific role
        
        Example format:
        {{
            "new_summary": ["Sentence 1.", "Sentence 2.", "Sentence 3."],
            "changes_made": ["Focused on data engineering skills", "Added relevant technologies"],
            "word_count": 45,
            "sentence_count": 3
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Create concise, impactful professional summaries that strictly adhere to word and sentence limits."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = safe_json_parse(response.choices[0].message.content, "update_summary")
        
        if result is None:
            fallback_data = {
                'new_summary': current_summary,
                'changes_made': ["Summary update failed - using original"],
                'word_count': 0,
                'sentence_count': 0
            }
            result = create_fallback_response("update_summary", fallback_data)
        
        new_summary = result.get('new_summary', current_summary)
        changes_made = result.get('changes_made', [])
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
        for change in changes_made:
            print(f"     - {change}")
        
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
