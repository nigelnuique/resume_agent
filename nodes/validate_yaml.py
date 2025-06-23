from typing import Dict, Any, List
import yaml
import copy
from state import ResumeState

def validate_yaml(state: ResumeState) -> ResumeState:
    """
    Validate YAML structure for RenderCV compatibility.
    """
    print("📋 Validating YAML structure...")
    
    try:
        working_cv = state['working_cv']
        validation_errors = []
        validation_warnings = []
        
        # Check top-level structure
        if 'cv' not in working_cv:
            validation_errors.append("Missing 'cv' top-level key")
            return state
        
        cv_data = working_cv['cv']
        
        # Check required top-level CV fields
        required_cv_fields = ['name', 'sections']
        for field in required_cv_fields:
            if field not in cv_data:
                validation_errors.append(f"Missing required CV field: {field}")
        
        # Check sections structure
        if 'sections' in cv_data:
            sections = cv_data['sections']
            
            # Validate each section type
            section_validators = {
                'professional_summary': validate_professional_summary,
                'experience': validate_experience,
                'projects': validate_projects,
                'education': validate_education,
                'skills': validate_skills
            }
            
            for section_name, section_data in sections.items():
                if section_name in section_validators:
                    section_errors, section_warnings = section_validators[section_name](section_data)
                    validation_errors.extend([f"{section_name}: {error}" for error in section_errors])
                    validation_warnings.extend([f"{section_name}: {warning}" for warning in section_warnings])
        
        # Test YAML serialization
        try:
            yaml_string = yaml.dump(working_cv, default_flow_style=False, sort_keys=False, allow_unicode=True)
            # Try to reload it
            yaml.safe_load(yaml_string)
        except Exception as e:
            validation_errors.append(f"YAML serialization error: {str(e)}")
        
        # Check for common RenderCV issues
        rendercv_checks = [
            check_date_formats,
            check_highlight_strings,
            check_required_entry_fields
        ]
        
        for check_func in rendercv_checks:
            errors, warnings = check_func(working_cv)
            validation_errors.extend(errors)
            validation_warnings.extend(warnings)
        
        # Update state
        state['errors'].extend(validation_errors)
        state['warnings'].extend(validation_warnings)
        state['yaml_validated'] = True
        
        print("✅ YAML validation completed")
        if validation_errors:
            print(f"   ❌ Found {len(validation_errors)} errors")
            for error in validation_errors[:3]:  # Show first 3
                print(f"      - {error}")
        if validation_warnings:
            print(f"   ⚠️ Found {len(validation_warnings)} warnings")
            for warning in validation_warnings[:3]:  # Show first 3
                print(f"      - {warning}")
        if not validation_errors and not validation_warnings:
            print("   ✅ No validation issues found")
        
    except Exception as e:
        error_msg = f"Error validating YAML: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state

def validate_professional_summary(summary_data) -> tuple:
    """Validate professional summary section"""
    errors = []
    warnings = []
    
    if not isinstance(summary_data, list):
        errors.append("Professional summary must be a list of strings")
    else:
        for i, item in enumerate(summary_data):
            if not isinstance(item, str):
                errors.append(f"Summary item {i} must be a string")
    
    return errors, warnings

def validate_experience(experience_data) -> tuple:
    """Validate experience section"""
    errors = []
    warnings = []
    
    if not isinstance(experience_data, list):
        errors.append("Experience must be a list of entries")
        return errors, warnings
    
    required_fields = ['company', 'position', 'start_date']
    for i, exp in enumerate(experience_data):
        if not isinstance(exp, dict):
            errors.append(f"Experience entry {i} must be a dictionary")
            continue
            
        for field in required_fields:
            if field not in exp:
                errors.append(f"Experience entry {i} missing required field: {field}")
        
        if 'highlights' in exp and not isinstance(exp['highlights'], list):
            errors.append(f"Experience entry {i} highlights must be a list")
    
    return errors, warnings

def validate_projects(projects_data) -> tuple:
    """Validate projects section"""
    errors = []
    warnings = []
    
    if not isinstance(projects_data, list):
        errors.append("Projects must be a list of entries")
        return errors, warnings
    
    for i, proj in enumerate(projects_data):
        if not isinstance(proj, dict):
            errors.append(f"Project entry {i} must be a dictionary")
            continue
            
        if 'name' not in proj:
            errors.append(f"Project entry {i} missing required field: name")
        
        if 'highlights' in proj and not isinstance(proj['highlights'], list):
            errors.append(f"Project entry {i} highlights must be a list")
    
    return errors, warnings

def validate_education(education_data) -> tuple:
    """Validate education section"""
    errors = []
    warnings = []
    
    if not isinstance(education_data, list):
        errors.append("Education must be a list of entries")
        return errors, warnings
    
    required_fields = ['institution', 'degree', 'area']
    for i, edu in enumerate(education_data):
        if not isinstance(edu, dict):
            errors.append(f"Education entry {i} must be a dictionary")
            continue
            
        for field in required_fields:
            if field not in edu:
                errors.append(f"Education entry {i} missing required field: {field}")
        
        if 'highlights' in edu and not isinstance(edu['highlights'], list):
            errors.append(f"Education entry {i} highlights must be a list")
    
    return errors, warnings

def validate_skills(skills_data) -> tuple:
    """Validate skills section"""
    errors = []
    warnings = []
    
    if not isinstance(skills_data, list):
        errors.append("Skills must be a list of entries")
        return errors, warnings
    
    for i, skill in enumerate(skills_data):
        if not isinstance(skill, dict):
            errors.append(f"Skill entry {i} must be a dictionary")
            continue
            
        if 'label' not in skill:
            errors.append(f"Skill entry {i} missing required field: label")
        if 'details' not in skill:
            errors.append(f"Skill entry {i} missing required field: details")
    
    return errors, warnings

def check_date_formats(cv_data) -> tuple:
    """Check date formats are valid"""
    errors = []
    warnings = []
    
    # This is a simplified check - RenderCV is flexible with date formats
    date_fields = ['start_date', 'end_date']
    
    def check_dates_in_section(section_data, section_name):
        if isinstance(section_data, list):
            for i, entry in enumerate(section_data):
                if isinstance(entry, dict):
                    for date_field in date_fields:
                        if date_field in entry:
                            date_value = entry[date_field]
                            if not isinstance(date_value, (str, int)) and date_value != 'present':
                                warnings.append(f"{section_name} entry {i}: {date_field} should be string, int, or 'present'")
    
    sections = cv_data.get('cv', {}).get('sections', {})
    for section_name, section_data in sections.items():
        if section_name in ['experience', 'education', 'projects']:
            check_dates_in_section(section_data, section_name)
    
    return errors, warnings

def check_highlight_strings(cv_data) -> tuple:
    """Check that all highlights are strings"""
    errors = []
    warnings = []
    
    sections = cv_data.get('cv', {}).get('sections', {})
    for section_name, section_data in sections.items():
        if isinstance(section_data, list):
            for i, entry in enumerate(section_data):
                if isinstance(entry, dict) and 'highlights' in entry:
                    highlights = entry['highlights']
                    if isinstance(highlights, list):
                        for j, highlight in enumerate(highlights):
                            if not isinstance(highlight, str):
                                errors.append(f"{section_name} entry {i} highlight {j} must be a string")
    
    return errors, warnings

def check_required_entry_fields(cv_data) -> tuple:
    """Check that entries have required fields for their type"""
    errors = []
    warnings = []
    
    # Field requirements by section type
    field_requirements = {
        'experience': ['company', 'position'],
        'education': ['institution', 'degree', 'area'],
        'projects': ['name']
    }
    
    sections = cv_data.get('cv', {}).get('sections', {})
    for section_name, required_fields in field_requirements.items():
        if section_name in sections:
            section_data = sections[section_name]
            if isinstance(section_data, list):
                for i, entry in enumerate(section_data):
                    if isinstance(entry, dict):
                        for field in required_fields:
                            if field not in entry or not entry[field]:
                                errors.append(f"{section_name} entry {i} missing required field: {field}")
    
    return errors, warnings 