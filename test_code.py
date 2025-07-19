#!/usr/bin/env python3
"""Test script to verify code integrity without Docker"""

import sys
import ast
import json
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(message, status="info"):
    if status == "success":
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")
    elif status == "error":
        print(f"{Colors.RED}✗ {message}{Colors.END}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")
    else:
        print(f"{Colors.BLUE}→ {message}{Colors.END}")

def check_python_syntax(file_path):
    """Check if Python file has valid syntax"""
    try:
        with open(file_path, 'r') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

def check_json_syntax(file_path):
    """Check if JSON file has valid syntax"""
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)

def test_backend_code():
    """Test all backend Python files"""
    print_status("Testing backend Python files...")
    
    backend_files = list(Path('backend').rglob('*.py'))
    all_good = True
    
    for py_file in backend_files:
        if '__pycache__' in str(py_file):
            continue
            
        is_valid, error = check_python_syntax(py_file)
        if is_valid:
            print_status(f"Python syntax valid: {py_file}", "success")
        else:
            print_status(f"Python syntax error in {py_file}: {error}", "error")
            all_good = False
    
    return all_good

def test_frontend_code():
    """Test frontend configuration files"""
    print_status("Testing frontend configuration files...")
    
    json_files = [
        'frontend/package.json',
        'frontend/tsconfig.json',
        'frontend/tsconfig.node.json'
    ]
    
    all_good = True
    
    for json_file in json_files:
        if Path(json_file).exists():
            is_valid, error = check_json_syntax(json_file)
            if is_valid:
                print_status(f"JSON syntax valid: {json_file}", "success")
            else:
                print_status(f"JSON syntax error in {json_file}: {error}", "error")
                all_good = False
        else:
            print_status(f"File not found: {json_file}", "error")
            all_good = False
    
    return all_good

def check_imports():
    """Check if all imports in Python files are valid"""
    print_status("Checking Python imports...")
    
    # Add backend to path
    sys.path.insert(0, 'backend')
    
    import_errors = []
    
    # Try importing main modules
    modules_to_check = [
        'main',
        'core.database',
        'core.websocket_manager',
        'api.health',
        'api.auth',
        'api.behavioral',
        'api.memory',
        'api.integrations',
        'collectors.screen_collector',
        'collectors.communication_collector'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print_status(f"Import successful: {module}", "success")
        except ImportError as e:
            print_status(f"Import error in {module}: {str(e)}", "warning")
            import_errors.append((module, str(e)))
        except Exception as e:
            print_status(f"Error in {module}: {str(e)}", "warning")
            import_errors.append((module, str(e)))
    
    return len(import_errors) == 0, import_errors

def check_docker_files():
    """Check Docker configuration files"""
    print_status("Checking Docker configuration...")
    
    docker_files = [
        'docker-compose.yml',
        'backend/Dockerfile',
        'frontend/Dockerfile'
    ]
    
    all_good = True
    
    for docker_file in docker_files:
        if Path(docker_file).exists():
            print_status(f"Docker file exists: {docker_file}", "success")
        else:
            print_status(f"Docker file missing: {docker_file}", "error")
            all_good = False
    
    return all_good

def main():
    print(f"\n{Colors.BLUE}Digital Twin Platform - Code Verification{Colors.END}\n")
    
    # Test backend code
    backend_ok = test_backend_code()
    print()
    
    # Test frontend config
    frontend_ok = test_frontend_code()
    print()
    
    # Check imports
    imports_ok, import_errors = check_imports()
    print()
    
    # Check Docker files
    docker_ok = check_docker_files()
    print()
    
    # Summary
    print(f"\n{Colors.BLUE}Code Verification Summary{Colors.END}")
    print(f"Backend code: {'✓' if backend_ok else '✗'}")
    print(f"Frontend config: {'✓' if frontend_ok else '✗'}")
    print(f"Python imports: {'✓' if imports_ok else '✗'}")
    print(f"Docker files: {'✓' if docker_ok else '✗'}")
    
    if not imports_ok:
        print(f"\n{Colors.YELLOW}Import errors found:{Colors.END}")
        for module, error in import_errors:
            print(f"  - {module}: {error}")
        print(f"\n{Colors.YELLOW}To fix import errors, install dependencies:{Colors.END}")
        print(f"  cd backend && pip install -r requirements.txt")
    
    if backend_ok and frontend_ok and docker_ok:
        print(f"\n{Colors.GREEN}All code checks passed!{Colors.END}")
        print(f"\nTo start the platform:")
        print(f"1. Start Docker Desktop")
        print(f"2. Run: ./start_local.sh")
        print(f"\nOr manually:")
        print(f"1. docker-compose up -d postgres redis")
        print(f"2. cd backend && pip install -r requirements.txt && uvicorn main:app --reload")
        print(f"3. cd frontend && npm install && npm run dev")
    else:
        print(f"\n{Colors.RED}Some checks failed. Please fix the issues above.{Colors.END}")

if __name__ == "__main__":
    main()