from vlib.globals import *
from google.cloud import aiplatform
from google.cloud.aiplatform_v1.services.dataset_service import DatasetServiceClient
from google.cloud.aiplatform_v1.types import dataset_service


class Datasets:
    """This class encapsulates a collection of Vertex AI Datasets."""

    def __init__(self, project=None, location=None):
        """Constructor for Datasets class."""
        if not project or not location:
            raise Exception("missing project and/or location")
        client_opts = {"api_endpoint": api_endpoint}
        self.client = aiplatform.gapic.DatasetServiceClient(client_options=client_opts)
        self.parent = f"projects/{project}/locations/{location}"
        self.datasets = {}

    def enumerate(self):
        """Return a list of Datasets."""
        req = dataset_service.ListDatasetsRequest(parent=self.parent)
        return self.client.list_datasets(req)

    def get(self, id):
        """Get a specific dataset."""
        name = f"{self.parent}/datasets/{id}"
        try:
            dataset = self.client.get_dataset(name=name)
        except:
            raise Exception(f"can't get requested dataset: {name}")
        self.datasets[name] = dataset
        return dataset
