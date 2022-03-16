def parse_config(options):
    """
    parses a config string (from file) and returns a dictionary
    """
    config = {}
    for option in options:
        option = option.strip()
        if option:
            name, value = option.split("=")
            config[name] = value
    return config


def load_json_from_gcs(project_id, bucket_name, filename):
    # Import the Google Cloud client library and JSON library
    from google.cloud import storage
    import json

    client = storage.Client(project_id)
    try:
        bucket = client.bucket(bucket_name)
        object = bucket.blob(filename)
        with object.open("rt") as f:
            data = json.load(f)
    except:
        print(f"GCS object {bucket_name}/{filename} not found")
        return None
    return data


def download_from_gcs(project_id, bucket_name, filename):
    # Import the Google Cloud client library and JSON library
    from google.cloud import storage
    import os

    client = storage.Client(project_id)
    bucket = client.bucket(bucket_name)
    object = bucket.blob(filename)
    if not os.path.exists("data"):
        os.makedirs("data")

    if "/" in filename:
        filename = filename.split("/")[-1]
    object.download_to_filename("data/" + filename)
    return "data/" + filename


def hashid(inputstring, length=16):
    """
    returns a hased string with length, length, given input string
    """
    import hashlib

    hash_int = int(hashlib.sha1(str(inputstring).encode("utf-8")).hexdigest(), 16) % (
        10 ** length
    )
    return str(hash_int).zfill(length)


def gen_tx_id(customer_id, terminal_id, datetime, extra=""):
    """
    generates a unique hashed string, based on customer, terminal and datetime
    """
    import hashlib

    stringtohash = f"{customer_id}_{terminal_id}_{datetime}{extra}".encode("utf-8")
    hashed_string = hashlib.sha1(stringtohash).hexdigest()
    return hashed_string


def gen_tx_amount(mean, std):
    """
    Randomly generates a non-negative tx amount loosely based on normal distribution
    """
    import random
    import numpy as np

    # generate a random transaction amount
    tx_amount = np.random.normal(mean, std)
    # if amount negative, draw from a uniform distribution
    if tx_amount < 0:
        tx_amount = np.random.uniform(0, mean * 2)

    # return rounded amount to 2 decimal places
    return tx_amount


def gen_tx(
    cid,
    curr_date_str,
    tx_datetime,
    hackdiceroll,
    hacked_customers_history,
    hacked_terminals_history,
    cust_terminals_dict,
    cust_mean_amount_dict,
    cust_std_amount_dict,
    hack_txamount_prob,
    hack_txamount_multiplier_mean,
    hack_txamount_multiplier_std,
    inflation_rate,
    tx_hacked_cardnotpresent=False,
):
    """
    Generates a tx
    """

    from datetime import datetime
    import random
    import numpy as np

    tx_terminal = random.choice(cust_terminals_dict[cid])

    tx_amount = gen_tx_amount(cust_mean_amount_dict[cid], cust_std_amount_dict[cid])

    tx_terminal_hacked = (
        1
        if hacked_terminals_history.get(curr_date_str, {}).get(tx_terminal, None)
        else 0
    )
    tx_customer_hacked = (
        1 if hacked_customers_history.get(curr_date_str, {}).get(cid, None) else 0
    )

    # if hacked
    if tx_customer_hacked:  # always 1 if tx_hacked_cardnotpresent
        tx_customer_hacked_probcheck = hackdiceroll <= hack_txamount_prob
        if tx_customer_hacked_probcheck:
            multiplier = np.random.normal(
                hack_txamount_multiplier_mean, hack_txamount_multiplier_std
            )
            tx_amount = (
                tx_amount * multiplier
                if multiplier >= 0
                else tx_amount * hack_txamount_multiplier_mean
            )
    else:
        tx_customer_hacked_probcheck = 0

    # add inflation
    tx_amount *= 1.0 + inflation_rate

    tx_id = gen_tx_id(cid, tx_terminal, tx_datetime, hackdiceroll)

    tx = {
        "TX_ID": tx_id,
        "TX_TS": tx_datetime,
        "CUSTOMER_ID": str(cid),
        "TERMINAL_ID": str(tx_terminal),
        "TX_AMOUNT": float(f"{tx_amount:.2f}"),
        "CARDPRESENT_HACKED": 1
        if (tx_customer_hacked_probcheck and not tx_hacked_cardnotpresent)
        else 0,
        "CARDNOTPRESENT_HACKED": 1 if tx_hacked_cardnotpresent else 0,
        "TERMINAL_HACKED": tx_terminal_hacked,
        "TX_FRAUD": 1
        if (
            tx_customer_hacked_probcheck
            or tx_terminal_hacked
            or tx_hacked_cardnotpresent
        )
        else 0,
    }

    return tx


def sendpubsubmessage_tx(data, project_id, topic):
    from google.cloud import pubsub_v1
    import json

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic)
    future = publisher.publish(topic_path, data=json.dumps(data).encode("utf-8"))
    return future.result()


def uploadfile_gcs(localfilepath, destfilepath, dest_bucket):
    from google.cloud import storage
    from datetime import datetime
    import time

    print(f"[uploadfile_gcs] Starting to upload from {localfilepath} to gs://{dest_bucket}/{destfilepath}...")
    start_time = time.time()

    storage_client = storage.Client()
    bucket = storage_client.bucket(dest_bucket)
    if not bucket.exists():
        storage_client.create_bucket(bucket, location="us-central1")
    bucket = storage_client.get_bucket(dest_bucket)
    blob = bucket.blob(destfilepath)
    blob.upload_from_filename(localfilepath)
    print(f"[uploadfile_gcs] {round(time.time() - start_time,2)}s elapsed.")

    blob.make_public()
    print(f"Public_url = {blob.public_url}")
    return f"gs://{dest_bucket}/{destfilepath}"


def transfer_gcstobq(
    gs_uri, schemadict, bq_dataset_id, bq_table_id, project_id, partition_field=None
):
    """
    given URI to a CSV file on Google Cloud Storage,
    using the schema dict, create a partitioned table in BigQuery
    """
    from google.cloud import bigquery
    import time

    print(f"[transfer_gcstobq] Starting...")
    start_time = time.time()
    # Construct a BigQuery client object.
    client = bigquery.Client()

    dataset_id = f"{project_id}.{bq_dataset_id}"
    table_id = f"{dataset_id}.{bq_table_id}"

    try:
        client.get_dataset(dataset_id)  # Make an API request.
    except:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "us-central1"
        client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {dataset_id}")

    #delete table if it already exists
    client.delete_table(table_id, not_found_ok=True)  # Make an API request.

    if partition_field == "TX_TS":
        job_config = bigquery.LoadJobConfig(
            schema=[bigquery.SchemaField(k, v) for k, v in schemadict.items()],
            skip_leading_rows=1,
            time_partitioning=bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="TX_TS",  # Name of the column to use for partitioning.
            ),
        )
    else:
        job_config = bigquery.LoadJobConfig(
            schema=[bigquery.SchemaField(k, v) for k, v in schemadict.items()],
            skip_leading_rows=1,
            write_disposition="WRITE_TRUNCATE",
        )

    load_job = client.load_table_from_uri(
        gs_uri, table_id, job_config=job_config
    )  # Make an API request.

    load_job.result()  # Wait for the job to complete.

    table = client.get_table(table_id)
    print(
        f"[transfer_gcstobq] Loaded {table.num_rows} rows to table {table_id}. {round(time.time() - start_time,2)}s elapsed."
    )


def bq_query(sql, async_flag=False):
    """
    If `async_flag` set to False (default),
        returns the query results for `sql` as a Pandas DataFrame,
    Else, submits query asynchronously and returns nothing.
    """
    from google.cloud import bigquery
    from google.api_core.exceptions import BadRequest

    client = bigquery.Client()
    # Try dry run before executing query to catch any errors
    try:
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        dry_run_job = client.query(sql, job_config=job_config)
    except BadRequest as err:
        print(err)
        return

    job_config = bigquery.QueryJobConfig()
    df = client.query(sql, job_config=job_config)

    if async_flag:
        return f"Query sent asynchronously for job id: {df.job_id}"
    else:
        df = df.result()  # wait for query to finish running
        return df.to_dataframe()


def prune_hacked_dict(hacked_history):
    """
    input: a dict containing hacked customers/terminals with dates as keys,
        where values is a dict of CUSTOMER_IDs and when their hacked status expires
    output:
        same dict but with future dates as keys removed
    """
    from datetime import datetime

    for datekey in list(hacked_history.keys()):
        if datetime.strptime(datekey, "%Y-%m-%d") >= (datetime.now()):
            del hacked_history[datekey]
    print(f"Last hacked date: {max(hacked_history.keys())}")
    return hacked_history


def remove_hacked(hacked_dict, current_date):
    """
    remove hacked customers/terminals if past their hacked deadline, current_date
    """
    from datetime import datetime

    # for each key (either a customer_id or terminal_id), check if deadline has been exceeded by current_date
    for key in list(hacked_dict.keys()):  # key is either a cust or term id
        hacked_deadline = datetime.strptime(hacked_dict[key], "%Y-%m-%d")

        if current_date > hacked_deadline:
            # deadline exceed, remove the key from the dict
            hacked_dict.pop(key, None)

    return hacked_dict


def add_hacked(
    hacked_dict, id_list, current_date, perc_to_hack, hacked_days_mean, hacked_days_std
):
    """
    add to hacked_dict new hacked customers/terminals with a random deadline that they will stay hacked
    """
    import random
    import numpy as np
    from datetime import datetime, timedelta

    new_hacked_id_list = random.sample(id_list, int(perc_to_hack * len(id_list)))

    for newid in new_hacked_id_list:
        # check if already hacked. If yes, then skip
        if not hacked_dict.get(newid, None):
            # add customer/terminal to hacked_dict with a deadline in the future determined by a normal distribution
            num_days_hacked = int(np.random.normal(hacked_days_mean, hacked_days_std))
            num_days_hacked = (
                num_days_hacked
                if num_days_hacked >= 1
                else random.randint(1, hacked_days_mean * 2)
            )
            hacked_dict[newid] = (
                current_date + timedelta(days=num_days_hacked)
            ).strftime("%Y-%m-%d")

    return hacked_dict


def update_hacked(
    hacked_dict, curr_date_dt, id_list, perc_to_hack, hacked_days_mean, hacked_days_std
):
    """
    INPUT:
    hacked_dict: a dictionary of dates as keys each containing dictionaries of IDs and hacked deadline as dates
    df: dataframe containing customer/terminal profiles data
    perc_to_hack: percentage chance to hack customer/terminal
    hacked_days_mean: average hack duration, in days
    hacked_days_std: std hack duration, in days

    OUTPUT:
    a dictionary which includes the current_date's date as a key if does not exist
    """
    from datetime import datetime

    curr_date_str = curr_date_dt.strftime("%Y-%m-%d")
    most_recent_hacked_date_str = max(hacked_dict.keys())
    if curr_date_str == most_recent_hacked_date_str:
        # if current date already exists as a key in the hacked_dict, exit
        return hacked_dict

    hacked_dict_current_date = add_hacked(
        hacked_dict[most_recent_hacked_date_str],
        id_list=id_list,
        current_date=curr_date_dt,
        perc_to_hack=perc_to_hack,
        hacked_days_mean=hacked_days_mean,
        hacked_days_std=hacked_days_std,
    )
    # print(hacked_dict_newdate)

    hacked_dict_current_date = remove_hacked(hacked_dict_current_date, curr_date_dt)

    hacked_dict[curr_date_str] = hacked_dict_current_date
    print(f"Added new hacked IDs to datekey: {curr_date_str}")
    return hacked_dict
