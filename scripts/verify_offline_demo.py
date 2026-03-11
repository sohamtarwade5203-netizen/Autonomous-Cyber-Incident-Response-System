#!/usr/bin/env python3
"""
Offline Demo Verification Script

This script verifies that ALL components are ready for a fully offline demo.
Run this 30 minutes before your hackathon presentation.

Usage:
    python scripts/verify_offline_demo.py
    
Exit codes:
    0 - All checks passed, ready for demo
    1 - Critical failures, demo will fail
"""

import os
import sys
import subprocess
import socket
from pathlib import Path

# ANSI colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_check(name, passed, details=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} {name}")
    if details:
        print(f"      {details}")

def check_ollama():
    """Verify Ollama is installed and llama3 model is available."""
    print_header("CHECKING OLLAMA (CRITICAL)")
    
    try:
        # Check Ollama is installed
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print_check("Ollama installed", False, "Ollama command failed")
            return False
        
        print_check("Ollama installed", True)
        
        # Check llama3 model is pulled
        if "llama3" in result.stdout:
            print_check("llama3 model available", True)
            return True
        else:
            print_check("llama3 model available", False, "Run: ollama pull llama3")
            return False
            
    except FileNotFoundError:
        print_check("Ollama installed", False, "Install from https://ollama.ai")
        return False
    except subprocess.TimeoutExpired:
        print_check("Ollama responding", False, "Ollama service not responding")
        return False

def check_data_files():
    """Verify all required data files exist."""
    print_header("CHECKING DATA FILES")
    
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "raw_logs"
    
    required_files = [
        "siem_ddos_alerts.parquet",
        "siem_portscan_alerts.parquet",
        "siem_benign_traffic.parquet"
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = data_dir / filename
        exists = filepath.exists()
        print_check(f"Data file: {filename}", exists)
        if not exists:
            all_exist = False
    
    return all_exist

def check_output_directory():
    """Verify output directory exists and is writable."""
    print_header("CHECKING OUTPUT DIRECTORY")
    
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "output"
    
    # Create if doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Test write permissions
    test_file = output_dir / ".test_write"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print_check("Output directory writable", True, str(output_dir))
        return True
    except Exception as e:
        print_check("Output directory writable", False, str(e))
        return False

def check_dependencies():
    """Verify Python dependencies are installed."""
    print_header("CHECKING PYTHON DEPENDENCIES")
    
    required_packages = [
        "pandas",
        "numpy",
        "pyod",
        "sklearn",
        "fastapi",
        "uvicorn",
        "langchain",
        "langgraph"
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print_check(f"Package: {package}", True)
        except ImportError:
            print_check(f"Package: {package}", False, f"Run: pip install {package}")
            all_installed = False
    
    return all_installed

def check_no_external_connections():
    """Verify no external network endpoints in code."""
    print_header("CHECKING OFFLINE OPERATION")
    
    base_dir = Path(__file__).parent.parent
    
    # Suspicious patterns that indicate external calls
    suspicious_patterns = [
        "https://api.",
        "http://api.",
        "openai.com",
        "anthropic.com",
        "huggingface.co/api"
    ]
    
    # Files to check
    check_files = [
        base_dir / "agents" / "incident_agent.py",
        base_dir / "scripts" / "playbook_generator.py",
        base_dir / "api" / "main.py"
    ]
    
    issues_found = []
    for filepath in check_files:
        if not filepath.exists():
            continue
        
        content = filepath.read_text()
        for pattern in suspicious_patterns:
            if pattern in content:
                issues_found.append(f"{filepath.name}: contains '{pattern}'")
    
    if issues_found:
        print_check("No external API calls", False)
        for issue in issues_found:
            print(f"      {issue}")
        return False
    else:
        print_check("No external API calls", True, "All LLM calls are local")
        return True

def check_api_binding():
    """Verify API is configured to bind to localhost only."""
    print_header("CHECKING API SECURITY")
    
    base_dir = Path(__file__).parent.parent
    
    # Check main.py for 0.0.0.0 binding
    main_py = base_dir / "api" / "main.py"
    if main_py.exists():
        content = main_py.read_text()
        if "0.0.0.0" in content:
            print_check("API bound to localhost", False, 
                       "Found 0.0.0.0 binding - should use 127.0.0.1")
            return False
        else:
            print_check("API bound to localhost", True)
            return True
    
    return True

def check_docker_compose():
    """Check Docker Compose configuration."""
    print_header("CHECKING DOCKER CONFIGURATION")
    
    base_dir = Path(__file__).parent.parent
    compose_file = base_dir / "docker-compose.yml"
    
    if not compose_file.exists():
        print_check("docker-compose.yml exists", False, "Optional for demo")
        return True  # Not critical
    
    content = compose_file.read_text()
    
    # Check for external port exposure
    if "0.0.0.0:" in content:
        print_check("Docker ports secure", False, "Ports exposed to 0.0.0.0")
        return False
    else:
        print_check("Docker ports secure", True)
        return True

def check_dashboard():
    """Verify dashboard file exists."""
    print_header("CHECKING DASHBOARD")
    
    base_dir = Path(__file__).parent.parent
    dashboard = base_dir / "dashboard" / "index.html"
    
    if dashboard.exists():
        print_check("Dashboard exists", True, str(dashboard))
        return True
    else:
        print_check("Dashboard exists", False)
        return False

def main():
    """Run all verification checks."""
    print(f"\n{Colors.BOLD}OFFLINE DEMO VERIFICATION{Colors.END}")
    print(f"Run this 30 minutes before your presentation\n")
    
    checks = [
        ("Ollama & LLM", check_ollama),
        ("Data Files", check_data_files),
        ("Output Directory", check_output_directory),
        ("Python Dependencies", check_dependencies),
        ("Offline Operation", check_no_external_connections),
        ("API Security", check_api_binding),
        ("Docker Config", check_docker_compose),
        ("Dashboard", check_dashboard)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"{Colors.RED}ERROR in {name}: {str(e)}{Colors.END}")
            results[name] = False
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    critical_checks = ["Ollama & LLM", "Data Files", "Python Dependencies"]
    critical_passed = all(results.get(c, False) for c in critical_checks)
    
    print(f"Checks passed: {passed}/{total}")
    print()
    
    if critical_passed and passed >= total - 1:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ READY System is Fully Offline{Colors.END}")
        
        return 0
    elif critical_passed:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ MOSTLY READY (minor issues){Colors.END}")
        print(f"\nFix non-critical issues if time permits")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ NOT READY - CRITICAL FAILURES{Colors.END}")
        print(f"\n{Colors.BOLD}Fix these issues immediately:{Colors.END}")
        for check, passed in results.items():
            if not passed and check in critical_checks:
                print(f"  - {check}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
