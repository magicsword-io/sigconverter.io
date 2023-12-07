#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import base64
import json
from flask import Flask, jsonify, render_template, request, Response

from sigma.conversion.base import Backend
from sigma.plugins import InstalledSigmaPlugins
from sigma.collection import SigmaCollection
from sigma.exceptions import SigmaError
from sigma.processing import pipeline
from sigma.processing.pipeline import ProcessingPipeline

app = Flask(__name__)

plugins = InstalledSigmaPlugins.autodiscover()

pipeline_generic = pipeline.ProcessingPipeline()

backends = plugins.backends
backend_names = [name for name, backend in backends.items()]

pipeline_resolver = plugins.get_pipeline_resolver()
pipelines = list(pipeline_resolver.list_pipelines())
pipeline_names = [p[0] for p in pipelines]

allowed_backends = {}

for name, pipeline in pipelines:
    if len(pipeline.allowed_backends) > 0:
        allowed_backends[name] = ", ".join(pipeline.allowed_backends)
    else:
        allowed_backends[name] = "all"

formats = []
for backend in backends.keys():
    for name, description in plugins.backends[backend].formats.items():
        formats.append({"name": name, "description": description, "backend": backend})


@app.route("/")
def home():
    for name, pipeline in pipelines:
        if len(pipeline.allowed_backends) > 0:
            pipeline.backends = ", ".join(pipeline.allowed_backends)
        else:
            pipeline.backends = "all"

    return render_template(
        "index.html", backends=backends, pipelines=pipelines, formats=formats
    )


@app.route("/getpipelines", methods=["GET"])
def get_pipelines_api():
    return jsonify(pipeline_names)


@app.route("/getbackends", methods=["GET"])
def get_backends_api():
    return jsonify(backend_names)


@app.route("/getformats", methods=["GET"])
def get_formats_api():
    return jsonify(formats)


@app.route("/getpipelineallowedbackend", methods=["GET"])
def get_pipeline_allowed_backend():
    return jsonify(allowed_backends)


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

    custom_pipelines_list = []
    if request.json["pipelineYml"]:
        pipelineYml = str(base64.b64decode(request.json["pipelineYml"]), "utf-8")
        pipelineYml_list = pipelineYml.split("\n---")
        for pipeline_ in pipelineYml_list:
            try:
                custom_pipelines_list.append(pipeline_generic.from_yaml(pipeline_))
            except:
                return Response(
                    f"YamlError: Malformed Pipeline Yaml", status=400, mimetype="text/html"
                )

    target = request.json["target"]
    format = request.json["format"]

    try:
        backend_class = backends[target]
    except:
        return Response(f"Unknown Backend", status=400, mimetype="text/html")
    
    try:
        processing_pipeline = pipeline_resolver.resolve(pipeline)
    except:
        return Response(f"Unknown Builtin Pipeline", status=400, mimetype="text/html")

    for pipeline_ in custom_pipelines_list:
        if isinstance(pipeline_, ProcessingPipeline):
            processing_pipeline += pipeline_

    backend: Backend = backend_class(processing_pipeline=processing_pipeline)

    try:
        sigma_rule = SigmaCollection.from_yaml(rule)
        result = backend.convert(sigma_rule, format)
        if isinstance(result, list):
            result = result[0]
    except SigmaError as e:
        return Response(f"SigmaError: {str(e)}", status=400, mimetype="text/html")
    except:
        return Response(f"UnknownError: {str(e)}", status=400, mimetype="text/html")

    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
