from vlib.globals import *
from google.cloud import aiplatform
from google.cloud.aiplatform_v1.services.model_service import ModelServiceClient
from google.cloud.aiplatform_v1.types import model_service


class Models:
    """This class encapsulates a collection of Vertex AI Models."""

    def __init__(self, project=None, location=None):
        """Constructor for Models class."""
        if not project or not location:
            raise Exception("missing project and/or location")
        client_opts = {"api_endpoint": api_endpoint}
        self.client = aiplatform.gapic.ModelServiceClient(client_options=client_opts)
        self.parent = f"projects/{project}/locations/{location}"
        self.models = {}

    def enumerate(self):
        """Return a list of Models."""
        req = model_service.ListModelsRequest(parent=self.parent)
        return self.client.list_models(req)

    def get(self, id):
        """Get a specific model."""
        name = f"{self.parent}/models/{id}"
        try:
            model = self.client.get_model(name=name)
        except:
            raise Exception(f"can't get requested model: {name}")
        self.models[name] = model
        return model
