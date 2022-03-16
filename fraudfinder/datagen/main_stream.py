from google.cloud import storage
import sys
from stream.stream import stream
from helperfxns.fxns import load_json_from_gcs
import json

# PROJECT = "fraudfinderdemo"
# GCS_BUCKET_NAME = f"{PROJECT}_datagen"
# GCS_CONFIG_OBJECT = "config.json"


# required_args = ["tx_per_second", "dest_pubsub_topic", "refresh_config_cycle"]

# config_overrides = {}

# def get_config():
#     config_options = load_json_from_gcs(PROJECT, GCS_BUCKET_NAME, GCS_CONFIG_OBJECT)
#     print(config_options)
#     config_merged = {**config_options, **config_overrides}
#     for name in required_args:
#         if name not in config_merged:
#             raise ValueError(f"Missing required option {name}")
#     print("\nConfig:", json.dumps(config_merged, indent=4, sort_keys=True), "\n")
#     return config_merged


if __name__ == "__main__":
    stream()
