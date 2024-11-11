#!/usr/bin/env python3
import os
import json
import subprocess
from pathlib import Path

def get_sigma_versions():
    """Fetch the 10 latest versions of sigma-cli from PyPI"""
    import requests
    response = requests.get("https://pypi.org/pypi/sigma-cli/json")
    versions = sorted(response.json()["releases"].keys())
    return versions[-10:]  # Return 10 latest versions

def get_sigma_backends():
    """Fetch all available Sigma backends from the plugin directory"""
    import requests
    try:
        response = requests.get("https://raw.githubusercontent.com/SigmaHQ/pySigma-plugin-directory/main/pySigma-plugins-v1.json")
        data = response.json()
        
        # Skip problematic backends
        excluded_backends = {
            "pySigma-backend-hawk",     # https://github.com/redsand/pySigma-backend-hawk/issues/1
            "pySigma-backend-kusto"    # Known issues with kusto backend
        }
        
        backends = []
        for plugin_id, plugin_info in data.get("plugins", {}).items():
            if "package" in plugin_info:
                package = plugin_info["package"]
                # Skip if package or its git URL is in excluded list
                if package not in excluded_backends and not any(excluded in package for excluded in excluded_backends):
                    backends.append(package)
        
        print(f"Found {len(backends)} backends to attempt installation")
        return backends
    except Exception as e:
        print(f"Error fetching backends: {e}")
        return ["pysigma-backend-splunk", "pysigma-backend-elasticsearch"]

def install_core_backends(python_path, sigma_version):
    """Install core backends that are known to work"""
    # First install required dependencies
    base_packages = [
        "pyyaml",
        "setuptools",
        "wheel",
        "requests",
        f"sigma-cli=={sigma_version}"  # Install sigma-cli first
    ]
    
    # Install base packages
    for package in base_packages:
        try:
            print(f"Installing {package}...")
            subprocess.run([
                str(python_path), "-m", "pip", "install", "--no-cache-dir", package
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install {package}")
            return False
    
    # Install all available backends
    backends = get_sigma_backends()
    successful_installs = 0
    
    for backend in backends:
        try:
            print(f"Attempting to install backend: {backend}")
            subprocess.run([
                str(python_path), "-m", "pip", "install", "--no-cache-dir", backend
            ], check=True)
            successful_installs += 1
        except subprocess.CalledProcessError as e:
            print(f"Note: Backend {backend} failed to install - might be incompatible with sigma-cli {sigma_version}")
            continue
    
    print(f"Successfully installed {successful_installs} out of {len(backends)} backends")
    return successful_installs > 0  # Return True if at least one backend was installed

def setup_sigma_versions():
    """Setup Sigma versions with their virtual environments"""
    versions = get_sigma_versions()
    installed_count = 0
    base_path = Path(__file__).parent / "sigma"
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Get the current Python executable
    import sys
    python_executable = sys.executable
    
    for version in versions:
        print(f"\nSetting up Sigma version {version}")
        try:
            version_path = base_path / version
            version_path.mkdir(parents=True, exist_ok=True)
            
            # Setup virtual environment
            venv_path = version_path / "venv"
            print(f"Creating virtual environment at: {venv_path}")
            
            # Ensure the venv directory doesn't exist
            if venv_path.exists():
                import shutil
                shutil.rmtree(venv_path)
            
            # Create venv using current Python executable
            try:
                subprocess.run([
                    python_executable, "-m", "venv", 
                    "--clear", "--system-site-packages",
                    str(venv_path)
                ], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"venv creation output: {e.stdout}")
                print(f"venv creation error: {e.stderr}")
                raise
                
            # Verify venv creation
            python_path = venv_path / "bin" / "python"
            if not python_path.exists():
                raise Exception(f"Python executable not found at {python_path}")
            
            print(f"Virtual environment created at: {venv_path}")
            print(f"Python executable path: {python_path}")
            
            # Install core backends and verify
            if install_core_backends(str(python_path), version):
                # Copy worker script to version directory
                worker_path = Path(__file__).parent / "worker.py"
                if worker_path.exists():
                    import shutil
                    shutil.copy2(worker_path, version_path)
                
                installed_count += 1
                print(f"Successfully set up version {version}")
            else:
                print(f"Warning: Failed to install backends for version {version}")
            
        except Exception as e:
            print(f"Error setting up version {version}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return installed_count

if __name__ == "__main__":
    count = setup_sigma_versions()
    if count == 0:
        print("Error: No Sigma versions were installed successfully")
        exit(1)
        
    print(f"Successfully installed {count} Sigma versions")