#!/usr/bin/env python3
import os
import json
import subprocess
from pathlib import Path

def install_core_backends(python_path, sigma_version):
    """Install core backends that are known to work"""
    # First install required dependencies
    base_packages = [
        "pyyaml",
        f"sigma-cli=={sigma_version}",
        "pysigma>=0.9.0,<0.12.0",  # Compatible with 1.0.x
        "setuptools",
        "wheel"
    ]
    
    # Install using pip instead of uv for better dependency resolution
    for package in base_packages:
        try:
            print(f"Installing {package}...")
            subprocess.run([
                python_path, "-m", "pip", "install", package
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install {package}: {e}")
            return False
    
    # Install minimal set of backends
    backends = [
        "pysigma-backend-splunk>=0.9.0",
        "pysigma-backend-elasticsearch>=0.9.0"
    ]
    
    for backend in backends:
        try:
            print(f"Installing {backend}...")
            subprocess.run([
                python_path, "-m", "pip", "install", backend
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install {backend}: {e}")
    
    # Verify installation
    try:
        verify_cmd = [python_path, "-c", "import yaml; import sigma.backends"]
        subprocess.run(verify_cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print("Failed to verify package installation")
        return False

def setup_sigma_versions():
    """Setup Sigma versions with their virtual environments"""
    versions = ["1.0.0", "1.0.1", "1.0.2", "1.0.3", "1.0.4"]  # Hardcode versions for now
    installed_count = 0
    base_path = Path(__file__).parent / "sigma"
    base_path.mkdir(parents=True, exist_ok=True)
    
    for version in versions:
        print(f"\nSetting up Sigma version {version}")
        try:
            version_path = base_path / version
            version_path.mkdir(parents=True, exist_ok=True)
            
            # Setup virtual environment using venv instead of uv
            venv_path = version_path / "venv"
            subprocess.run([
                "python3", "-m", "venv", str(venv_path)
            ], check=True)
            
            python_path = str(venv_path / "bin" / "python")
            
            # Install core backends and verify
            if install_core_backends(python_path, version):
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
            continue
    
    return installed_count

if __name__ == "__main__":
    count = setup_sigma_versions()
    if count == 0:
        print("Error: No Sigma versions were installed successfully")
        exit(1)
    print(f"Successfully installed {count} Sigma versions") 