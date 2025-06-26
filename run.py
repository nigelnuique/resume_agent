#!/usr/bin/env python3
"""
Resume Agent - Automated Resume Tailoring System
Uses LangGraph to orchestrate AI-powered resume tailoring based on job advertisements.
"""

import os
import copy
import subprocess
from typing import Dict, Any
from langgraph.graph import StateGraph, END
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
from nodes.validate_yaml import validate_yaml

def setup_workflow() -> StateGraph:
    """Set up the LangGraph workflow for resume tailoring."""
    
    # Create the graph
    workflow = StateGraph(ResumeState)
    
    # Add core nodes (non-tailoring nodes)
    workflow.add_node("parse_job_ad", parse_job_ad)
    workflow.add_node("reorder_sections", reorder_sections)
    workflow.add_node("update_summary", update_summary)
    workflow.add_node("validate_yaml", validate_yaml)
    
    # Define the workflow sequence
    workflow.set_entry_point("parse_job_ad")
    
    # New order: Parse job → Reorder/optimize → Tailor individual sections → Final checks
    workflow.add_edge("parse_job_ad", "reorder_sections")
    workflow.add_edge("reorder_sections", "update_summary")

    # Helper function for conditional skipping
    def skip_if_removed(section_name, node_name):
        def wrapper(state: ResumeState) -> ResumeState:
            removed = state.get('removed_sections', [])
            if section_name in removed:
                print(f"⏭️ Skipping {node_name} (section '{section_name}' was removed)")
                state[f'{node_name}_skipped'] = True
                # Set the tailored flag to True so summary shows as completed
                state[f'{section_name}_tailored'] = True
                return state
            return globals()[node_name](state)
        return wrapper

    # Add tailoring nodes with conditional wrappers
    workflow.add_node("tailor_experience", skip_if_removed('experience', 'tailor_experience'))
    workflow.add_node("tailor_projects", skip_if_removed('projects', 'tailor_projects'))
    workflow.add_node("tailor_education", skip_if_removed('education', 'tailor_education'))
    workflow.add_node("tailor_certifications", skip_if_removed('certifications', 'tailor_certifications'))
    workflow.add_node("tailor_extracurricular", skip_if_removed('extracurricular', 'tailor_extracurricular'))
    workflow.add_node("tailor_skills", skip_if_removed('skills', 'tailor_skills'))

    workflow.add_edge("update_summary", "tailor_experience")
    workflow.add_edge("tailor_experience", "tailor_projects")
    workflow.add_edge("tailor_projects", "tailor_education")
    workflow.add_edge("tailor_education", "tailor_certifications")
    workflow.add_edge("tailor_certifications", "tailor_extracurricular")
    workflow.add_edge("tailor_extracurricular", "tailor_skills")
    workflow.add_edge("tailor_skills", "validate_yaml")
    workflow.add_edge("validate_yaml", END)
    
    return workflow

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

def save_working_cv(state: ResumeState, filename: str = "working_CV.yaml") -> None:
    """Save the working CV to file."""
    try:
        save_cv_to_file(state['working_cv'], filename)
        state['output_file'] = filename
        print(f"💾 Saved working CV to {filename}")
    except Exception as e:
        error_msg = f"Error saving working CV: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)

def render_cv(filename: str = "working_CV.yaml", output_dir: str = "rendercv_output") -> bool:
    """Render the CV using RenderCV."""
    print(f"🎨 Rendering CV using RenderCV...")
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Run RenderCV using Python module instead of command line
        cmd = ["python", "-m", "rendercv", "render", filename]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Move generated files to output directory
            import shutil
            import glob
            
            # Get base name from filename (without .yaml extension)
            base_name = os.path.splitext(filename)[0]
            cv_name = os.path.basename(base_name)
            
            # Look for generated files and move them to output directory
            generated_files = []
            for pattern in [f"{cv_name}*.pdf", f"{cv_name}*.html", f"{cv_name}*.png", f"{cv_name}*.md", f"{cv_name}*.typ"]:
                files = glob.glob(pattern)
                for file in files:
                    dest_path = os.path.join(output_dir, os.path.basename(file))
                    shutil.move(file, dest_path)
                    generated_files.append(os.path.basename(file))
            
            print("✅ CV rendered successfully!")
            print(f"   📄 Output files saved to {output_dir}/")
            
            # List moved files
            for file in generated_files:
                print(f"   - {file}")
            
            return True
        else:
            print("❌ RenderCV failed:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ RenderCV command timed out")
        return False
    except Exception as e:
        print(f"❌ Error rendering CV: {str(e)}")
        return False

def print_summary(state: ResumeState) -> None:
    """Print a summary of the tailoring process."""
    print("\n" + "="*60)
    print("📊 RESUME TAILORING SUMMARY")
    print("="*60)
    
    # Process status
    process_steps = [
        ("Job advertisement parsed", state.get('job_requirements', {})),
        ("Sections reordered", state.get('sections_reordered', False)),
        ("Summary updated", state.get('summary_updated', False)),
        ("Experience tailored", state.get('experience_tailored', False)),
        ("Projects tailored", state.get('projects_tailored', False)),
        ("Education tailored", state.get('education_tailored', False)),
        ("Skills tailored", state.get('skills_tailored', False)),
        ("Certifications tailored", state.get('certifications_tailored', False)),
        ("Extracurricular tailored", state.get('extracurricular_tailored', False)),
        ("YAML validated", state.get('yaml_validated', False))
    ]
    
    print("\n📋 Process Status:")
    for step_name, status in process_steps:
        icon = "✅" if status else "❌"
        print(f"   {icon} {step_name}")
    
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

def main():
    """Main function to run the resume tailoring agent."""
    print("🚀 Resume Agent - Starting tailoring process...")
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
        print_summary(state)
        return
    
    # Set up and compile the workflow
    print("\n🔧 Setting up workflow...")
    workflow = setup_workflow()
    
    # Use in-memory checkpointer for this demo
    # In production, you might want to use SqliteSaver for persistence
    app = workflow.compile()
    
    # Run the workflow
    print("\n⚙️ Running tailoring workflow...")
    print("-" * 40)
    
    try:
        # Execute the workflow
        final_state = app.invoke(state)
        
        # Save the working CV
        save_working_cv(final_state)
        
        # Render the CV if no critical errors
        if not final_state.get('errors'):
            success = render_cv()
            if not success:
                print("⚠️ CV tailoring completed but rendering failed")
        else:
            print("⚠️ Skipping CV rendering due to errors in tailoring process")
        
        # Print summary
        print_summary(final_state)
        
        if not final_state.get('errors'):
            print("🎉 Resume tailoring completed successfully!")
        else:
            print("⚠️ Resume tailoring completed with errors - please review")
            
    except Exception as e:
        print(f"❌ Fatal error during workflow execution: {str(e)}")
        print("   Check your OpenAI API key and internet connection")

if __name__ == "__main__":
    main() 