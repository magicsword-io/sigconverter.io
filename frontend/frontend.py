#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
sigma_versions = [
    os.path.basename(it.path) for it in os.scandir("../backend/") if it.is_dir()
]


def version_key(version):
    return tuple(map(int, version.split(".")))


def get_port_from_version(version):
    pattern = r"^\d+\.\d+\.\d+$"
    if re.match(pattern, version):
        return int(f'8{version.replace(".", "")}')
    elif version == "latest":
        latest_version = sorted(
            sigma_versions, key=version_key, reverse=True)[0]
        return int(f'8{latest_version.replace(".", "")}')
    else:
        return None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/v1/sigma-versions", methods=["GET"])
def get_versions():
    return jsonify(sorted(sigma_versions, key=version_key, reverse=True))


@app.route("/api/v1/<version>/targets", methods=["GET"])
def get_targets(version):
    port = get_port_from_version(version)
    return requests.get(
        f"http://localhost:{port}/api/v1/targets", params=dict(request.args)
    ).json()


@app.route("/api/v1/<version>/formats", methods=["GET"])
def get_formats(version):
    port = get_port_from_version(version)
    return requests.get(
        f"http://localhost:{port}/api/v1/formats", params=dict(request.args)
    ).json()


@app.route("/api/v1/<version>/pipelines", methods=["GET"])
def get_pipelines(version):
    port = get_port_from_version(version)
    return requests.get(
        f"http://localhost:{port}/api/v1/pipelines", params=dict(request.args)
    ).json()


@app.route("/api/v1/<version>/convert", methods=["POST"])
def convert(version):
    port = get_port_from_version(version)
    payload = request.json
    return requests.post(f"http://localhost:{port}/api/v1/convert", json=payload).text


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
