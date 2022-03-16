import sys, os

sys.path.append("..")
from google.cloud import aiplatform
from datasets import Datasets
from models import Models
from endpoints import Endpoints
from os.path import basename

import urllib.request

## PARAMETERS GCP
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

aiplatform.init(project=project, location=location)

for ctor in (Datasets, Models, Endpoints):
    collection = ctor(project=project, location=location)
    for i in collection.enumerate():
        collection_type = i.name.split("/")[4][:-1]
        id = basename(i.name)
        print(f"{collection_type}: {i.display_name} ({id})")
        obj = collection.get(id)
        print("get: ", obj.name)
        """
        endpoints.monitoring(name, True, 1)
        endpoints.monitoring(name, False)
        try:
            mm_status = i.model_deployment_monitoring_job
        except:
            mm_status = "Disabled"
        print(f"endpoint: {i.display_name} ({basename(i.name)}), monitoring: {mm_status}")
        """
