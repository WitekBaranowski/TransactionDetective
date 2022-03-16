import os
import sys
from google.cloud import pubsub_v1

project_id = "fraudfinderdemo"
topic = "ff-tx"
subscription = "ff-tx-sub"
if len(sys.argv) > 1:
    subscription = sys.argv[1]
topic_name = f"projects/{project_id}/topics/{topic}"
subscription_name = f"projects/{project_id}/subscriptions/{subscription}"


def callback(message):
    print("callback...")
    print(message.data)
    message.ack()


with pubsub_v1.SubscriberClient() as subscriber:
    # subscriber.create_subscription(
    # name=subscription_name, topic=topic_name)
    future = subscriber.subscribe(subscription_name, callback)
    try:
        future.result()
    except KeyboardInterrupt:
        future.cancel()
