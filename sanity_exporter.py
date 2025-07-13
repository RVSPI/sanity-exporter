#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SANITY Exporter - Universal project structure and content exporter
"""

import os
import sys
import json
import argparse
import logging
import chardet
import codecs
import time
import platform
import html

# Constants
TEXT_EXTENSIONS = [
    '.txt', '.py', '.js', '.java', '.kt', '.xml', '.gradle', 
    '.json', '.md', '.html', '.css', '.csv', '.ts', '.jsx', 
    '.tsx', '.yml', '.yaml', '.properties', '.c', '.cpp', '.h', 
    '.hpp', '.php', '.rb', '.go', '.swift', '.kt', '.kts'
]

# For colored output in Windows
try:
    import colorama
    colorama.init()
    COLORS_ENABLED = True
except ImportError:
    COLORS_ENABLED = False

# Color codes
COLORS = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m"
}

def print_header(text):
    """Print header"""
    if COLORS_ENABLED:
        print(f"{COLORS['HEADER']}{text}{COLORS['ENDC']}")
    else:
        print(text)

def print_success(text):
    """Print success message"""
    if COLORS_ENABLED:
        print(f"{COLORS['OKGREEN']}✓ {text}{COLORS['ENDC']}")
    else:
        print(f"[SUCCESS] {text}")

def print_error(text):
    """Print error message"""
    if COLORS_ENABLED:
        print(f"{COLORS['FAIL']}✗ {text}{COLORS['ENDC']}", file=sys.stderr)
    else:
        print(f"[ERROR] {text}", file=sys.stderr)

def print_progress(progress, message):
    """Simple progress display"""
    bar_length = 20
    block = int(round(bar_length * progress / 100))
    text = f"\rProgress: [{'#' * block}{'-' * (bar_length - block)}] {progress}% | {message}"
    sys.stdout.write(text)
    sys.stdout.flush()

def prompt_selection(prompt, options):
    """
    Show selection menu
    :param options: list of tuples (description, value)
    """
    print(f"\n{prompt}")
    for i, (desc, _) in enumerate(options, 1):
        print(f"{i}. {desc}")
    
    while True:
        try:
            choice = int(input("Your choice: "))
            if 1 <= choice <= len(options):
                return options[choice-1][1]
            print_error("Invalid choice!")
        except ValueError:
            print_error("Please enter a number!")

def prompt_input(prompt, default=None, example=None):
    """Prompt for input with default value and example"""
    if default:
        prompt = f"{prompt} (default: {default})"
    if example:
        prompt = f"{prompt} (e.g.: {example})"
    result = input(f"{prompt}: ")
    return result.strip() or default

def validate_directory(path):
    """Validate directory existence"""
    return os.path.exists(path) and os.path.isdir(path)

def is_supported_encoding(encoding):
    """Check if encoding is supported"""
    try:
        codecs.lookup(encoding)
        return True
    except LookupError:
        return False

def is_text_file(file_path):
    """Identify text files by extension"""
    return any(file_path.lower().endswith(ext) for ext in TEXT_EXTENSIONS)

def safe_read_file(file_path):
    """Universal file reading with encoding handling"""
    try:
        # Detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        # Validate encoding
        if not is_supported_encoding(encoding):
            encoding = 'utf-8'
        
        # Read file
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return f"\n[FILE READ ERROR: {str(e)}]\n"

def export_to_txt(project_dir, exclude_dirs, exclude_files, output_file, mode, progress_callback):
    """Export project to TXT format"""
    # Count files for progress bar
    total_files = 0
    if mode in ["both", "content"]:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            total_files += sum(
                1 for file in files 
                if file not in exclude_files 
                and is_text_file(os.path.join(root, file)))
    
    processed_files = 0
    with open(output_file, "w", encoding="utf-8") as out_file:
        # Export structure
        if mode in ["both", "structure"]:
            if progress_callback:
                progress_callback(0, "Building structure...")
            
            # Add spacing before section
            out_file.write("\n\n===== PROJECT STRUCTURE =====\n\n")
            
            # Tree generation
            for root, dirs, files in os.walk(project_dir):
                # Apply exclusions
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                files = [f for f in files if f not in exclude_files]
                
                # Calculate tree depth
                level = root.replace(project_dir, '').count(os.sep)
                indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''
                
                # Write directory
                out_file.write(f"{indent}{os.path.basename(root)}/\n")
                
                # Write files
                file_indent = '│   ' * level + '├── '
                last_file_indent = '│   ' * level + '└── '
                for i, f in enumerate(files):
                    prefix = last_file_indent if i == len(files) - 1 else file_indent
                    out_file.write(f"{prefix}{f}\n")
            
            # Add spacing after section
            out_file.write("\n\n")

        # Export content
        if mode in ["both", "content"]:
            # Add spacing before section
            out_file.write("\n\n===== FILE CONTENTS =====\n\n")
            
            for root, dirs, files in os.walk(project_dir):
                # Apply exclusions
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                files = [f for f in files if f not in exclude_files]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    if not is_text_file(file_path):
                        continue
                    
                    try:
                        # Read and write content with spacing
                        content = safe_read_file(file_path)
                        out_file.write(f"\n~~~~~ {os.path.relpath(file_path, project_dir)} ~~~~~~\n\n")
                        out_file.write(content)
                        out_file.write("\n\n")
                        
                        # Update progress
                        processed_files += 1
                        if progress_callback and total_files > 0:
                            progress = int((processed_files / total_files) * 100)
                            progress_callback(progress, f"Processed: {processed_files}/{total_files}")
                    except Exception as e:
                        logging.error(f"Error processing file {file_path}: {e}")
                        if progress_callback:
                            progress_callback(progress, f"Error in file: {file_path}")
    
    return True, ""

def export_to_json(project_dir, exclude_dirs, exclude_files, output_file, mode, progress_callback):
    """Export project to JSON format"""
    project_data = {
        "structure": {},
        "content": {}
    }
    
    # Count files for progress bar
    total_files = 0
    if mode in ["both", "content"]:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            total_files += sum(
                1 for file in files 
                if file not in exclude_files 
                and is_text_file(os.path.join(root, file)))
    
    processed_files = 0
    
    # Export structure
    if mode in ["both", "structure"]:
        if progress_callback:
            progress_callback(0, "Building structure...")
        
        for root, dirs, files in os.walk(project_dir):
            # Apply exclusions
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            files = [f for f in files if f not in exclude_files]
            
            rel_path = os.path.relpath(root, project_dir)
            if rel_path == ".":
                rel_path = ""
            
            # Create directory entry
            if rel_path not in project_data["structure"]:
                project_data["structure"][rel_path] = {
                    "directories": [],
                    "files": []
                }
            
            # Add subdirectories and files
            project_data["structure"][rel_path]["directories"] = dirs
            project_data["structure"][rel_path]["files"] = files
    
    # Export content
    if mode in ["both", "content"]:
        for root, dirs, files in os.walk(project_dir):
            # Apply exclusions
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            files = [f for f in files if f not in exclude_files]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not is_text_file(file_path):
                    continue
                
                try:
                    # Read file content
                    content = safe_read_file(file_path)
                    rel_path = os.path.relpath(file_path, project_dir)
                    project_data["content"][rel_path] = content
                    
                    # Update progress
                    processed_files += 1
                    if progress_callback and total_files > 0:
                        progress = int((processed_files / total_files) * 100)
                        progress_callback(progress, f"Processed: {processed_files}/{total_files}")
                except Exception as e:
                    logging.error(f"Error processing file {file_path}: {e}")
                    if progress_callback:
                        progress_callback(progress, f"Error in file: {file_path}")
    
    # Write JSON output
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        return True, ""
    except Exception as e:
        return False, str(e)

def export_to_html(project_dir, exclude_dirs, exclude_files, output_file, mode, progress_callback):
    """Export project to HTML format"""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Export: {os.path.basename(project_dir)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        h1, h2 {{ color: #2c3e50; }}
        .structure {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .file-content {{ margin-top: 20px; border-left: 3px solid #3498db; padding-left: 15px; }}
        .file-header {{ font-weight: bold; color: #2980b9; }}
        .content {{ white-space: pre-wrap; font-family: monospace; }}
        .tree {{ font-family: monospace; }}
    </style>
</head>
<body>
    <h1>Project Export: {html.escape(os.path.basename(project_dir))}</h1>
    <p>Exported at: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
    
    # Count files for progress bar
    total_files = 0
    if mode in ["both", "content"]:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            total_files += sum(
                1 for file in files 
                if file not in exclude_files 
                and is_text_file(os.path.join(root, file)))
    
    processed_files = 0
    
    # Export structure
    if mode in ["both", "structure"]:
        if progress_callback:
            progress_callback(0, "Building structure...")
        
        html_content += "<h2>Project Structure</h2>\n"
        html_content += "<div class='structure'>\n"
        html_content += "<div class='tree'>\n"
        
        for root, dirs, files in os.walk(project_dir):
            # Apply exclusions
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            files = [f for f in files if f not in exclude_files]
            
            # Calculate tree depth
            level = root.replace(project_dir, '').count(os.sep)
            indent = '│&nbsp;&nbsp;&nbsp;' * (level - 1) + '├── ' if level > 0 else ''
            
            # Write directory
            dir_name = html.escape(os.path.basename(root))
            html_content += f"<div>{indent}{dir_name}/</div>\n"
            
            # Write files
            file_indent = '│&nbsp;&nbsp;&nbsp;' * level + '├── '
            last_file_indent = '│&nbsp;&nbsp;&nbsp;' * level + '└── '
            for i, f in enumerate(files):
                prefix = last_file_indent if i == len(files) - 1 else file_indent
                file_name = html.escape(f)
                html_content += f"<div>{prefix}{file_name}</div>\n"
        
        html_content += "</div>\n"  # .tree
        html_content += "</div>\n"  # .structure
    
    # Export content
    if mode in ["both", "content"]:
        html_content += "<h2>File Contents</h2>\n"
        
        for root, dirs, files in os.walk(project_dir):
            # Apply exclusions
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            files = [f for f in files if f not in exclude_files]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not is_text_file(file_path):
                    continue
                
                try:
                    # Read file content
                    content = safe_read_file(file_path)
                    rel_path = os.path.relpath(file_path, project_dir)
                    
                    # Add file section
                    html_content += f"<div class='file-content'>\n"
                    html_content += f"<div class='file-header'>{html.escape(rel_path)}</div>\n"
                    html_content += f"<div class='content'>{html.escape(content)}</div>\n"
                    html_content += "</div>\n"
                    
                    # Update progress
                    processed_files += 1
                    if progress_callback and total_files > 0:
                        progress = int((processed_files / total_files) * 100)
                        progress_callback(progress, f"Processed: {processed_files}/{total_files}")
                except Exception as e:
                    logging.error(f"Error processing file {file_path}: {e}")
                    if progress_callback:
                        progress_callback(progress, f"Error in file: {file_path}")
    
    # Close HTML document
    html_content += "</body>\n</html>"
    
    # Write HTML output
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        return True, ""
    except Exception as e:
        return False, str(e)

def export_project(project_dir, exclude_dirs, exclude_files, output_file, mode, format, progress_callback):
    """
    Export project
    :param progress_callback: callback function(progress: int, message: str)
    :return: tuple (success: bool, message: str)
    """
    # Validate parameters
    if not os.path.exists(project_dir):
        return False, "Directory not found"
    
    # Add extension if missing
    if not output_file.endswith(f'.{format}'):
        output_file += f'.{format}'
    
    # Dispatch to format-specific exporters
    if format == "txt":
        return export_to_txt(project_dir, exclude_dirs, exclude_files, output_file, mode, progress_callback)
    elif format == "json":
        return export_to_json(project_dir, exclude_dirs, exclude_files, output_file, mode, progress_callback)
    elif format == "html":
        return export_to_html(project_dir, exclude_dirs, exclude_files, output_file, mode, progress_callback)
    else:
        return False, f"Unsupported format: {format}"

def load_templates():
    """Load built-in templates"""
    templates = {
        "Android": {
            "exclude_dirs": ["build", "gradle", ".gradle", ".idea", "captures"],
            "exclude_files": [".DS_Store", ".gitignore", ".pro", "*.iml", "gradlew", "gradlew.bat"]
        },
        "Web": {
            "exclude_dirs": ["node_modules", "dist", ".cache", "build"],
            "exclude_files": [".DS_Store", "package-lock.json"]
        },
        "Python": {
            "exclude_dirs": ["__pycache__", ".pytest_cache", "venv", "env"],
            "exclude_files": [".DS_Store", "*.pyc"]
        }
    }
    return templates

def interactive_mode():
    """Interactive mode"""
    print_header("   ~$~ SANITY EXPORTER ~$~")
    
    # Mode selection
    mode_options = [
        ("Structure and Content", "both"),
        ("Structure Only", "structure"),
        ("Content Only", "content")
    ]
    mode = prompt_selection("   Select export mode:", mode_options)
    
    # Template selection
    templates = load_templates()
    template_choice = prompt_selection(
        "   Use a template?",
        [("No", None)] + [(name, name) for name in templates.keys()]
    )
    
    # Apply template
    exclude_dirs = []
    exclude_files = []
    if template_choice:
        template = templates[template_choice]
        exclude_dirs = template.get("exclude_dirs", [])
        exclude_files = template.get("exclude_files", [])
        print_success(f"Template applied: {template_choice}")
    
    # Directory input
    while True:
        project_dir = prompt_input("\nProject directory path")
        if validate_directory(project_dir):
            break
        print_error("Directory does not exist!")
    
    # Additional exclusions
    if not template_choice or prompt_selection("   Add exclusions?", [("Yes", True), ("No", False)]):
        dirs_input = prompt_input("\nExclude folders (comma separated)", example="build, dist")
        if dirs_input:
            exclude_dirs += [e.strip() for e in dirs_input.split(",") if e.strip()]
        
        files_input = prompt_input("Exclude files (comma separated)", example="*.log, temp.*")
        if files_input:
            exclude_files += [e.strip() for e in files_input.split(",") if e.strip()]
    
    # Format selection
    format_options = [
        ("TXT", "txt"),
        ("JSON", "json"),
        ("HTML", "html")
    ]
    format = prompt_selection("   Select export format:", format_options)
    
    # Output filename
    default_name = f"export.{format}"
    output_name = prompt_input("\nOutput filename", default=default_name, example="project_export")
    
    # Confirmation
    print_header("\n        EXPORT SETTINGS:")
    print(f"    Mode: {next(desc for desc, val in mode_options if val == mode)}")
    print(f"    Format: {next(desc for desc, val in format_options if val == format)}")
    print(f"    Directory: {project_dir}")
    print(f"    Excluded folders: {', '.join(exclude_dirs) or 'none'}")
    print(f"    Excluded files: {', '.join(exclude_files) or 'none'}")
    print(f"    Output file: {output_name}")
    
    if prompt_selection("   Start export?", [("Yes", True), ("No", False)]):
        # Start export with progress
        start_time = time.time()
        try:
            success, error = export_project(
                project_dir,
                exclude_dirs,
                exclude_files,
                output_name,
                mode,
                format,
                print_progress
            )
            
            elapsed = time.time() - start_time
            
            if success:
                # Get absolute paths for better visibility
                abs_project_dir = os.path.abspath(project_dir)
                abs_output_file = os.path.abspath(output_name)
                
                # Display success report
                print("\n\n" + "~"*60)
                print_success("  EXPORT COMPLETED SUCCESSFULLY!")
                print(f"• Output file: {output_name}")
                print(f"  (Full path: {abs_output_file})")
                print(f"• Time taken: {elapsed:.2f} seconds")
                print(f"• Source directory: {abs_project_dir}")
                print("~"*60 + "\n")
            else:
                print_error(f"Export failed: {error}")
                elapsed = time.time() - start_time
                print(f"Time taken: {elapsed:.2f} seconds")
            
            # Wait for key press before closing
            if platform.system() == "Windows":
                os.system("pause")
            else:
                input("\nPress Enter to exit...")
                
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            if platform.system() == "Windows":
                os.system("pause")
            else:
                input("\nPress Enter to exit...")

def main():
    """Main command handler"""
    parser = argparse.ArgumentParser(
        prog="sanity-exporter",
        description="Utility for exporting project structure and content"
    )
    parser.add_argument("-d", "--dir", help="Project directory")
    parser.add_argument("-o", "--output", default="export.txt", help="Output file")
    parser.add_argument("-m", "--mode", choices=["both", "structure", "content"], default="both",
                        help="Export mode")
    parser.add_argument("-f", "--format", choices=["txt", "json", "html"], default="txt",
                        help="Output format")
    parser.add_argument("-t", "--template", help="Template name")
    parser.add_argument("--exclude-dirs", help="Exclude folders (comma separated)")
    parser.add_argument("--exclude-files", help="Exclude files (comma separated)")
    parser.add_argument("--list-templates", action="store_true", help="Show available templates")
    
    args = parser.parse_args()
    
    # Show template list
    if args.list_templates:
        templates = load_templates()
        print_header("AVAILABLE TEMPLATES:")
        for name in templates:
            print(f"- {name}")
        return
    
    # Batch mode
    if args.dir:
        # Apply template
        exclude_dirs = []
        exclude_files = []
        if args.template:
            templates = load_templates()
            if args.template in templates:
                template = templates[args.template]
                exclude_dirs = template.get("exclude_dirs", [])
                exclude_files = template.get("exclude_files", [])
            else:
                print_error(f"Template {args.template} not found!")
                return
        
        # Add exclusions from arguments
        if args.exclude_dirs:
            exclude_dirs += [e.strip() for e in args.exclude_dirs.split(",") if e.strip()]
        if args.exclude_files:
            exclude_files += [e.strip() for e in args.exclude_files.split(",") if e.strip()]
        
        # Validate
        if not validate_directory(args.dir):
            print_error("Invalid directory!")
            return
        
        # Start export
        start_time = time.time()
        try:
            success, error = export_project(
                args.dir,
                exclude_dirs,
                exclude_files,
                args.output,
                args.mode,
                args.format,
                print_progress
            )
            
            elapsed = time.time() - start_time
            
            if success:
                # Get absolute paths
                abs_project_dir = os.path.abspath(args.dir)
                abs_output_file = os.path.abspath(args.output)
                
                # Display success report
                print("\n\n" + "~"*60)
                print_success("    EXPORT COMPLETED SUCCESSFULLY!")
                print(f"• Output file: {args.output}")
                print(f"  (Full path: {abs_output_file})")
                print(f"• Time taken: {elapsed:.2f} seconds")
                print(f"• Source directory: {abs_project_dir}")
                print("~"*60 + "\n")
            else:
                print_error(f"Export failed: {error}")
                print(f"Time taken: {elapsed:.2f} seconds")
            
            # Wait for key press
            if platform.system() == "Windows":
                os.system("pause")
            else:
                input("\nPress Enter to exit...")
                
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            if platform.system() == "Windows":
                os.system("pause")
            else:
                input("\nPress Enter to exit...")
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()