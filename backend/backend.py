#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import base64
import importlib.metadata as metadata
from flask import Flask, jsonify, request, Response

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
pipeline_resolver = plugins.get_pipeline_resolver()
pipelines = list(pipeline_resolver.list_pipelines())

@app.route("/api/v1/targets", methods=["GET"])
def get_targets():
    response = []
    for name, backend in backends.items():
            response.append(
            {"name": name, "description": backend.name}
            )
    return jsonify(response)

@app.route("/api/v1/formats", methods=["GET"])
def get_formats():
    args = request.args
    response = []
    if len(args) == 0:
        for backend in backends.keys():
            for name, description in plugins.backends[backend].formats.items():
                response.append(
                    {"name": name, "description": description, "target": backend}
                )
    elif "target" in args:
        target = args.get("target")
        for backend in backends.keys():
            if backend == target:
                for name, description in plugins.backends[backend].formats.items():
                    response.append(
                        {"name": name, "description": description}
                    )

    return jsonify(response)

@app.route("/api/v1/pipelines", methods=["GET"])
def get_pipelines():
    args = request.args
    response = []
    if len(args) == 0:
        for name, pipeline in pipelines:
            response.append({"name": name, "targets": list(pipeline.allowed_backends)})
    elif "target" in args:
        target = args.get("target")
        for name, pipeline in pipelines:
            if (len(pipeline.allowed_backends) == 0) or (target in pipeline.allowed_backends):
                response.append({"name": name, "targets": list(pipeline.allowed_backends)})
    return jsonify(response)


@app.route("/api/v1/convert", methods=["POST"])
def convert():
    rule = str(base64.b64decode(request.json["rule"]), "utf-8")
    # check if input is valid yaml
    try:
        yaml.safe_load(rule)
    except:
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
        return Response(f"Unknown Target", status=400, mimetype="text/html")
    
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
    current_version = metadata.version("sigma-cli")
    port = int(f'8{current_version.replace(".","")}')
    app.run(host="0.0.0.0", port=port)
