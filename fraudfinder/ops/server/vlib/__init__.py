from google.cloud import aiplatform
from vlib.datasets import Datasets
from vlib.models import Models
from vlib.endpoints import Endpoints

initialized = False

def init(
    # your Google Cloud Project ID or number
    project=None,
    # the Vertex AI region you will use
    location=None,
    # Google Cloud Stoage bucket in same region as location
    # used to stage artifacts
    staging_bucket=None,
    # custom google.auth.credentials.Credentials
    # environment default creds used if not set
    credentials=None,
    # customer managed encryption key resource name
    # will be applied to all Vertex AI resources if set
    encryption_spec_key_name=None,
    # the name of the experiment to use to track
    # logged metrics and parameters
    experiment=None,
    # description of the experiment above
    experiment_description=None,
    ):
    aiplatform.init(
        project=project,
        location=location,
        staging_bucket=staging_bucket,
        credentials=credentials,
        encryption_spec_key_name=encryption_spec_key_name,
        experiment=experiment,
        experiment_description=experiment_description,
    )
    initialized = True
