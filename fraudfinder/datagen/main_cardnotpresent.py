from helperfxns.fxns import load_json_from_gcs, uploadfile_gcs
import json

PROJECT = "fraudfinderdemo"
GCS_BUCKET_NAME = PROJECT
PREFIX = "datagen"
GCS_CONFIG_OBJECT = "config.json"


if __name__ == "__main__":

    for 
    cardnotpresent = load_json_from_gcs(project_id=PROJECT,
                                        bucket_name=GCS_BUCKET_NAME,
                                        filename=f"{PREFIX}/cardnotpresent.json")
    
    for tx_datetime in cardnotpresent:
        print(tx_datetime)