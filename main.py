#!/usr/bin/env python3
"""
Autonomous Cyber Incident Response System - Main Orchestrator

This script runs the complete end-to-end pipeline:
1. Load and standardize security logs
2. Detect anomalies using PyOD
3. Correlate incidents using UEBA
4. Rank incidents by fidelity
5. Generate AI-powered response playbooks
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# ANSI color codes for better terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_step(step_num, message):
    """Print formatted step"""
    print(f"{Colors.OKCYAN}{Colors.BOLD}[Step {step_num}]{Colors.ENDC} {message}")

def print_success(message):
    """Print success message (ASCII-safe for Windows terminals)"""
    print(f"{Colors.OKGREEN}[OK] {message}{Colors.ENDC}")


def print_error(message):
    """Print error message (ASCII-safe for Windows terminals)"""
    print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")


def print_warning(message):
    """Print warning message (ASCII-safe for Windows terminals)"""
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")

def run_script(script_path, description):
    """Run a Python script and handle errors"""
    try:
        print(f"\n{Colors.OKBLUE}Running: {description}{Colors.ENDC}")
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        elapsed_time = time.time() - start_time
        print(result.stdout)
        print_success(f"Completed in {elapsed_time:.2f} seconds")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to execute {description}")
        print(f"\n{Colors.FAIL}Error Output:{Colors.ENDC}")
        print(e.stderr)
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success("Ollama is installed and accessible")
            if "llama3" in result.stdout:
                print_success("llama3 model is available")
                return True
            else:
                print_warning("llama3 model not found. Playbook generation may fail.")
                print(f"{Colors.WARNING}Run: ollama pull llama3{Colors.ENDC}")
                return False
        return False
    except FileNotFoundError:
        print_error("Ollama is not installed")
        print(f"{Colors.WARNING}Install from: https://ollama.ai/download{Colors.ENDC}")
        return False
    except Exception as e:
        print_warning(f"Could not verify Ollama: {str(e)}")
        return False

def check_data_files():
    """Check if required data files exist"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data", "raw_logs")
    
    required_files = [
        "siem_ddos_alerts.parquet",
        "siem_portscan_alerts.parquet",
        "siem_benign_traffic.parquet"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            print_success(f"Found: {file}")
        else:
            print_error(f"Missing: {file}")
            all_exist = False
    
    return all_exist

def main():
    """Main orchestration function"""
    print_header("AUTONOMOUS CYBER INCIDENT RESPONSE SYSTEM")
    print(f"{Colors.BOLD}Hackathon: Barclays Hack-O-Hire 2026{Colors.ENDC}")
    print(f"{Colors.BOLD}Problem Statement: Cyber Incident Response in Banking{Colors.ENDC}")
    print(f"\nExecution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, "scripts")
    
    # Pre-flight checks
    print_header("PRE-FLIGHT CHECKS")
    
    print_step("1", "Checking data files...")
    if not check_data_files():
        print_error("Required data files are missing. Please ensure data files are in data/raw_logs/")
        sys.exit(1)
    
    print_step("2", "Checking Ollama installation...")
    ollama_available = check_ollama()
    
    # Define pipeline steps
    pipeline_steps = [
        {
            "script": os.path.join(scripts_dir, "load_logs.py"),
            "description": "Load and Standardize Security Logs",
            "step": 1
        },
        {
            "script": os.path.join(scripts_dir, "anomaly_detection.py"),
            "description": "Anomaly Detection (PyOD + Temporal Burst)",
            "step": 2
        },
        {
            "script": os.path.join(scripts_dir, "ueba_correlation.py"),
            "description": "UEBA Correlation and Incident Grouping",
            "step": 3
        },
        {
            "script": os.path.join(scripts_dir, "fidelity_ranking.py"),
            "description": "Fidelity Ranking and Prioritization",
            "step": 4
        }
    ]
    
    # Add playbook generation only if Ollama is available
    if ollama_available:
        pipeline_steps.append({
            "script": os.path.join(scripts_dir, "playbook_generator.py"),
            "description": "AI-Powered Playbook Generation (Offline LLM)",
            "step": 5
        })
    else:
        print_warning("Skipping playbook generation (Ollama not available)")
    
    # Execute pipeline
    print_header("EXECUTING PIPELINE")
    
    failed_steps = []
    for step in pipeline_steps:
        print_step(step["step"], step["description"])
        success = run_script(step["script"], step["description"])
        
        if not success:
            failed_steps.append(step["description"])
            print_error(f"Pipeline failed at step {step['step']}")
            break
    
    # Summary
    print_header("EXECUTION SUMMARY")
    
    if not failed_steps:
        print_success("All pipeline steps completed successfully!")
        
        # ============================================================
        # ANALYST OPERATIONAL SUMMARY (NEW - Fix #1)
        # ============================================================
        print_header("ANALYST SUMMARY")
        
        # Load final results for metrics
        try:
            import pandas as pd
            alerts_path = os.path.join(base_dir, "output", "alerts_with_anomalies.csv")
            incidents_path = os.path.join(base_dir, "output", "ranked_incidents.csv")
            
            if os.path.exists(alerts_path) and os.path.exists(incidents_path):
                alerts_df = pd.read_csv(alerts_path)
                incidents_df = pd.read_csv(incidents_path)
                
                total_alerts = len(alerts_df)
                anomalous_alerts = alerts_df['is_anomaly'].sum()
                total_incidents = len(incidents_df)
                critical_incidents = len(incidents_df[incidents_df['priority'] == 'CRITICAL'])
                high_incidents = len(incidents_df[incidents_df['priority'] == 'HIGH'])
                
                print(f"{Colors.BOLD}OPERATIONAL METRICS:{Colors.ENDC}")
                print(f"  Total alerts ingested:        {total_alerts:,}")
                print(f"  Alerts flagged anomalous:     {anomalous_alerts:,} ({anomalous_alerts/total_alerts*100:.1f}%)")
                print(f"  Incidents created:            {total_incidents}")
                print(f"  Incidents requiring action:   {critical_incidents + high_incidents}")
                if ollama_available:
                    print(f"  Playbooks generated:          {total_incidents}")
                
                print(f"\n{Colors.BOLD}ANALYST WORKLOAD REDUCTION:{Colors.ENDC}")
                print(f"  Before: {total_alerts:,} alerts to review manually")
                print(f"  After:  {total_incidents} incidents to investigate")
                print(f"  Reduction: {(1 - total_incidents/total_alerts)*100:.2f}% fewer actions required")
                
                print(f"\n{Colors.BOLD}PRIORITY BREAKDOWN:{Colors.ENDC}")
                for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    count = len(incidents_df[incidents_df['priority'] == priority])
                    if count > 0:
                        print(f"  {priority}: {count} incident(s)")
        except Exception as e:
            print_warning(f"Could not generate detailed metrics: {str(e)}")
        
        # ============================================================
        
        print(f"\n{Colors.BOLD}Output files generated in:{Colors.ENDC} {os.path.join(base_dir, 'output')}")
        print(f"\n{Colors.OKGREEN}Key Outputs:{Colors.ENDC}")
        print(f"  • standardized_alerts.csv - Normalized security alerts")
        print(f"  • alerts_with_anomalies.csv - Anomaly-flagged alerts")
        print(f"  • correlated_incidents.csv - UEBA-correlated incidents")
        print(f"  • ranked_incidents.csv - Fidelity-ranked incidents")
        if ollama_available:
            print(f"  • incident_playbooks.txt - AI-generated response playbooks")
        
        print(f"\n{Colors.BOLD}Benefits Achieved:{Colors.ENDC}")
        print(f"  ✓ Reduced detection and response time")
        print(f"  ✓ Enhanced threat visibility across systems")
        print(f"  ✓ Reduced analyst fatigue through intelligent filtering")
        print(f"  ✓ Consistent, automated incident response")
        print(f"  ✓ Fully offline, secure processing")
        
    else:
        print_error("Pipeline execution failed!")
        print(f"\n{Colors.FAIL}Failed steps:{Colors.ENDC}")
        for step in failed_steps:
            print(f"  • {step}")
    
    print(f"\nExecution completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Pipeline interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
