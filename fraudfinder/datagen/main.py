import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, disconnect
from main_batch import batch
from batch.gen_transactions import batch_stop
from stream.stream import stream, stream_continue, stream_stop
from helperfxns.fxns import uploadfile_gcs, load_json_from_gcs
import json
import random
import urllib.request


app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))  # Get PORT setting from environment.
print(f"port: {PORT}")
socket = SocketIO(app, cors_allowed_origins="*")

def get_project_id():
    url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    req = urllib.request.Request(url)
    req.add_header("Metadata-Flavor", "Google")
    project_id = urllib.request.urlopen(req).read().decode()
    print("project_id:", project_id)
    return project_id

try:
    PROJECT = get_project_id()
except:
    PROJECT = "fraudfinderdemo"
BUCKET = PROJECT
PREFIX = "datagen"

stream_started = False

def sockprint(socket, s):
    socket.emit("log", {"data": s})
    print(s)


def gen_config():
    config = {
        "project_id": PROJECT,
        "bq_dataset_tx": "txstaging",
        "num_customers": 50000,
        "num_terminals": 5000,
        "radius": 5,
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "stream_limit": 180,
        "tx_per_day": 10000,
        "tx_per_second": 1,
        "refresh_config_cycle": 5,
        "refresh_hack_cycle": 86400,
        "dest_pubsub_topic": "prod",
        "inflation_rate": 0.0,
        "hack_txamount_prob": 0.5,
        "hack_txamount_multiplier_mean": 5,
        "hack_txamount_multiplier_std": 1,
        "cust_tohack_perc": 0.0004,
        "cust_hacked_days_mean": 10,
        "cust_hacked_days_std": 3,
        "term_tohack_perc": 0.0003,
        "term_hacked_days_mean": 14,
        "term_hacked_days_std": 2,
        "cardnotpresent_hack_probability": 0.001,
        "cardnotpresent_numfraudtx_mean": 10,
        "cardnotpresent_duration_minutes_mean": 10,
        "cardnotpresent_duration_minutes_std": 5,
    }

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    # upload to GCS as single source of truth for config settings
    project_id = config["project_id"]
    uploadfile_gcs(
        localfilepath="config.json",
        destfilepath=f"{PREFIX}/config.json",
        dest_bucket=BUCKET,
    )

    config_options = load_json_from_gcs(
        project_id, f"{PROJECT}", f"{PREFIX}/config.json"
    )
    print(config_options)


def home():
    home_page = """
    <h2>Fraudfinder Data Generation Microservice</h2>
    <a href="/batch">Run data batch generation service</a><br>
    <a href="/stream">Run data stream generation service</a><br>
    """

    return home_page


# Handler for a message recieved over 'connect' channel
@socket.on("connect")
def connect():
    emit("welcome")


@socket.on("stop")
def stop():
    sockprint(socket, "received stop request")
    stream_stop()
    batch_stop()


@socket.on("batch")
def start_batch():
    sockprint(socket, "received start batch request")
    batch(PROJECT, socket)


@socket.on("stream")
def start_stream():
    global stream_started
    stream_started = True
    sockprint(socket, "received start stream request")
    stream(PROJECT, socket)


@socket.on("continue")
def continue_stream():
    sockprint(socket, "received continue stream request")
    if stream_started:
        stream_continue()


@socket.on("echo")
def echo(msg):
    print(f"msg: {msg.text}")
    emit(msg)


app.add_url_rule("/", view_func=home)
app.add_url_rule(
    "/stream", view_func=stream, defaults={"PROJECT": PROJECT, "socket": socket}
)
app.add_url_rule(
    "/batch", view_func=batch, defaults={"PROJECT": PROJECT, "socket": socket}
)

if __name__ == "__main__":
    app.before_first_request(gen_config)
    socket.run(app, host="0.0.0.0", port=PORT, use_reloader=True, debug=True)
