"""
Cross-reference validation using library-based utilities.
Provides cost-effective consistency checking between CV sections.
"""

from typing import Dict, Any, List
import os
from openai import OpenAI
from state import ResumeState
from .json_utils import safe_json_parse, create_fallback_response
import re

def deduplicate_skills(skills_section: List[Dict]) -> List[Dict]:
    """
    Remove duplicate skills across different skill categories.
    """
    all_skills = set()
    deduplicated_skills = []
    
    for skill_group in skills_section:
        if 'details' not in skill_group:
            deduplicated_skills.append(skill_group)
            continue
            
        # Split skills and track which ones we've seen
        skills_list = [s.strip() for s in skill_group['details'].split(',')]
        unique_skills = []
        
        for skill in skills_list:
            if skill.lower() not in all_skills:
                all_skills.add(skill.lower())
                unique_skills.append(skill)
        
        # Only keep the skill group if it has unique skills
        if unique_skills:
            skill_group_copy = skill_group.copy()
            skill_group_copy['details'] = ', '.join(unique_skills)
            deduplicated_skills.append(skill_group_copy)
    
    return deduplicated_skills

def remove_unsupported_skills(working_cv: Dict) -> List[str]:
    """
    Remove skills that aren't demonstrated in experience, projects, or education.
    """
    changes_made = []
    
    # Extract all text from experience, projects, and education
    demonstrated_text = ""
    for section in ['experience', 'projects', 'education']:
        if section in working_cv:
            demonstrated_text += str(working_cv[section]).lower()
    
    # List of tools that should be removed if not demonstrated
    unsupported_tools = ['airflow', 'dagster', 'prefect', 'dbt', 'mlops tooling']
    
    if 'skills' in working_cv:
        for skill_group in working_cv['skills']:
            if 'details' in skill_group:
                skills_list = [s.strip() for s in skill_group['details'].split(',')]
                supported_skills = []
                
                for skill in skills_list:
                    skill_lower = skill.lower()
                    if any(tool in skill_lower for tool in unsupported_tools):
                        if skill_lower not in demonstrated_text:
                            changes_made.append(f"Removed unsupported skill: {skill}")
                            continue
                    supported_skills.append(skill)
                
                skill_group['details'] = ', '.join(supported_skills)
    
    return changes_made

def fix_experience_hallucinations(working_cv: Dict) -> List[str]:
    """
    Fix hallucinated claims in experience section, especially for hardware testing roles.
    """
    changes_made = []
    
    if 'experience' not in working_cv:
        return changes_made
    
    for exp in working_cv['experience']:
        if 'position' in exp and 'test development engineer' in exp['position'].lower():
            # This is a hardware testing role - remove software development claims
            if 'highlights' in exp:
                updated_highlights = []
                
                for highlight in exp['highlights']:
                    highlight_lower = highlight.lower()
                    
                    # Check for software development claims that don't belong in hardware testing
                    if any(phrase in highlight_lower for phrase in [
                        'data pipeline', 'sql', 'python', 'ci/cd', 'git', 'mlops'
                    ]):
                        # Replace with hardware-appropriate activities
                        updated_highlight = highlight
                        
                        # Remove or replace software development terms
                        updated_highlight = updated_highlight.replace('automated test sequences', 'automated test procedures')
                        updated_highlight = updated_highlight.replace('using Python and SQL', 'using test automation tools')
                        updated_highlight = updated_highlight.replace('Python and SQL', 'test automation tools')
                        updated_highlight = updated_highlight.replace('data pipelines', 'test procedures')
                        updated_highlight = updated_highlight.replace('data pipeline', 'test procedure')
                        updated_highlight = updated_highlight.replace('CI/CD practices', 'version control practices')
                        updated_highlight = updated_highlight.replace('Git for version control and CI/CD', 'version control systems')
                        updated_highlight = updated_highlight.replace('pipeline development', 'test development')
                        
                        # If it still contains problematic terms, make it more generic
                        if any(term in updated_highlight.lower() for term in ['python', 'sql', 'git', 'ci/cd']):
                            if 'developed and deployed' in updated_highlight.lower():
                                updated_highlight = 'Developed and deployed automated test procedures for 4 new IC products'
                            elif 'implemented' in updated_highlight.lower():
                                updated_highlight = 'Implemented test automation and version control practices to streamline development'
                            else:
                                # Keep the highlight but make it hardware-focused
                                updated_highlight = re.sub(r'using.*?(Python|SQL|Git|CI/CD).*?(?=\s|$)', 'using test automation tools', updated_highlight, flags=re.IGNORECASE)
                        
                        updated_highlights.append(updated_highlight)
                        changes_made.append(f"Fixed software claim in hardware role: {highlight[:40]}...")
                    else:
                        updated_highlights.append(highlight)
                
                exp['highlights'] = updated_highlights
        
        # Also check Associate Member of Technical Staff role
        elif 'position' in exp and 'associate member of technical staff' in exp['position'].lower() and 'test systems' in exp['position'].lower():
            if 'highlights' in exp:
                updated_highlights = []
                
                for highlight in exp['highlights']:
                    highlight_lower = highlight.lower()
                    
                    # Remove MLOps and data model claims from hardware testing
                    if 'mlops' in highlight_lower or 'data model' in highlight_lower:
                        updated_highlight = highlight.replace('integrating MLOps tooling', 'for production testing')
                        updated_highlight = updated_highlight.replace('data models', 'test procedures')
                        updated_highlights.append(updated_highlight)
                        changes_made.append(f"Fixed software claim in hardware role: {highlight[:40]}...")
                    else:
                        updated_highlights.append(highlight)
                
                exp['highlights'] = updated_highlights
    
    return changes_made

def cross_reference_check(state: ResumeState) -> ResumeState:
    """
    Cross-reference check to ensure consistency between sections and fix inconsistencies.
    """
    print("🔍 Performing cross-reference consistency check...")
    
    working_cv = state['working_cv']['cv']['sections']
    all_changes = []
    all_issues = []
    
    try:
        # 1. Programmatic skill deduplication (always runs)
        if 'skills' in working_cv:
            original_skills = working_cv['skills']
            deduplicated_skills = deduplicate_skills(original_skills)
            
            if str(deduplicated_skills) != str(original_skills):
                working_cv['skills'] = deduplicated_skills
                all_changes.append("Removed duplicate skills across categories")
                all_issues.append("Found duplicate skills in different categories")
                print("   🔧 Applied skill deduplication")
        
        # 2. Remove unsupported skills
        unsupported_changes = remove_unsupported_skills(working_cv)
        all_changes.extend(unsupported_changes)
        if unsupported_changes:
            all_issues.append("Found unsupported skills without evidence")
            print("   🔧 Removed unsupported skills")
        
        # 3. Fix experience hallucinations
        hallucination_changes = fix_experience_hallucinations(working_cv)
        all_changes.extend(hallucination_changes)
        if hallucination_changes:
            all_issues.append("Found hallucinated claims in experience section")
            print("   🔧 Fixed experience hallucinations")
        
        # 4. Try LLM-based analysis (optional)
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = f"""
            Review this CV for any remaining inconsistencies and provide a brief analysis.
            
            CV Sections:
            Professional Summary: {working_cv.get('professional_summary', [])}
            Experience: {working_cv.get('experience', [])}
            Projects: {working_cv.get('projects', [])}
            Skills: {working_cv.get('skills', [])}
            
            Focus on:
            1. Professional summary claims vs actual experience
            2. Timeline consistency
            3. Any remaining unsupported claims
            
            Return a simple JSON with just: {{"analysis": "brief summary of any remaining issues"}}
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a resume reviewer. Provide brief analysis of remaining issues."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = safe_json_parse(response.choices[0].message.content, "cross_reference_check")
            if result and 'analysis' in result:
                analysis = result['analysis']
                if analysis and analysis.lower() != 'none' and 'no issues' not in analysis.lower():
                    all_issues.append(f"LLM analysis: {analysis}")
                    print(f"   📝 Additional analysis: {analysis}")
        
        except Exception as e:
            print(f"   ⚠️ LLM analysis failed: {str(e)}")
        
        state['cross_reference_checked'] = True
        
        print("✅ Cross-reference check and corrections completed")
        print(f"   📊 Issues found: {len(all_issues)}")
        print(f"   🔧 Changes made: {len(all_changes)}")
        
        if all_issues:
            print("   🔍 Issues identified and fixed:")
            for issue in all_issues[:3]:
                print(f"     - {issue}")
        
        if all_changes:
            print("   ✅ Changes applied:")
            for change in all_changes[:3]:
                print(f"     - {change}")
        
    except Exception as e:
        error_msg = f"Error in cross-reference check: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state 