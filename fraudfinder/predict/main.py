import os
import sys
import pandas as pd
import json
import time
import urllib.request
from google.api_core import retry
from google.cloud import pubsub_v1
from flask import Flask
from flask_socketio import SocketIO
from google.cloud import aiplatform as vertex_ai
from google.cloud.aiplatform import Endpoint, Featurestore, EntityType
from google.cloud import bigquery

# initialize project and location.

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

# Initialize pubsub data.
subscription = "ff-tx-sub"
subscription_path = f"projects/{project}/subscriptions/{subscription}"
max_messages = 100

# Initialize web server and web sockets.
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))
if not PORT:
    PORT = 8080
socket = SocketIO(app, cors_allowed_origins="*")

# Initialize feature store data.
feature_store = None
customer_entity_type = None
terminal_entity_type = None


def entity_type_list_index(li, s):
    for i in li:
        path = i.resource_name
        if path.endswith(s):
            return path


feature_store_id = "fraud_finder_845"
feature_store_ready = False

def fs_connect():
    global feature_store_ready, feature_store_id, feature_store, customer_entity_type, terminal_entity_type
    feature_store_resource_name = (
        f"projects/{project}/locations/{location}/featurestores/{feature_store_id}"
    )
    try:
        feature_store = Featurestore(feature_store_resource_name)
        entity_types_list = feature_store.list_entity_types()
        if not entity_types_list:
            print("entity_types_list is empty!")
            return
        customer_entity_type = EntityType(
            entity_type_list_index(entity_types_list, "customer")
        )
        terminal_entity_type = EntityType(
            entity_type_list_index(entity_types_list, "terminal")
        )
        feature_store_ready = True
    except:
        print(f"error connecting to feature store {feature_store_id}")
        feature_store_ready = False


def set_fsid(id):
    global feature_store_id
    feature_store_id = id

"""
feature_store_list = Featurestore.list()
for i in feature_store_list:
    print(os.path.basename(i.resource_name))
ff_feature_store_resource_name = feature_store_list[1].resource_name
feature_store = Featurestore(feature_store_resource_name)

def entity_type_list_index(li, s):
    for i in li:
        path = i.resource_name
        if path.endswith(s):
            return path
"""

# get entity instances

# Enumerate aggregated features needed for prediction.
terminal_feature_ids = [
    "terminal_id_nb_tx_1day_window",
    "terminal_id_nb_tx_7day_window",
    "terminal_id_nb_tx_14day_window",
    "terminal_id_risk_1day_window",
    "terminal_id_risk_7day_window",
    "terminal_id_risk_14day_window",
]
customer_feature_ids = [
    "customer_id_avg_amount_1day_window",
    "customer_id_avg_amount_7day_window",
    "customer_id_avg_amount_14day_window",
    "customer_id_nb_tx_1day_window",
    "customer_id_nb_tx_7day_window",
    "customer_id_nb_tx_14day_window",
]

# Initialize Vertex Endpoint data.
endpoint = None


def set_endpoint(id):
    global endpoint
    endpoint_path = f"projects/{project}/locations/{location}/endpoints/{id}"
    endpoint = Endpoint(endpoint_path)


set_endpoint("5996727621797281792")



# Initialize BigQuery data.
bq_dataset_id = "tx"
bq_table_id = "predictions"
table_id = f"{project}.{bq_dataset_id}.{bq_table_id}"
bq_client = bigquery.Client()


def predict(endpoint, online_sample):
    online_features = pd.DataFrame.from_dict(online_sample)
    aggregated_customer_features = customer_entity_type.read(
        entity_ids=online_features["customer_entity_id"][0],
        feature_ids=customer_feature_ids,
    )
    aggregated_customer_features = aggregated_customer_features.to_dict("records")[0]

    aggregated_terminal_features = terminal_entity_type.read(
        entity_ids=online_features["terminal_entity_id"][0],
        feature_ids=terminal_feature_ids,
    )
    aggregated_terminal_features = aggregated_terminal_features.to_dict("records")[0]

    features = {
        "tx_amount": online_features["tx_amount"][0],
        "terminal_id": online_features["terminal_entity_id"][0],
        "customer_id": online_features["customer_entity_id"][0],
    }
    for i in customer_feature_ids:
        features[i] = aggregated_customer_features[i]
    for i in terminal_feature_ids:
        features[i] = aggregated_terminal_features[i]

    feature_list = []
    schema = [
        "customer_id_avg_amount_1day_window",
        "customer_id_avg_amount_7day_window",
        "customer_id_avg_amount_14day_window",
        "customer_id_nb_tx_1day_window",
        "customer_id_nb_tx_7day_window",
        "customer_id_nb_tx_14day_window",
        "tx_amount",
        "terminal_id_nb_tx_1day_window",
        "terminal_id_nb_tx_7day_window",
        "terminal_id_nb_tx_14day_window",
        "terminal_id_risk_1day_window",
        "terminal_id_risk_7day_window",
        "terminal_id_risk_14day_window",
    ]
    for i in schema:
        feature_list.append(features[i])
    prediction = endpoint.predict([feature_list])
    features["prediction"] = prediction.predictions[0]
    return features


def bq_insert(rows):
    errors = bq_client.insert_rows_json(table_id, rows)  # Make an API request.
    if not errors:
        print("New rows have been added.")
    else:
        print(f"Encountered errors while inserting rows: {errors}")


def run():
    with pubsub_v1.SubscriberClient() as subscriber:
        while True:
            while not feature_store_ready:
                fs_connect()
                time.sleep(1)

            response = subscriber.pull(
                request={
                    "subscription": subscription_path,
                    "max_messages": max_messages,
                },
                retry=retry.Retry(deadline=300),
            )
            ack_ids = []
            for msg in response.received_messages:
                data = json.loads(msg.message.data)
                print(f"Received: {data}.")
                online_sample = {
                    "customer_entity_id": [data["CUSTOMER_ID"]],
                    "terminal_entity_id": [data["TERMINAL_ID"]],
                    "tx_id": [data["TX_ID"]],
                    "tx_amount": [data["TX_AMOUNT"]],
                }
                start_time = time.time()
                result = predict(endpoint, online_sample)
                latency = time.time() - start_time
                result["latency"] = latency
                print(result)
                bq_insert([result])
                socket.emit("tx", {"data": result})
                ack_ids.append(msg.ack_id)

            # Acknowledges the received messages so they will not be sent again.
            if ack_ids:
                subscriber.acknowledge(
                    request={"subscription": subscription_path, "ack_ids": ack_ids}
                )

            print(
                f"Received and acknowledged {len(response.received_messages)} messages from {subscription_path}."
            )
            print("sleeping")
            time.sleep(0.05)


@socket.on("connect")
def connect():
    socket.emit("log", {"data": "hello"})


@socket.on("config")
def config(msg):
    print("config update:", msg)
    set_endpoint(msg["endpoint_id"])
    set_fsid(msg["featurestore_id"])


@socket.on("start")
def start():
    run()


def home():
    return "Fraud Finder Prediction Microservice"


app.add_url_rule("/", view_func=home)

if __name__ == "__main__":
    # run()
    socket.run(app, host="0.0.0.0", port=PORT, use_reloader=True, debug=True)
