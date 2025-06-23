from typing import Dict, Any, List
import re
from state import ResumeState

def convert_au_english(state: ResumeState) -> ResumeState:
    """
    Convert American English to Australian English spelling throughout the CV.
    """
    print("🇦🇺 Converting to Australian English...")
    
    try:
        # Define American to Australian English conversions
        us_to_au_conversions = {
            # -ize to -ise
            r'\b(\w+)ize\b': r'\1ise',
            r'\b(\w+)izing\b': r'\1ising',
            r'\b(\w+)ized\b': r'\1ised',
            r'\b(\w+)ization\b': r'\1isation',
            
            # -or to -our
            r'\bbehavior\b': 'behaviour',
            r'\bcolor\b': 'colour',
            r'\bfavor\b': 'favour',
            r'\bhonor\b': 'honour',
            r'\blabor\b': 'labour',
            r'\bneighbor\b': 'neighbour',
            
            # -er to -re
            r'\bcenter\b': 'centre',
            r'\btheater\b': 'theatre',
            r'\bmeter\b': 'metre',
            r'\bliter\b': 'litre',
            
            # -yze to -yse
            r'\banalyze\b': 'analyse',
            r'\banalyzed\b': 'analysed',
            r'\banalyzing\b': 'analysing',
            r'\banalysis\b': 'analysis',  # No change needed
            
            # -ense to -ence
            r'\bdefense\b': 'defence',
            r'\blicense\b': 'licence',  # As noun
            
            # Other common words
            r'\borganization\b': 'organisation',
            r'\borganizational\b': 'organisational',
            r'\brecognize\b': 'recognise',
            r'\brecognized\b': 'recognised',
            r'\bspecialize\b': 'specialise',
            r'\bspecialized\b': 'specialised',
            r'\boptimize\b': 'optimise',
            r'\boptimized\b': 'optimised',
            r'\boptimization\b': 'optimisation',
            r'\bharmonize\b': 'harmonise',
            r'\bharmonized\b': 'harmonised',
            r'\bharmonization\b': 'harmonisation',
            r'\bstandardize\b': 'standardise',
            r'\bstandardized\b': 'standardised',
            r'\bvisualize\b': 'visualise',
            r'\bvisualized\b': 'visualised',
            r'\bvisualization\b': 'visualisation',
        }
        
        def convert_text(text: str) -> str:
            """Convert a single text string to Australian English"""
            if not isinstance(text, str):
                return text
                
            converted_text = text
            for us_pattern, au_replacement in us_to_au_conversions.items():
                converted_text = re.sub(us_pattern, au_replacement, converted_text, flags=re.IGNORECASE)
            
            return converted_text
        
        def convert_section_recursively(data):
            """Recursively convert text in nested structures"""
            if isinstance(data, str):
                return convert_text(data)
            elif isinstance(data, list):
                return [convert_section_recursively(item) for item in data]
            elif isinstance(data, dict):
                return {key: convert_section_recursively(value) for key, value in data.items()}
            else:
                return data
        
        # Convert all sections
        sections = state['working_cv']['cv']['sections']
        conversions_made = []
        
        for section_name, section_data in sections.items():
            original_data = str(section_data)
            converted_data = convert_section_recursively(section_data)
            sections[section_name] = converted_data
            
            # Track changes made
            if str(converted_data) != original_data:
                conversions_made.append(f"Updated {section_name} section")
        
        state['au_english_converted'] = True
        
        print("✅ Australian English conversion completed")
        if conversions_made:
            print(f"   Converted {len(conversions_made)} sections")
            for conversion in conversions_made:
                print(f"   - {conversion}")
        else:
            print("   No conversions needed - text already in Australian English")
        
    except Exception as e:
        error_msg = f"Error converting to Australian English: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state 