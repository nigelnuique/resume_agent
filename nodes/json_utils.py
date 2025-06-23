import json
import re
from typing import Dict, Any, Optional

def safe_json_parse(content: str, node_name: str = "unknown") -> Optional[Dict[Any, Any]]:
    """
    Safely parse JSON content from OpenAI responses.
    
    Args:
        content: The raw content from OpenAI response
        node_name: Name of the node for error reporting
        
    Returns:
        Parsed JSON dict or None if parsing fails
    """
    if not content or not content.strip():
        print(f"⚠️ Empty response from OpenAI in {node_name}")
        return None
    
    # Clean up the content - sometimes OpenAI adds extra text before/after JSON
    content = content.strip()
    
    # Try to find JSON within the response
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        json_content = json_match.group()
    else:
        json_content = content
    
    try:
        return json.loads(json_content)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing error in {node_name}: {str(e)}")
        print(f"   Raw content (first 200 chars): {content[:200]}...")
        
        # Try to fix common JSON issues
        try:
            # Fix common issues like trailing commas, unescaped quotes, etc.
            fixed_content = fix_common_json_issues(json_content)
            return json.loads(fixed_content)
        except json.JSONDecodeError:
            print(f"⚠️ Could not fix JSON in {node_name}")
            return None

def fix_common_json_issues(content: str) -> str:
    """
    Fix common JSON formatting issues that OpenAI sometimes produces.
    """
    # Remove trailing commas before closing brackets/braces
    content = re.sub(r',\s*}', '}', content)
    content = re.sub(r',\s*]', ']', content)
    
    # Fix unescaped quotes in strings (basic fix)
    # This is a simple approach - more complex cases might need better handling
    
    return content

def create_fallback_response(node_name: str, fallback_data: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Create a fallback response when JSON parsing fails.
    
    Args:
        node_name: Name of the node
        fallback_data: Default data structure to return
        
    Returns:
        Fallback response dictionary
    """
    print(f"📋 Using fallback response for {node_name}")
    return fallback_data 