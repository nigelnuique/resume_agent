#!/usr/bin/env python3
"""
Resume Agent Workflow Orchestration
Main workflow setup and execution functions for the resume tailoring system
"""

import os
import copy
import subprocess
import yaml
from typing import Dict, Any, cast
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

# Import state management
from state import ResumeState, create_initial_state, save_cv_to_file, load_cv_from_file

# Import all workflow nodes
from nodes.parse_job_ad import parse_job_ad
from nodes.reorder_sections import reorder_sections
from nodes.update_summary import update_summary
from nodes.tailor_experience import tailor_experience
from nodes.tailor_projects import tailor_projects
from nodes.tailor_education import tailor_education
from nodes.tailor_skills import tailor_skills
from nodes.tailor_certifications import tailor_certifications
from nodes.tailor_extracurricular import tailor_extracurricular
from nodes.validate_yaml import validate_yaml

def setup_workflow() -> StateGraph:
    """
    Set up the LangGraph workflow for resume tailoring.
    
    Returns:
        StateGraph: Configured workflow ready for compilation
    """
    print("🔧 Setting up resume tailoring workflow...")
    
    # Create the workflow graph
    workflow = StateGraph(ResumeState)
    
    # Add all processing nodes
    workflow.add_node("parse_job_ad", parse_job_ad)
    workflow.add_node("reorder_sections", reorder_sections)
    workflow.add_node("update_summary", update_summary)
    workflow.add_node("tailor_experience", tailor_experience)
    workflow.add_node("tailor_projects", tailor_projects)
    workflow.add_node("tailor_education", tailor_education)
    workflow.add_node("tailor_skills", tailor_skills)
    workflow.add_node("tailor_certifications", tailor_certifications)
    workflow.add_node("tailor_extracurricular", tailor_extracurricular)
    workflow.add_node("validate_yaml", validate_yaml)
    
    # Define the workflow sequence
    workflow.add_edge(START, "parse_job_ad")
    workflow.add_edge("parse_job_ad", "reorder_sections")
    workflow.add_edge("reorder_sections", "update_summary")
    workflow.add_edge("update_summary", "tailor_experience")
    workflow.add_edge("tailor_experience", "tailor_projects")
    workflow.add_edge("tailor_projects", "tailor_education")
    workflow.add_edge("tailor_education", "tailor_skills")
    workflow.add_edge("tailor_skills", "tailor_certifications")
    workflow.add_edge("tailor_certifications", "tailor_extracurricular")
    workflow.add_edge("tailor_extracurricular", "validate_yaml")
    workflow.add_edge("validate_yaml", END)
    
    print("✅ Workflow setup complete")
    return workflow

def validate_working_cv_sections(state: ResumeState) -> None:
    """
    Validate that the working CV has the required structure and sections.
    
    Args:
        state: Current resume state to validate
    """
    print("🔍 Validating working CV sections...")
    
    try:
        working_cv = state.get('working_cv', {})
        
        if not working_cv:
            print("⚠️ Warning: Working CV is empty")
            return
            
        cv_data = working_cv.get('cv', {})
        if not cv_data:
            print("⚠️ Warning: No 'cv' section found in working CV")
            return
            
        # Check for required top-level fields
        required_fields = ['name']
        missing_fields = [field for field in required_fields if field not in cv_data]
        if missing_fields:
            print(f"⚠️ Warning: Missing required fields: {missing_fields}")
            
        # Check sections structure
        sections = cv_data.get('sections', {})
        if not isinstance(sections, dict):
            print("⚠️ Warning: Sections should be a dictionary")
            return
            
        # Validate common sections
        section_counts = {}
        for section_name, section_data in sections.items():
            if isinstance(section_data, list):
                section_counts[section_name] = len(section_data)
            else:
                section_counts[section_name] = 1
                
        print(f"📊 CV sections found: {section_counts}")
        print("✅ CV validation complete")
        
    except Exception as e:
        print(f"❌ Error validating CV: {str(e)}")
        state.setdefault('errors', []).append(f"CV validation error: {str(e)}")

def save_working_cv(state: ResumeState, filename: str = "working_CV.yaml") -> None:
    """
    Save the working CV to a file.
    
    Args:
        state: Current resume state
        filename: Output filename (default: working_CV.yaml)
    """
    print(f"💾 Saving working CV to {filename}...")
    
    try:
        working_cv = state.get('working_cv', {})
        if not working_cv:
            print("⚠️ Warning: No working CV data to save")
            return
            
        save_cv_to_file(working_cv, filename)
        state['output_file'] = filename
        print(f"✅ Working CV saved successfully to {filename}")
        
    except Exception as e:
        error_msg = f"Error saving working CV: {str(e)}"
        print(f"❌ {error_msg}")
        state.setdefault('errors', []).append(error_msg)

def render_cv(input_file: str = "working_CV.yaml", output_dir: str = "rendercv_output") -> bool:
    """
    Render the CV to PDF using RenderCV.
    
    Args:
        input_file: YAML file to render (default: working_CV.yaml)
        output_dir: Output directory for rendered files (default: rendercv_output)
        
    Returns:
        bool: True if rendering was successful, False otherwise
    """
    print(f"📄 Rendering CV from {input_file}...")
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"❌ Input file {input_file} not found")
            return False
            
        # Run RenderCV command
        cmd = [
            "python", "-m", "rendercv", "render",
            input_file,
            "--output-folder-name", output_dir
        ]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ CV rendered successfully")
            print(f"📁 Output saved to: {output_dir}/")
            return True
        else:
            print(f"❌ RenderCV failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ RenderCV timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Error rendering CV: {str(e)}")
        return False

def load_initial_data(master_cv_file: str = "master_CV.yaml", 
                     job_ad_file: str = "job_advertisement.txt") -> ResumeState:
    """
    Load initial data and create a state for the workflow.
    
    Args:
        master_cv_file: Path to master CV file
        job_ad_file: Path to job advertisement file
        
    Returns:
        ResumeState: Initial state with loaded data
    """
    print("📂 Loading initial data...")
    
    # Create initial state
    state = create_initial_state()
    
    try:
        # Load master CV
        if os.path.exists(master_cv_file):
            master_cv = load_cv_from_file(master_cv_file)
            state['master_cv'] = master_cv
            state['working_cv'] = copy.deepcopy(master_cv)
            print(f"✅ Loaded master CV from {master_cv_file}")
        else:
            print(f"⚠️ Master CV file {master_cv_file} not found")
            
        # Load job advertisement
        if os.path.exists(job_ad_file):
            with open(job_ad_file, 'r', encoding='utf-8') as file:
                job_ad = file.read().strip()
            state['job_advertisement'] = job_ad
            print(f"✅ Loaded job advertisement from {job_ad_file}")
        else:
            print(f"⚠️ Job advertisement file {job_ad_file} not found")
            
    except Exception as e:
        error_msg = f"Error loading initial data: {str(e)}"
        print(f"❌ {error_msg}")
        state.setdefault('errors', []).append(error_msg)
    
    return state

def print_summary(state: ResumeState) -> None:
    """
    Print a summary of the workflow results.
    
    Args:
        state: Final state after workflow completion
    """
    print("\n" + "="*50)
    print("📋 RESUME TAILORING SUMMARY")
    print("="*50)
    
    # Processing status
    processing_steps = [
        ('job_parsed', 'Job requirements parsed'),
        ('sections_reordered', 'Sections reordered'),
        ('summary_updated', 'Professional summary updated'),
        ('experience_tailored', 'Experience section tailored'),
        ('projects_tailored', 'Projects section tailored'),
        ('education_tailored', 'Education section tailored'),
        ('skills_tailored', 'Skills section tailored'),
        ('certifications_tailored', 'Certifications tailored'),
        ('extracurricular_tailored', 'Extracurricular activities tailored'),
        ('yaml_validated', 'YAML structure validated')
    ]
    
    print("\n🔧 Processing Steps:")
    for flag, description in processing_steps:
        status = "✅" if state.get(flag, False) else "❌"
        print(f"  {status} {description}")
    
    # Output information
    output_file = state.get('output_file')
    if output_file:
        print(f"\n📄 Output file: {output_file}")
    
    # Removed sections
    removed_sections = state.get('removed_sections', [])
    if removed_sections:
        print(f"\n🗑️ Removed sections: {', '.join(removed_sections)}")
    
    # Errors and warnings
    errors = state.get('errors', [])
    warnings = state.get('warnings', [])
    
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️ Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors:
        print("\n🎉 Resume tailoring completed successfully!")
    
    print("="*50)

# Main execution function (for command line usage)
def main():
    """Main function for command line execution."""
    load_dotenv()
    
    print("🚀 Resume Agent - AI-Powered Resume Tailoring")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key in the .env file")
        return
    
    # Load initial data
    state = load_initial_data()
    
    if state.get('errors'):
        print("❌ Failed to load initial data. Check file paths and try again.")
        return
    
    # Validate CV sections
    validate_working_cv_sections(state)
    
    # Set up and run workflow
    workflow = setup_workflow()
    app = workflow.compile()
    
    print("\n🔄 Starting workflow execution...")
    final_state = cast(ResumeState, app.invoke(state))
    
    # Save results
    save_working_cv(final_state)
    
    # Render CV
    output_file = final_state.get('output_file')
    if output_file:
        render_cv(output_file)
    
    # Print summary
    print_summary(final_state)

if __name__ == "__main__":
    main() 