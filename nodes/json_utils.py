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
            # Create a minimal valid response for cross-reference check
            return {
                "corrected_sections": {},
                "changes_made": ["JSON parsing failed - no corrections applied"],
                "issues_found": ["JSON parsing error prevented analysis"]
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