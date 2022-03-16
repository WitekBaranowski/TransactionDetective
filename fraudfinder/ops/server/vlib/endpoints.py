from vlib.globals import *
from google.cloud import aiplatform
from google.cloud.aiplatform_v1.services.endpoint_service import EndpointServiceClient
from google.cloud.aiplatform_v1.types import endpoint_service


class Endpoints:
    """This class encapsulates a collection of Vertex AI Endpoint."""

    def __init__(self, project=None, location=None):
        """Constructor for Endpoints class."""
        if not project or not location:
            raise Exception("missing project and/or location")
        client_opts = {"api_endpoint": api_endpoint}
        self.client = aiplatform.gapic.EndpointServiceClient(client_options=client_opts)
        self.parent = f"projects/{project}/locations/{location}"
        self.endpoints = {}

    def enumerate(self):
        """Return a list of Endpoints."""
        req = endpoint_service.ListEndpointsRequest(parent=self.parent)
        return self.client.list_endpoints(req)

    def get(self, id):
        """Get a specific endpoint."""
        name = f"{self.parent}/endpoints/{id}"
        try:
            endpoint = self.client.get_endpoint(name=name)
        except:
            raise Exception(f"can't get requested endpoint: {name}")
        self.endpoints[name] = endpoint
        return endpoint

    def monitoring(self, name, state, params=None):
        """Enable or disable model monitoring on a given endpoint"""
        print("Monitoring:", name, state, params)
