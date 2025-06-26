from typing import Dict, Any
import os
from openai import OpenAI
from state import ResumeState

def convert_au_english(state: ResumeState) -> ResumeState:
    """
    Convert American English to Australian English spelling throughout the CV.
    """
    print("🇦🇺 Converting to Australian English...")
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        def convert_text(text: str) -> str:
            if not isinstance(text, str) or not text.strip():
                return text

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Convert the following text to Australian English spelling without changing the meaning."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0
            )

            return response.choices[0].message.content.strip() if response.choices[0].message.content else ""

        def convert_section(data):
            if isinstance(data, str):
                return convert_text(data)
            if isinstance(data, list):
                return [convert_section(item) for item in data]
            if isinstance(data, dict):
                return {k: convert_section(v) for k, v in data.items()}
            return data

        sections = state['working_cv']['cv']['sections']
        
        # Ensure sections is a dictionary
        if not isinstance(sections, dict):
            print("   ⚠️ Sections is not a dictionary, skipping Australian English conversion")
            state['au_english_converted'] = True
            return state

        for name, content in sections.items():
            sections[name] = convert_section(content)

        state['au_english_converted'] = True

        print("✅ Australian English conversion completed")

    except Exception as e:
        error_msg = f"Error converting to Australian English: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)

    return state
