import json
import re
from typing import Dict, Any, Optional

def safe_json_parse(content: str, context: str = "unknown") -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON content with fallback handling for malformed JSON.
    """
    if not content or not content.strip():
        print(f"   ⚠️ Empty content in {context}")
        return None
    
    # Remove common markdown formatting that might interfere
    content = content.strip()
    if content.startswith('```json'):
        content = content[7:]
    if content.startswith('```'):
        content = content[3:]
    if content.endswith('```'):
        content = content[:-3]
    
    content = content.strip()
    
    # First attempt: direct parsing
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"   ⚠️ JSON parsing error in {context}: {str(e)}")
        print(f"   Raw content (first 200 chars): {content[:200]}...")
    
    # Second attempt: try to fix common JSON issues
    try:
        # Fix common issues like unescaped quotes, trailing commas
        fixed_content = content
        
        # Replace single quotes with double quotes (but be careful not to break contractions)
        fixed_content = re.sub(r"(?<![a-zA-Z])'([^']*)'(?![a-zA-Z])", r'"\1"', fixed_content)
        
        # Remove trailing commas before closing brackets/braces
        fixed_content = re.sub(r',(\s*[}\]])', r'\1', fixed_content)
        
        # Fix unescaped quotes in string values
        # This is a more sophisticated approach to handle quotes within strings
        def fix_quotes_in_strings(text):
            # Find all string values and escape internal quotes
            pattern = r'"([^"]*(?:\\.[^"]*)*)"'
            def replace_string(match):
                string_content = match.group(1)
                # Escape any unescaped quotes within the string
                string_content = string_content.replace('"', '\\"')
                return f'"{string_content}"'
            
            return re.sub(pattern, replace_string, text)
        
        fixed_content = fix_quotes_in_strings(fixed_content)
        
        # Try to find and extract just the JSON object
        json_match = re.search(r'(\{.*\})', fixed_content, re.DOTALL)
        if json_match:
            fixed_content = json_match.group(1)
        
        return json.loads(fixed_content)
    except json.JSONDecodeError:
        print(f"   ⚠️ Could not fix JSON in {context}")
    
    # Third attempt: try to extract key-value pairs manually for simple cases
    try:
        if context == "cross_reference_check":
            # Create a minimal valid response for cross_reference_check
            return {
                "corrected_sections": {},
                "changes_made": ["JSON parsing failed - no corrections applied"],
                "issues_found": ["JSON parsing error prevented analysis"]
            }
        elif context == "reorder_sections":
            # Create a minimal valid response for reorder_sections
            return {
                "optimized_sections": ["professional_summary", "skills", "experience", "projects", "education", "certifications", "extracurricular"],
                "reasoning": {
                    "professional_summary": "Standard order - summary first",
                    "skills": "Skills early to show capabilities",
                    "experience": "Experience after skills to demonstrate application",
                    "projects": "Projects to show practical work",
                    "education": "Education towards the end",
                    "certifications": "Certifications after education",
                    "extracurricular": "Extracurricular activities last"
                }
            }
        elif context == "resolve_inconsistencies":
            # Create a minimal valid response for resolve_inconsistencies
            return {
                "corrections": ["JSON parsing failed - no corrections applied"],
                "updated_sections": {},
                "resolution_summary": "JSON parsing error prevented inconsistency resolution"
            }
    except Exception:
        pass
    
    # Fourth attempt: try to parse as plain text and extract structured information
    try:
        if context == "cross_reference_check":
            # Try to extract issues from plain text
            issues = []
            if "issue" in content.lower() or "problem" in content.lower():
                # Extract numbered or bulleted issues
                issue_matches = re.findall(r'[0-9]+\.\s*(.+?)(?=\n|$)', content, re.IGNORECASE)
                issues.extend(issue_matches)
            
            return {
                "corrected_sections": {},
                "changes_made": ["Parsed from plain text - limited analysis"],
                "issues_found": issues if issues else ["Analysis completed from plain text response"]
            }
        elif context == "resolve_inconsistencies":
            # Try to extract corrections from plain text
            corrections = []
            if "correction" in content.lower() or "fix" in content.lower():
                # Extract numbered or bulleted corrections
                correction_matches = re.findall(r'[0-9]+\.\s*(.+?)(?=\n|$)', content, re.IGNORECASE)
                corrections.extend(correction_matches)
            
            return {
                "corrections": corrections if corrections else ["Parsed from plain text - limited corrections"],
                "updated_sections": {},
                "resolution_summary": "Inconsistencies analyzed from plain text response"
            }
    except Exception:
        pass
    
    return None

def create_fallback_response(context: str, default_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a fallback response when JSON parsing fails.
    """
    print(f"   🔄 Using fallback response for {context}")
    return default_data 