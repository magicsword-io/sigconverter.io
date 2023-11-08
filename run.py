#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import base64
from flask import Flask, render_template, request, Response

from sigma.conversion.base import Backend
from sigma.plugins import InstalledSigmaPlugins
from sigma.collection import SigmaCollection
from sigma.exceptions import SigmaError

app = Flask(__name__)
plugins = InstalledSigmaPlugins.autodiscover()
backends = plugins.backends
pipeline_resolver = plugins.get_pipeline_resolver()
pipelines = list(pipeline_resolver.list_pipelines())


@app.route("/")
def home():
    formats = []
    for backend in backends.keys():
        for name, description in plugins.backends[backend].formats.items():
            formats.append(
                {"name": name, "description": description, "backend": backend}
            )

    for name, pipeline in pipelines:
        if len(pipeline.allowed_backends) > 0:
            pipeline.backends = ", ".join(pipeline.allowed_backends)
        else:
            pipeline.backends = "all"

    return render_template(
        "index.html", backends=backends, pipelines=pipelines, formats=formats
    )


@app.route("/sigma", methods=["POST"])
def convert():
    # get params from request
    rule = str(base64.b64decode(request.json["rule"]), "utf-8")
    # check if input is valid yaml
    try:
        yaml.safe_load(rule)
    except:
        print("error")
        return Response(
            f"YamlError: Malformed yaml file", status=400, mimetype="text/html"
        )

    pipeline = []
    if request.json["pipeline"]:
        for p in request.json["pipeline"]:
            pipeline.append(p)

    target = request.json["target"]
    format = request.json["format"]

    backend_class = backends[target]
    processing_pipeline = pipeline_resolver.resolve(pipeline)
    backend: Backend = backend_class(processing_pipeline=processing_pipeline)

    try:
        sigma_rule = SigmaCollection.from_yaml(rule)
        result = backend.convert(sigma_rule, format)
        if isinstance(result, list):
            result = result[0]
    except SigmaError as e:
        return Response(f"SigmaError: {str(e)}", status=400, mimetype="text/html")

    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
