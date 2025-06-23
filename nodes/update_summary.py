from typing import Dict, Any
import os
from openai import OpenAI
from state import ResumeState

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
        - Be concise and impactful

        Current Professional Summary:
        {current_summary}

        Job Requirements:
        - Role Focus: {job_requirements.get('role_focus', [])}
        - Industry: {job_requirements.get('industry_domain', 'General')}
        - Key Technologies: {job_requirements.get('key_technologies', [])}
        - Essential Requirements: {job_requirements.get('essential_requirements', [])}
        - Company Culture: {job_requirements.get('company_culture', '')}
        - Tone: {job_requirements.get('tone_indicators', [])}

        CV Context (for truthfulness):
        - Experience: {[exp.get('position', '') + ' at ' + exp.get('company', '') for exp in state['working_cv']['cv']['sections'].get('experience', [])]}
        - Education: {[edu.get('degree', '') + ' in ' + edu.get('area', '') for edu in state['working_cv']['cv']['sections'].get('education', [])]}
        - Skills: {[skill.get('details', '') for skill in state['working_cv']['cv']['sections'].get('skills', [])]}

        Guidelines:
        1. STRICT LIMIT: 2-4 sentences, 40-70 words total
        2. Lead with the most relevant experience/skills for this role
        3. Use keywords from the job advertisement naturally
        4. Maintain professional tone matching the job posting
        5. Only mention skills/experience that exist elsewhere in the CV
        6. Be concise - every word must add value
        7. Avoid redundant phrases and filler words

        Return a JSON object with:
        - "summary": list of strings (each sentence - must be 2-4 sentences total)
        - "word_count": total word count across all sentences
        - "sentence_count": number of sentences
        - "changes_made": list of specific changes and reasons

        VERIFY: The summary must be 40-70 words and 2-4 sentences.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Create concise, impactful professional summaries within strict word limits (40-70 words, 2-4 sentences)."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        new_summary = result['summary']
        word_count = result.get('word_count', 0)
        sentence_count = result.get('sentence_count', 0)
        changes_made = result['changes_made']
        
        # Validate constraints
        actual_word_count = sum(len(sentence.split()) for sentence in new_summary)
        actual_sentence_count = len(new_summary)
        
        if actual_word_count < 40 or actual_word_count > 70:
            print(f"   ⚠️ Word count ({actual_word_count}) outside target range (40-70)")
        
        if actual_sentence_count < 2 or actual_sentence_count > 4:
            print(f"   ⚠️ Sentence count ({actual_sentence_count}) outside target range (2-4)")
        
        # Update the professional summary
        state['working_cv']['cv']['sections']['professional_summary'] = new_summary
        state['summary_updated'] = True
        
        print("✅ Professional summary updated successfully")
        print(f"   📊 Length: {actual_word_count} words, {actual_sentence_count} sentences")
        print("   Changes made:")
        for change in changes_made:
            print(f"   - {change}")
        
    except Exception as e:
        error_msg = f"Error updating professional summary: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state
