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
                    original_highlight = highlight
                    
                    # Check for software development claims that don't belong in hardware testing
                    problematic_phrases = [
                        'leveraging sql', 'utilizing sql', 'using sql',
                        'data querying', 'data transformation', 'data optimisation', 'data optimization',
                        'data pipeline', 'data engineering', 'data analytics',
                        'machine learning initiatives', 'analytics engineering',
                        'python', 'ci/cd', 'git', 'mlops'
                    ]
                    
                    has_problematic_content = any(phrase in highlight_lower for phrase in problematic_phrases)
                    
                    if has_problematic_content:
                        # Remove the problematic phrases and clean up the sentence
                        updated_highlight = highlight
                        
                        # Remove specific problematic phrases
                        updated_highlight = re.sub(r',\s*leveraging\s+sql[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*utilizing\s+sql[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*using\s+sql[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*demonstrating\s+strong\s+proficiency\s+in\s+data\s+engineering[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*bridging\s+the\s+gap\s+between[^,]*machine\s+learning\s+initiatives[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*emphasising\s+on\s+data[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*utilising\s+data\s+analytics[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*utilising\s+data\s+engineering[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*leveraging\s+data\s+analytics[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        
                        # Clean up any remaining artifacts
                        updated_highlight = re.sub(r'\s+', ' ', updated_highlight)  # Multiple spaces
                        updated_highlight = updated_highlight.strip()
                        
                        # If the highlight is significantly different, log the change
                        if updated_highlight != original_highlight:
                            updated_highlights.append(updated_highlight)
                            changes_made.append(f"Fixed software claim in hardware role: {original_highlight[:50]}...")
                        else:
                            updated_highlights.append(highlight)
                    else:
                        updated_highlights.append(highlight)
                
                exp['highlights'] = updated_highlights
        
        # Also check Associate Member of Technical Staff role
        elif 'position' in exp and 'associate member of technical staff' in exp['position'].lower() and 'test systems' in exp['position'].lower():
            if 'highlights' in exp:
                updated_highlights = []
                
                for highlight in exp['highlights']:
                    highlight_lower = highlight.lower()
                    original_highlight = highlight
                    
                    # Remove MLOps and data model claims from hardware testing
                    problematic_phrases = [
                        'emphasising on data-focused', 'utilising data analytics',
                        'data models', 'mlops', 'machine learning'
                    ]
                    
                    has_problematic_content = any(phrase in highlight_lower for phrase in problematic_phrases)
                    
                    if has_problematic_content:
                        updated_highlight = highlight
                        updated_highlight = re.sub(r',\s*emphasising\s+on\s+data-focused[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = re.sub(r',\s*utilising\s+data\s+analytics[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                        updated_highlight = updated_highlight.replace('integrating MLOps tooling', 'for production testing')
                        updated_highlight = updated_highlight.replace('data models', 'test procedures')
                        
                        # Clean up
                        updated_highlight = re.sub(r'\s+', ' ', updated_highlight)
                        updated_highlight = updated_highlight.strip()
                        
                        if updated_highlight != original_highlight:
                            updated_highlights.append(updated_highlight)
                            changes_made.append(f"Fixed software claim in hardware role: {original_highlight[:50]}...")
                        else:
                            updated_highlights.append(highlight)
                    else:
                        updated_highlights.append(highlight)
                
                exp['highlights'] = updated_highlights
        
        # Check for other irrelevant roles that got inappropriate data engineering content
        elif 'position' in exp:
            position_lower = exp['position'].lower()
            irrelevant_positions = ['personal shopper', 'event staff', 'property audit']
            
            if any(pos in position_lower for pos in irrelevant_positions):
                if 'highlights' in exp:
                    updated_highlights = []
                    
                    for highlight in exp['highlights']:
                        highlight_lower = highlight.lower()
                        original_highlight = highlight
                        
                        # Remove inappropriate data engineering content from service roles
                        problematic_phrases = [
                            'leveraging data analytics', 'utilising data analytics',
                            'utilising data engineering', 'data optimisation',
                            'data engineering for', 'demonstrating strong'
                        ]
                        
                        has_problematic_content = any(phrase in highlight_lower for phrase in problematic_phrases)
                        
                        if has_problematic_content:
                            updated_highlight = highlight
                            updated_highlight = re.sub(r',\s*leveraging\s+data\s+analytics[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                            updated_highlight = re.sub(r',\s*utilising\s+data\s+analytics[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                            updated_highlight = re.sub(r',\s*utilising\s+data\s+engineering[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                            updated_highlight = re.sub(r',\s*demonstrating\s+strong[^,]*skills[^,]*', '', updated_highlight, flags=re.IGNORECASE)
                            
                            # Clean up
                            updated_highlight = re.sub(r'\s+', ' ', updated_highlight)
                            updated_highlight = updated_highlight.strip()
                            
                            if updated_highlight != original_highlight:
                                updated_highlights.append(updated_highlight)
                                changes_made.append(f"Removed inappropriate data claims from service role: {original_highlight[:50]}...")
                            else:
                                updated_highlights.append(highlight)
                        else:
                            updated_highlights.append(highlight)
                    
                    exp['highlights'] = updated_highlights
    
    return changes_made

def fix_project_inflated_claims(working_cv: Dict) -> List[str]:
    """
    Fix inflated claims in projects section about professional collaboration and production deployment.
    """
    changes_made = []
    
    if 'projects' not in working_cv:
        return changes_made
    
    for project in working_cv['projects']:
        if 'highlights' in project:
            updated_highlights = []
            
            for highlight in project['highlights']:
                original_highlight = highlight
                updated_highlight = highlight
                
                # Remove inflated collaboration claims for academic/personal projects
                problematic_patterns = [
                    r'collaborated with data scientists to deploy[^.]*in production environments',
                    r'collaborated with data scientists and engineers to[^.]*machine learning pipelines',
                    r'collaborated with stakeholders for[^.]*deployment',
                    r'deployed and tested[^.]*models in production environments',
                    r'collaborated with[^.]*data scientists[^.]*production',
                    r'collaborated with[^.]*engineers[^.]*enhance[^.]*pipelines'
                ]
                
                for pattern in problematic_patterns:
                    if re.search(pattern, updated_highlight.lower()):
                        # Replace with more honest alternatives
                        if 'collaborated with data scientists to deploy' in updated_highlight.lower():
                            updated_highlight = re.sub(
                                r'collaborated with data scientists to deploy and test the models in production environments',
                                'developed and tested machine learning models achieving high accuracy',
                                updated_highlight,
                                flags=re.IGNORECASE
                            )
                        elif 'collaborated with data scientists and engineers to enhance' in updated_highlight.lower():
                            updated_highlight = re.sub(
                                r'collaborated with data scientists and engineers to enhance machine learning pipelines',
                                'developed NLP processing pipeline for task extraction',
                                updated_highlight,
                                flags=re.IGNORECASE
                            )
                        elif 'collaborated with stakeholders for' in updated_highlight.lower():
                            updated_highlight = re.sub(
                                r'collaborated with stakeholders for technical discovery and deployment of the web application',
                                'implemented web application with job recommendation functionality',
                                updated_highlight,
                                flags=re.IGNORECASE
                            )
                        
                        changes_made.append(f"Fixed inflated project claim: {original_highlight[:50]}...")
                        break
                
                updated_highlights.append(updated_highlight)
            
            if any(changes_made):
                                project['highlights'] = updated_highlights
    
    return changes_made

def fix_ai_sounding_language(working_cv: Dict) -> List[str]:
    """
    Fix AI-sounding language patterns like 'demonstrating', 'showcasing', 'highlighting'.
    """
    changes_made = []
    
    # Fix experience section
    if 'experience' in working_cv:
        for exp in working_cv['experience']:
            if 'highlights' in exp:
                updated_highlights = []
                
                for highlight in exp['highlights']:
                    original_highlight = highlight
                    updated_highlight = highlight
                    
                    # Remove AI-sounding patterns
                    ai_patterns = [
                        (r',\s*demonstrating\s+[^,]*skills?[^,]*', ''),
                        (r',\s*showcasing\s+[^,]*skills?[^,]*', ''),
                        (r',\s*highlighting\s+[^,]*skills?[^,]*', ''),
                        (r',\s*demonstrating\s+[^,]*capabilities?[^,]*', ''),
                        (r',\s*showcasing\s+[^,]*capabilities?[^,]*', ''),
                        (r',\s*demonstrating\s+[^,]*proficiency[^,]*', ''),
                        (r',\s*showcasing\s+[^,]*proficiency[^,]*', ''),
                        (r',\s*demonstrating\s+[^,]*competence[^,]*', ''),
                        (r',\s*demonstrating\s+[^,]*expertise[^,]*', ''),
                        (r',\s*contributing\s+to\s+[^,]*efficiency[^,]*', ''),
                        (r',\s*demonstrating\s+[^,]*collaboration[^,]*', ''),
                        (r',\s*showcasing\s+[^,]*management[^,]*', ''),
                    ]
                    
                    for pattern, replacement in ai_patterns:
                        if re.search(pattern, updated_highlight, re.IGNORECASE):
                            updated_highlight = re.sub(pattern, replacement, updated_highlight, flags=re.IGNORECASE)
                            # Clean up any trailing commas or spaces
                            updated_highlight = re.sub(r',\s*$', '', updated_highlight)
                            updated_highlight = re.sub(r'\s+', ' ', updated_highlight).strip()
                    
                    if updated_highlight != original_highlight:
                        changes_made.append(f"Removed AI-sounding language from experience: {original_highlight[:50]}...")
                    
                    updated_highlights.append(updated_highlight)
                
                exp['highlights'] = updated_highlights
    
    # Fix projects section
    if 'projects' in working_cv:
        for project in working_cv['projects']:
            if 'highlights' in project:
                updated_highlights = []
                
                for highlight in project['highlights']:
                    original_highlight = highlight
                    updated_highlight = highlight
                    
                    # Remove AI-sounding patterns from projects
                    ai_patterns = [
                        (r',\s*demonstrating\s+[^,]*skills?[^,]*\.?', '.'),
                        (r',\s*showcasing\s+[^,]*skills?[^,]*\.?', '.'),
                        (r',\s*demonstrating\s+[^,]*proficiency[^,]*\.?', '.'),
                        (r',\s*showcasing\s+[^,]*proficiency[^,]*\.?', '.'),
                        (r'[^.]*,\s*demonstrating\s+[^.]*\.', '.'),
                        (r'[^.]*,\s*showcasing\s+[^.]*\.', '.'),
                    ]
                    
                    for pattern, replacement in ai_patterns:
                        if re.search(pattern, updated_highlight, re.IGNORECASE):
                            updated_highlight = re.sub(pattern, replacement, updated_highlight, flags=re.IGNORECASE)
                            # Clean up multiple periods
                            updated_highlight = re.sub(r'\.+', '.', updated_highlight)
                            updated_highlight = re.sub(r'\s+', ' ', updated_highlight).strip()
                    
                    if updated_highlight != original_highlight:
                        changes_made.append(f"Removed AI-sounding language from project: {original_highlight[:50]}...")
                    
                    updated_highlights.append(updated_highlight)
                
                project['highlights'] = updated_highlights
    
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
        
        # 4. Fix project inflated claims
        project_changes = fix_project_inflated_claims(working_cv)
        all_changes.extend(project_changes)
        if project_changes:
            all_issues.append("Found inflated collaboration claims in projects section")
            print("   🔧 Fixed project inflated claims")
        
        # 5. Fix AI-sounding language patterns
        ai_language_changes = fix_ai_sounding_language(working_cv)
        all_changes.extend(ai_language_changes)
        if ai_language_changes:
            all_issues.append("Found AI-sounding language patterns (demonstrating, showcasing)")
            print("   🔧 Fixed AI-sounding language patterns")
        
        # 6. Try LLM-based analysis (optional)
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