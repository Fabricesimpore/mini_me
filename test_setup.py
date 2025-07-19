#!/usr/bin/env python3
"""Test script to verify the Digital Twin platform setup"""

import sys
import subprocess
import time
import requests
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

def check_docker():
    """Check if Docker is installed and running"""
    print_status("Checking Docker installation...")
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Docker is installed", "success")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode == 0:
                print_status("Docker daemon is running", "success")
                return True
            else:
                print_status("Docker daemon is not running. Please start Docker.", "error")
                return False
        else:
            print_status("Docker is not installed", "error")
            return False
    except FileNotFoundError:
        print_status("Docker is not installed", "error")
        return False

def check_docker_compose():
    """Check if Docker Compose is installed"""
    print_status("Checking Docker Compose installation...")
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Docker Compose is installed", "success")
            return True
        else:
            print_status("Docker Compose is not installed", "error")
            return False
    except FileNotFoundError:
        # Try docker compose (v2)
        try:
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                print_status("Docker Compose V2 is installed", "success")
                return True
        except:
            pass
        print_status("Docker Compose is not installed", "error")
        return False

def check_project_structure():
    """Verify project structure is correct"""
    print_status("Checking project structure...")
    
    required_dirs = [
        'backend', 'frontend', 'infrastructure', 'ml_models', 'extension',
        'backend/api', 'backend/core', 'backend/collectors',
        'frontend/src', 'frontend/src/components', 'frontend/src/pages'
    ]
    
    required_files = [
        'docker-compose.yml', 
        'backend/Dockerfile', 'backend/requirements.txt', 'backend/main.py',
        'frontend/Dockerfile', 'frontend/package.json',
        'infrastructure/init.sql'
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_status(f"Directory {dir_path} exists", "success")
        else:
            print_status(f"Directory {dir_path} is missing", "error")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print_status(f"File {file_path} exists", "success")
        else:
            print_status(f"File {file_path} is missing", "error")
            all_good = False
    
    return all_good

def start_services():
    """Start Docker services"""
    print_status("Starting Docker services...")
    
    # First, try to stop any existing containers
    print_status("Stopping any existing containers...")
    subprocess.run(['docker-compose', 'down'], capture_output=True)
    
    # Start services
    print_status("Starting PostgreSQL and Redis...")
    result = subprocess.run(['docker-compose', 'up', '-d', 'postgres', 'redis'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print_status(f"Failed to start services: {result.stderr}", "error")
        return False
    
    # Wait for services to be ready
    print_status("Waiting for services to be ready...")
    time.sleep(10)
    
    # Check if services are running
    result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
    print(result.stdout)
    
    return True

def test_backend():
    """Test backend without Docker (for local development)"""
    print_status("Testing backend setup...")
    
    # Check if we can import the main module
    try:
        sys.path.insert(0, 'backend')
        import main
        print_status("Backend modules can be imported", "success")
        return True
    except Exception as e:
        print_status(f"Backend import error: {str(e)}", "error")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print_status("Testing API endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print_status("Health endpoint is working", "success")
        else:
            print_status(f"Health endpoint returned {response.status_code}", "error")
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to API. Make sure backend is running.", "warning")
        return False
    
    return True

def main():
    print(f"\n{Colors.BLUE}Digital Twin Platform - Setup Test{Colors.END}\n")
    
    # Check prerequisites
    if not check_docker():
        print_status("\nPlease install and start Docker before proceeding.", "error")
        return
    
    if not check_docker_compose():
        print_status("\nPlease install Docker Compose before proceeding.", "error")
        return
    
    # Check project structure
    if not check_project_structure():
        print_status("\nProject structure is incomplete. Please check the setup.", "error")
        return
    
    # Start services
    print_status("\nStarting services...", "info")
    if start_services():
        print_status("Services started successfully!", "success")
    else:
        print_status("Failed to start services", "error")
        return
    
    # Test backend
    print_status("\nTesting backend...", "info")
    test_backend()
    
    # Summary
    print(f"\n{Colors.BLUE}Setup Test Complete!{Colors.END}")
    print(f"\nNext steps:")
    print(f"1. Run: {Colors.GREEN}cd backend && pip install -r requirements.txt{Colors.END}")
    print(f"2. Run: {Colors.GREEN}cd frontend && npm install{Colors.END}")
    print(f"3. Start backend: {Colors.GREEN}cd backend && uvicorn main:app --reload{Colors.END}")
    print(f"4. Start frontend: {Colors.GREEN}cd frontend && npm run dev{Colors.END}")
    print(f"\nOr use Docker Compose: {Colors.GREEN}docker-compose up{Colors.END}")

if __name__ == "__main__":
    main()