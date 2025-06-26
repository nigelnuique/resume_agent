from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict
import yaml

class ResumeState(TypedDict):
    """State structure for the resume tailoring workflow"""
    
    # Input data
    master_cv: Dict[str, Any]  # Original CV data
    job_advertisement: str     # Job ad text
    
    # Working data
    working_cv: Dict[str, Any]  # CV being modified
    
    # Analysis results
    job_requirements: Dict[str, Any]  # Parsed job requirements
    tailoring_plan: Dict[str, Any]    # Plan for tailoring
    
    # Processing flags
    job_parsed: bool
    sections_reordered: bool
    summary_updated: bool
    experience_tailored: bool
    projects_tailored: bool
    education_tailored: bool
    skills_tailored: bool
    certifications_tailored: bool
    extracurricular_tailored: bool
    grammar_checked: bool
    au_english_converted: bool
    yaml_validated: bool
    
    # Interactive workflow tracking
    workflow_terminated_by_user: bool
    termination_node: Optional[str]
    
    # Error tracking
    errors: List[str]
    warnings: List[str]
    
    # Final output
    output_file: Optional[str]

def create_initial_state() -> ResumeState:
    """Create initial state with default values"""
    return ResumeState(
        master_cv={},
        job_advertisement="",
        working_cv={},
        job_requirements={},
        tailoring_plan={},
        job_parsed=False,
        sections_reordered=False,
        summary_updated=False,
        experience_tailored=False,
        projects_tailored=False,
        education_tailored=False,
        skills_tailored=False,
        certifications_tailored=False,
        extracurricular_tailored=False,
        grammar_checked=False,
        au_english_converted=False,
        yaml_validated=False,
        workflow_terminated_by_user=False,
        termination_node=None,
        errors=[],
        warnings=[],
        output_file=None
    )

def load_cv_from_file(filepath: str) -> Dict[str, Any]:
    """Load CV data from YAML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise Exception(f"Error loading CV from {filepath}: {str(e)}")

def save_cv_to_file(cv_data: Dict[str, Any], filepath: str) -> None:
    """Save CV data to YAML file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(cv_data, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except Exception as e:
        raise Exception(f"Error saving CV to {filepath}: {str(e)}")

def load_job_ad_from_file(filepath: str) -> str:
    """Load job advertisement from text file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        raise Exception(f"Error loading job advertisement from {filepath}: {str(e)}") 