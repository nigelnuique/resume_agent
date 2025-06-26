#!/usr/bin/env python3
"""
Resume Agent - Interactive Resume Tailoring System
Uses LangGraph to orchestrate AI-powered resume tailoring with user interaction after each node.
"""

import os
import copy
import subprocess
from typing import Dict, Any
from dotenv import load_dotenv

# Import state and all nodes
from state import ResumeState, create_initial_state, load_cv_from_file, save_cv_to_file, load_job_ad_from_file
from nodes.parse_job_ad import parse_job_ad
from nodes.reorder_sections import reorder_sections
from nodes.update_summary import update_summary
from nodes.tailor_experience import tailor_experience
from nodes.tailor_projects import tailor_projects
from nodes.tailor_education import tailor_education
from nodes.tailor_skills import tailor_skills
from nodes.tailor_certifications import tailor_certifications
from nodes.tailor_extracurricular import tailor_extracurricular
from nodes.convert_au_english import convert_au_english
from nodes.validate_yaml import validate_yaml
from utils.interactive_rendering import save_and_render_cv, get_next_node_name

def create_interactive_node(original_node_func, node_name: str):
    """
    Create a wrapper function that renders the CV and asks for user input after the original node.
    
    Args:
        original_node_func: The original node function
        node_name: Name of the node
        
    Returns:
        Wrapper function that includes rendering and user interaction
    """
    def interactive_node(state: ResumeState) -> ResumeState:
        """Interactive wrapper for node execution with rendering and user input."""
        print(f"\n{'='*60}")
        print(f"🚀 Starting node: {node_name}")
        print(f"{'='*60}")
        
        # Execute the original node
        state = original_node_func(state)
        
        # Check if there were errors in the node
        if state.get('errors'):
            print(f"⚠️ Node {node_name} completed with errors")
            # Still render and ask user if they want to proceed
            proceed = save_and_render_cv(state, node_name)
        else:
            print(f"✅ Node {node_name} completed successfully")
            # Render and ask user if they want to proceed
            proceed = save_and_render_cv(state, node_name)
        
        # Store the user's decision in the state
        state[f'{node_name}_user_proceed'] = proceed
        
        if not proceed:
            # User chose to stop
            next_node = get_next_node_name(node_name)
            print(f"\n⏹️ User chose to stop after {node_name}")
            print(f"📋 Next node would have been: {next_node}")
            print(f"📄 Final CV is available in rendercv_output/")
            # Set a flag to indicate early termination
            state['workflow_terminated_by_user'] = True
            state['termination_node'] = node_name
        
        return state
    
    return interactive_node

def setup_interactive_workflow():
    """Set up the interactive workflow with rendering and user interaction."""
    print("🔧 Setting up interactive workflow...")
    
    # Create interactive versions of all nodes
    interactive_nodes = {
        "parse_job_ad": create_interactive_node(parse_job_ad, "parse_job_ad"),
        "update_summary": create_interactive_node(update_summary, "update_summary"),
        "tailor_experience": create_interactive_node(tailor_experience, "tailor_experience"),
        "tailor_projects": create_interactive_node(tailor_projects, "tailor_projects"),
        "tailor_education": create_interactive_node(tailor_education, "tailor_education"),
        "tailor_skills": create_interactive_node(tailor_skills, "tailor_skills"),
        "tailor_certifications": create_interactive_node(tailor_certifications, "tailor_certifications"),
        "tailor_extracurricular": create_interactive_node(tailor_extracurricular, "tailor_extracurricular"),
        "reorder_sections": create_interactive_node(reorder_sections, "reorder_sections"),
        "convert_au_english": create_interactive_node(convert_au_english, "convert_au_english"),
        "validate_yaml": create_interactive_node(validate_yaml, "validate_yaml")
    }
    
    return interactive_nodes

def load_initial_data() -> ResumeState:
    """Load master CV and job advertisement into initial state."""
    print("📁 Loading initial data...")
    
    # Ensure we start with a clean slate - remove any existing working CV
    cleanup_previous_working_files()
    
    state = create_initial_state()
    
    try:
        # Load master CV
        master_cv = load_cv_from_file("master_CV.yaml")
        state['master_cv'] = master_cv
        state['working_cv'] = copy.deepcopy(master_cv)  # Create working copy
        print(f"   ✅ Loaded master CV: {master_cv['cv']['name']}")
        
        # Validate that all sections were copied correctly
        validate_working_cv_sections(state)
        
        # Load job advertisement
        job_ad = load_job_ad_from_file("job_advertisement.txt")
        state['job_advertisement'] = job_ad
        print(f"   ✅ Loaded job advertisement ({len(job_ad)} characters)")
        
    except Exception as e:
        error_msg = f"Error loading initial data: {str(e)}"
        print(f"   ❌ {error_msg}")
        state['errors'].append(error_msg)
    
    return state

def cleanup_previous_working_files() -> None:
    """Remove any existing working files to ensure fresh start."""
    working_files = ["working_CV.yaml"]
    
    for file in working_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"   🧹 Removed existing {file}")
            except Exception as e:
                print(f"   ⚠️ Could not remove {file}: {e}")

def validate_working_cv_sections(state: ResumeState) -> None:
    """Validate that all sections from master CV are present in working CV."""
    try:
        master_sections = state['master_cv']['cv']['sections']
        working_sections = state['working_cv']['cv']['sections']
        
        # List of sections that should be preserved
        critical_sections = ['education', 'certifications', 'extracurricular', 'experience', 'projects', 'skills']
        
        missing_sections = []
        empty_sections = []
        
        for section in critical_sections:
            if section in master_sections:
                master_content = master_sections[section]
                working_content = working_sections.get(section)
                
                if working_content is None:
                    missing_sections.append(section)
                    # Copy the section from master
                    working_sections[section] = copy.deepcopy(master_content)
                elif not working_content and master_content:
                    empty_sections.append(section)
                    # Copy the section from master
                    working_sections[section] = copy.deepcopy(master_content)
        
        if missing_sections or empty_sections:
            print(f"   🔧 Fixed missing/empty sections: {missing_sections + empty_sections}")
            
        # Log section counts for verification
        section_counts = {}
        for section in critical_sections:
            if section in working_sections and working_sections[section]:
                if isinstance(working_sections[section], list):
                    section_counts[section] = len(working_sections[section])
                else:
                    section_counts[section] = "present"
        
        print(f"   📊 Working CV sections: {section_counts}")
        
    except Exception as e:
        error_msg = f"Error validating working CV sections: {str(e)}"
        print(f"   ⚠️ {error_msg}")
        state['warnings'].append(error_msg)

def print_interactive_summary(state: ResumeState) -> None:
    """Print a summary of the interactive tailoring process."""
    print("\n" + "="*60)
    print("📊 INTERACTIVE RESUME TAILORING SUMMARY")
    print("="*60)
    
    # Process status
    process_steps = [
        ("Job advertisement parsed", state.get('job_parsed', False)),
        ("Summary updated", state.get('summary_updated', False)),
        ("Experience tailored", state.get('experience_tailored', False)),
        ("Projects tailored", state.get('projects_tailored', False)),
        ("Education tailored", state.get('education_tailored', False)),
        ("Skills tailored", state.get('skills_tailored', False)),
        ("Certifications tailored", state.get('certifications_tailored', False)),
        ("Extracurricular tailored", state.get('extracurricular_tailored', False)),
        ("Sections reordered", state.get('sections_reordered', False)),
        ("Australian English converted", state.get('au_english_converted', False)),
        ("YAML validated", state.get('yaml_validated', False))
    ]
    
    print("\n📋 Process Status:")
    for step_name, status in process_steps:
        icon = "✅" if status else "❌"
        print(f"   {icon} {step_name}")
    
    # User interaction summary
    print("\n👤 User Interaction:")
    workflow_terminated = state.get('workflow_terminated_by_user', False)
    if workflow_terminated:
        termination_node = state.get('termination_node', 'Unknown')
        print(f"   ⏹️ Workflow terminated by user after: {termination_node}")
    else:
        print(f"   ✅ Workflow completed through all nodes")
    
    # Job analysis summary
    job_reqs = state.get('job_requirements', {})
    if job_reqs:
        print(f"\n🎯 Job Analysis:")
        print(f"   Industry: {job_reqs.get('industry_domain', 'Not specified')}")
        print(f"   Essential requirements: {len(job_reqs.get('essential_requirements', []))}")
        print(f"   Key technologies: {len(job_reqs.get('key_technologies', []))}")
    
    # Errors and warnings
    errors = state.get('errors', [])
    warnings = state.get('warnings', [])
    
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors[:5]:  # Show first 5
            print(f"   - {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
    
    if warnings:
        print(f"\n⚠️ Warnings ({len(warnings)}):")
        for warning in warnings[:5]:  # Show first 5
            print(f"   - {warning}")
        if len(warnings) > 5:
            print(f"   ... and {len(warnings) - 5} more")
    
    # Output files
    output_file = state.get('output_file')
    if output_file:
        print(f"\n📄 Output:")
        print(f"   Working CV: {output_file}")
        print(f"   Rendered files: rendercv_output/")
    
    print("\n" + "="*60)

def run_interactive_workflow():
    """Run the interactive workflow with user interaction after each node."""
    print("🚀 Resume Agent - Starting interactive tailoring process...")
    print("="*60)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Please create a .env file with your OpenAI API key:")
        print("   1. Copy env_template.txt to .env")
        print("   2. Replace 'your-openai-api-key-here' with your actual API key")
        print("   3. Get your API key from: https://platform.openai.com/api-keys")
        return
    
    # Load initial data
    state = load_initial_data()
    
    if state['errors']:
        print("❌ Cannot proceed due to initial data loading errors")
        print_interactive_summary(state)
        return
    
    # Set up interactive workflow
    interactive_nodes = setup_interactive_workflow()
    
    # Define the workflow sequence
    workflow_sequence = [
        "parse_job_ad",
        "update_summary", 
        "tailor_experience",
        "tailor_projects",
        "tailor_education",
        "tailor_certifications",
        "tailor_extracurricular",
        "tailor_skills",
        "reorder_sections",
        "convert_au_english",
        "validate_yaml"
    ]
    
    print("\n⚙️ Running interactive tailoring workflow...")
    print("-" * 40)
    
    try:
        # Execute each node in sequence
        for node_name in workflow_sequence:
            if node_name in interactive_nodes:
                state = interactive_nodes[node_name](state)
                
                # Check if user chose to stop
                if state.get('workflow_terminated_by_user', False):
                    break
            else:
                print(f"⚠️ Node {node_name} not found in interactive nodes")
        
        # Print final summary
        print_interactive_summary(state)
        
        if state.get('workflow_terminated_by_user', False):
            print("⏹️ Interactive workflow completed - terminated by user")
        elif not state.get('errors'):
            print("🎉 Interactive resume tailoring completed successfully!")
        else:
            print("⚠️ Interactive resume tailoring completed with errors - please review")
            
    except Exception as e:
        print(f"❌ Fatal error during interactive workflow execution: {str(e)}")
        print("   Check your OpenAI API key and internet connection")

if __name__ == "__main__":
    run_interactive_workflow() 