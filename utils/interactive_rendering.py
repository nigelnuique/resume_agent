import os
import subprocess
import shutil
import glob
from typing import Dict, Any
from state import ResumeState, save_cv_to_file

def save_and_render_cv(state: ResumeState, node_name: str) -> bool:
    """
    Save the working CV and render it, then ask user if they want to proceed.
    
    Args:
        state: Current resume state
        node_name: Name of the node that just completed
        
    Returns:
        True if user wants to proceed, False if user wants to stop
    """
    print(f"\n🎨 Rendering CV after {node_name}...")
    
    try:
        # Save the working CV
        save_cv_to_file(state['working_cv'], "working_CV.yaml")
        state['output_file'] = "working_CV.yaml"
        print(f"💾 Saved working CV to working_CV.yaml")
        
        # Render the CV
        success = render_cv("working_CV.yaml", "rendercv_output")
        
        if success:
            print(f"✅ CV rendered successfully after {node_name}")
        else:
            print(f"⚠️ CV rendering failed after {node_name}")
        
        # Ask user if they want to proceed
        return ask_user_to_proceed(node_name)
        
    except Exception as e:
        error_msg = f"Error in save_and_render_cv: {str(e)}"
        print(f"❌ {error_msg}")
        state['errors'].append(error_msg)
        return ask_user_to_proceed(node_name)

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

def ask_user_to_proceed(node_name: str) -> bool:
    """
    Ask the user if they want to proceed to the next node.
    
    Args:
        node_name: Name of the node that just completed
        
    Returns:
        True if user wants to proceed, False if user wants to stop
    """
    print(f"\n{'='*60}")
    print(f"📋 Node '{node_name}' completed!")
    print(f"📄 CV has been rendered to rendercv_output/")
    print(f"{'='*60}")
    
    while True:
        response = input("\nDo you want to proceed to the next node? (y/n): ").strip().lower()
        
        if response in ['y', 'yes']:
            print("✅ Proceeding to next node...")
            return True
        elif response in ['n', 'no']:
            print("⏹️ Stopping workflow as requested by user")
            return False
        else:
            print("❓ Please enter 'y' for yes or 'n' for no")

def get_next_node_name(current_node: str) -> str:
    """
    Get the name of the next node in the workflow.
    
    Args:
        current_node: Name of the current node
        
    Returns:
        Name of the next node
    """
    workflow_sequence = [
        "parse_job_ad",
        "reorder_sections",
        "update_summary", 
        "tailor_experience",
        "tailor_projects",
        "tailor_education",
        "tailor_certifications",
        "tailor_extracurricular",
        "tailor_skills",
        "validate_yaml"
    ]
    
    try:
        current_index = workflow_sequence.index(current_node)
        if current_index < len(workflow_sequence) - 1:
            return workflow_sequence[current_index + 1]
        else:
            return "END"
    except ValueError:
        return "Unknown" 