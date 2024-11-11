#!/usr/bin/env python3
import os
import json
import yaml
import base64
import subprocess
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__)

def run_sigma_command(version, endpoint, method='GET', data=None):
    """Execute command in specific version's virtual environment"""
    version_path = Path(__file__).parent / "sigma" / version
    venv_path = version_path / "venv" / "bin" / "python"
    worker_path = Path(__file__).parent / "worker.py"
    
    # Verify paths exist
    if not venv_path.exists():
        return None, f"Virtual environment not found for Sigma version {version}"
    if not worker_path.exists():
        return None, f"Worker script not found"
    
    cmd = [str(venv_path), str(worker_path), endpoint]
    
    # Add backend for formats and pipelines endpoints
    if endpoint in ['formats', 'pipelines'] and data and 'target' in data:
        cmd.append(data['target'])
    
    # Add conversion parameters
    if endpoint == 'convert' and data:
        cmd.extend([
            data['target'],
            data['rule']
        ])
        if data.get('format'):
            cmd.append(data['format'])
        if data.get('pipeline'):
            cmd.append(','.join(data['pipeline']))
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, None
    except subprocess.CalledProcessError as e:
        return None, e.stderr

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/v1/sigma-versions", methods=["GET"])
def get_versions():
    sigma_path = Path(__file__).parent / "sigma"
    versions = [
        d.name for d in sigma_path.iterdir() 
        if d.is_dir() and (d / "venv").exists()
    ]
    # Filter and sort versions
    clean_versions = []
    for version in versions:
        try:
            clean_version = version.lstrip('v')
            [int(x) for x in clean_version.split('.')]
            clean_versions.append(clean_version)
        except ValueError:
            continue
            
    return jsonify(sorted(clean_versions, key=lambda v: tuple(map(int, v.split("."))), reverse=True))

@app.route("/api/v1/<version>/targets", methods=["GET"])
def get_targets(version):
    output, error = run_sigma_command(version, 'targets')
    if error:
        return Response(f"Error: {error}", status=400)
    return Response(output, mimetype='application/json')

@app.route("/api/v1/<version>/formats", methods=["GET"])
def get_formats(version):
    target = request.args.get('target', '').strip()
    if not target:
        return Response("Error: No backend specified", status=400)
    
    data = {'target': target}
    output, error = run_sigma_command(version, 'formats', data=data)
    if error:
        return Response(error, status=400)
    return Response(output, mimetype='application/json')

@app.route("/api/v1/<version>/pipelines", methods=["GET"])
def get_pipelines(version):
    target = request.args.get('target', '').strip()
    if not target:
        return Response("Error: No backend specified", status=400)
    
    data = {'target': target}
    output, error = run_sigma_command(version, 'pipelines', data=data)
    if error:
        return Response(error, status=400)
    return Response(output, mimetype='application/json')

@app.route("/api/v1/<version>/convert", methods=["POST"])
def convert(version):
    try:
        data = request.json
        rule = str(base64.b64decode(data["rule"]), "utf-8")
        yaml.safe_load(rule)  # Validate YAML
        
        # Prepare data for worker
        worker_data = {
            "rule": rule,
            "target": data["target"],
            "format": data.get("format"),
            "pipeline": data.get("pipeline", [])
        }
        
        output, error = run_sigma_command(version, 'convert', data=worker_data)
        if error:
            return Response(error, status=400)
        return Response(output, mimetype='application/json')
        
    except yaml.YAMLError:
        return Response("YamlError: Malformed yaml file", status=400)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=400)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
