import os
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
    
project_id = "fraudfinderdemo"
topic = "ff-tx"
topic_name = f"projects/{project_id}/topics/{topic}"
future = publisher.publish(topic_name, b"Message", spam="eggs")
future.result()
