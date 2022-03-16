import json
import os
import random
import urllib.request
import vlib
from vlib import Datasets, Models, Endpoints
from flask import Flask, request, Response, escape, render_template, jsonify
from google.protobuf.json_format import MessageToJson


def get_project_id():
    url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    req = urllib.request.Request(url)
    req.add_header("Metadata-Flavor", "Google")
    project_id = urllib.request.urlopen(req).read().decode()
    print("project_id:", project_id)
    return project_id

try:
    project = get_project_id()
except:
    project = "fraudfinderdemo"
location = "us-central1"
vlib.init(project=project, location=location)

app = Flask(__name__)
PORT = os.environ.get("PORT")
if not PORT:
    PORT = 8080


@app.route("/", methods=["GET"])
def home():
    return "Fraud Finder Server"


@app.route("/test", methods=["GET"])
def test():
    return "test called"


@app.route("/datasets", methods=["GET"])
@app.route("/datasets/get/<id>", methods=["GET"])
def datasets(id=None):
    datasets = Datasets(project=project, location=location)
    response = Response(headers={"Access-Control-Allow-Origin": "*"})
    if id:
        dataset = datasets.get(id)
        response.set_data(MessageToJson(dataset._pb))
    else:
        # If a specific dataset was not requested,
        # then enumerate and summarize all datasets.
        json = "["
        sep = ""
        for i in datasets.enumerate():
            if json != "[":
                sep = ", "
            json += sep + MessageToJson(i._pb)
        json += "]"
        print(json)
        response.set_data(json)
    return response


@app.route("/models", methods=["GET"])
@app.route("/models/get/<id>", methods=["GET"])
def models(id=None):
    models = Models(project=project, location=location)
    response = Response(headers={"Access-Control-Allow-Origin": "*"})
    if id:
        model = models.get(id)
        response.set_data(MessageToJson(model._pb))
    else:
        json = "["
        sep = ""
        for i in models.enumerate():
            if json != "[":
                sep = ", "
            json += sep + MessageToJson(i._pb)
        json += "]"
        print(json)
        response.set_data(json)
    return response


@app.route("/endpoints", methods=["GET"])
@app.route("/endpoints/get/<id>", methods=["GET"])
def endpoints(id=None):
    endpoints = Endpoints(project=project, location=location)
    response = Response(headers={"Access-Control-Allow-Origin": "*"})
    if id:
        endpoint = endpoints.get(id)
        response.set_data(MessageToJson(endpoint._pb))
    else:
        json = "["
        sep = ""
        for i in endpoints.enumerate():
            if json != "[":
                sep = ", "
            json += sep + MessageToJson(i._pb)
        json += "]"
        print(json)
        response.set_data(json)
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, use_reloader=True, debug=True, threaded=True)
