from google.cloud import pubsub_v1
import json
import random
import sys
from datetime import datetime, timedelta
import pandas as pd
from ast import literal_eval
import numpy as np
from helperfxns.fxns import (
    bq_query,
    uploadfile_gcs,
    load_json_from_gcs,
    prune_hacked_dict,
    update_hacked,
    download_from_gcs,
    gen_tx,
    sendpubsubmessage_tx,
)
from google.cloud import storage
import time
import urllib.request

## PARAMETERS GCP
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

GCS_DATAGEN_BUCKET_NAME = PROJECT
PREFIX = "datagen"
PUBSUB_TOPIC = "ff-tx"

Continue = True
queue_cardnotpresent_tx = {}
num_tx_generated = 0

def sockprint(socket, s):
    socket.emit("log", {"data": s})
    print(s)


def stream_continue():
    global Continue
    Continue = True


def stream_stop():
    global Continue
    Continue = False

def stream(PROJECT, socket):
    """
    1. Check if need to update which customers/terminals are currently hacked
        If yes need to update,
            - update hacked customers/terminals (remove if no longer hacked, add new hacked ones)
            - Add new hacked customers, write to GCS
            - Add new hacked terminals, write to GCS
    2. Generate transactions
        - import customer_terminal data
        -
    """
    sockprint(socket, "Starting stream()...")
    global Continue
    global num_tx_generated
    Continue = True
    # init_gcs()
    ## Initialize config file
    config = load_json_from_gcs(
        PROJECT, f"{GCS_DATAGEN_BUCKET_NAME}", f"{PREFIX}/config.json"
    )

    ## Initialize customer, terminal profiles
    start_time = time.time()

    custdf_fp = "customer_with_terminal_profiles.csv"
    custdf_local_fp = download_from_gcs(
        PROJECT, f"{GCS_DATAGEN_BUCKET_NAME}", f"{PREFIX}/demographics/{custdf_fp}"
    )
    sockprint(socket, custdf_local_fp)
    custdf = pd.read_csv(
        custdf_local_fp,
        dtype={"CUSTOMER_ID": object},
        converters={"available_terminals": literal_eval},
    )
    cust_id_list = list(custdf["CUSTOMER_ID"].values)
    cust_nb_mean_tx_per_day_list = list(custdf["mean_num_tx_per_sec"].values)

    # Initialize cust data as dicts, to be used as inputs to generate tx (gen_tx)
    cust_terminals_dict = custdf.set_index("CUSTOMER_ID")[
        "available_terminals"
    ].to_dict()
    cust_mean_amount_dict = custdf.set_index("CUSTOMER_ID")["mean_amount"].to_dict()
    cust_std_amount_dict = custdf.set_index("CUSTOMER_ID")["std_amount"].to_dict()

    termdf_fp = "terminal_profiles.csv"
    termdf_local_fp = download_from_gcs(
        PROJECT, f"{GCS_DATAGEN_BUCKET_NAME}", f"{PREFIX}/demographics/{termdf_fp}"
    )
    termdf = pd.read_csv(termdf_local_fp, dtype={"TERMINAL_ID": object})
    term_idlist = list(termdf["TERMINAL_ID"].values)
    sockprint(
        socket, f"Elapsed time for loading CSVs: {np.round(time.time()-start_time,1)}s"
    )

    ## Prune hacked customers/terminals after today, so the hacked data is up until today only
    start_time = time.time()
    hacked_customers_history = prune_hacked_dict(
        load_json_from_gcs(
            PROJECT,
            f"{GCS_DATAGEN_BUCKET_NAME}",
            f"{PREFIX}/hacked_customers_history.txt",
        )
    )
    hacked_terminals_history = prune_hacked_dict(
        load_json_from_gcs(
            PROJECT,
            f"{GCS_DATAGEN_BUCKET_NAME}",
            f"{PREFIX}/hacked_terminals_history.txt",
        )
    )
    sockprint(
        socket,
        f"Elapsed time for loading/pruning hacked dicts: {np.round(time.time()-start_time,1)}s",
    )

    ## Clear BigQuery table of tx that occur after a specific time, so that there is a seamless transition
    ## from historical to streaming data

    time_now = datetime.now()
    '''
    The following code was deleting all batch data in BQ which exists after the start of streaming.
    This has the negative side effect of truncating the batch data  to the earliest stream ever run, 
    which affects our ability to run streams in the future with matching batch data. This was done
    to prepare for the streamed transactions to be appended to the batch table, but we haven't 
    implemented that yet so, for now, this section is being commented out. 
    
    In the future we should either add the streamed data into a separate table or perhaps periodically
    merge the streamed transactions into the batch table, such that streamed txes override any batch 
    txes in an overlapping time frame. This design choice should be based on how a real world enterprise
    would manage historical and new transactions.

    time_nowplus30 = time_now + timedelta(seconds=30)
    time_nowplus30_str = time_nowplus30.strftime("%Y-%m-%d %H:%M:%S")
    sockprint(socket, time_nowplus30_str)

    bq_dataset_tx = config["bq_dataset_tx"]
    sql = f"""
        #should complete within 30 sec
        CREATE OR REPLACE TEMP TABLE todelete AS (
            SELECT TX_ID FROM `{PROJECT}.{bq_dataset_tx}.tx`
            WHERE TX_TS >= "{time_nowplus30_str}"
        );

        DELETE `{PROJECT}.{bq_dataset_tx}.tx`
        WHERE TX_ID IN (SELECT TX_ID FROM todelete);

        DELETE `{PROJECT}.{bq_dataset_tx}.txlabels`
        WHERE TX_ID IN (SELECT TX_ID FROM todelete);
    """
    # send to BigQuery to delete future rows that will be replaced by streaming data
    bq_query(sql)

    if time_nowplus30 >= datetime.now():
        seconds_to_wait = (time_nowplus30 - datetime.now()).total_seconds()
        sockprint(socket, f"Waiting for {seconds_to_wait} seconds...")
        time.sleep(seconds_to_wait)
        sockprint(socket, "...Done waiting")
'''

    i = 0
    while True:
        if not Continue:
            time.sleep(1)
            continue
        start_time = time.time()
        limit = config["stream_limit"]

        if i >= limit:
            sockprint(socket, f"stream limit {limit} reached")
            sys.exit()
        if i == 0 or (i % config["refresh_config_cycle"]) == 0:
            sockprint(socket, f"\n--- new refresh_config_cycle i = {i} ---")
            config = load_json_from_gcs(
                PROJECT, f"{GCS_DATAGEN_BUCKET_NAME}", f"{PREFIX}/config.json"
            )
            if not config:
                continue
        if i == 0 or (i % config["refresh_hack_cycle"]) == 0:
            sockprint(socket, f"\n--- new refresh_hack_cycle i = {i} ---")
            lengthcheck_cust = len(hacked_customers_history.keys())
            hacked_customers_history = update_hacked(
                hacked_customers_history,
                datetime.today(),
                cust_id_list,
                config["cust_tohack_perc"],
                config["cust_hacked_days_mean"],
                config["cust_hacked_days_std"],
            )

            if len(hacked_customers_history.keys()) - lengthcheck_cust != 0:
                # if size of dict has changed, then upload to GCS
                fname_cust = "hacked_customers_history.txt"
                with open("data/" + fname_cust, "w") as f:
                    json.dump(hacked_customers_history, f)
                uploadfile_gcs(
                    localfilepath="data/" + fname_cust,
                    destfilepath=fname_cust,
                    dest_bucket=GCS_DATAGEN_BUCKET_NAME,
                )

            lengthcheck_term = len(hacked_terminals_history.keys())
            hacked_terminals_history = update_hacked(
                hacked_terminals_history,
                datetime.today(),
                term_idlist,
                config["term_tohack_perc"],
                config["term_hacked_days_mean"],
                config["term_hacked_days_std"],
            )

            if len(hacked_terminals_history.keys()) - lengthcheck_term != 0:
                # if size of dict has changed, then upload to GCS
                fname_term = "hacked_terminals_history.txt"
                with open("data/" + fname_term, "w") as f:
                    json.dump(hacked_terminals_history, f)
                uploadfile_gcs(
                    localfilepath="data/" + fname_term,
                    destfilepath=fname_term,
                    dest_bucket=GCS_DATAGEN_BUCKET_NAME,
                )
            
            #keep list of today's hacked customers in-memory (to help determine which cid should generate CNP fraud)
            todays_hacked_customers = hacked_customers_history.get(datetime.today().strftime("%Y-%m-%d"), {})

        sockprint(socket, f"tx generated: {num_tx_generated}")

        for cid, hackdiceroll in zip(
            random.choices(
                population=cust_id_list,
                weights=cust_nb_mean_tx_per_day_list,
                k=config["tx_per_second"],
            ),
            (random.random() for i in range(config["tx_per_second"])),
        ):
            start_time = time.time()
            now_dt = datetime.now()
            curr_date_str = now_dt.strftime("%Y-%m-%d")
            tx_datetime = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            tx = gen_tx(
                cid,
                curr_date_str=curr_date_str,
                tx_datetime=tx_datetime,
                hackdiceroll=hackdiceroll,
                hacked_customers_history=hacked_customers_history,
                hacked_terminals_history=hacked_terminals_history,
                cust_terminals_dict=cust_terminals_dict,
                cust_mean_amount_dict=cust_mean_amount_dict,
                cust_std_amount_dict=cust_std_amount_dict,
                hack_txamount_prob=config["hack_txamount_prob"],
                hack_txamount_multiplier_mean=config["hack_txamount_multiplier_mean"],
                hack_txamount_multiplier_std=config["hack_txamount_multiplier_std"],
                inflation_rate=config["inflation_rate"],
                tx_hacked_cardnotpresent=False,
            )

            print(tx)
            num_tx_generated += 1
            publisher = pubsub_v1.PublisherClient()

            ## TODO: Create Pub/Sub topic

            # Publish tx only (no label of if it's fraud or not fraud)
            # filter tx dictionary to only the values needed for a tx
            txmsg = {
                k: tx[k]
                for k in [
                    "TX_ID",
                    "TX_TS",
                    "CUSTOMER_ID",
                    "TERMINAL_ID",
                    "TX_AMOUNT",
                    "CARDPRESENT_HACKED",
                    "CARDNOTPRESENT_HACKED",
                    "TERMINAL_HACKED",
                    "TX_FRAUD",
                ]
            }
            socket.emit("tx", {"data": txmsg})
            sendpubsubmessage_tx(data=txmsg, project_id=PROJECT, topic=PUBSUB_TOPIC)

            # check if customer is hacked, generate backlog of tx to generate in the near future
            if cid in todays_hacked_customers.get(cid, []):
                if random.random() <= config["cardnotpresent_hack_probability"]:
                    # generate queue of card-not-present tx
                    nb_tx = np.random.poisson(config["cardnotpresent_numfraudtx_mean"])
                    start_time_tx = random.randint(0, 86399)
                    end_time_tx = int(
                        60
                        * np.random.normal(
                            config["cardnotpresent_duration_minutes_mean"],
                            config["cardnotpresent_duration_minutes_std"],
                        )
                    )
                    end_time_tx = ( #recalc if end_time_tx is negative
                        start_time_tx + end_time_tx
                        if end_time_tx >= 0
                        else start_time_tx
                        + random.randint(1, 2 * 60 * config["cardnotpresent_duration_minutes_mean"])
                    )

                    #add to queue CNP fraudulent transactions
                    for txtime in [random.randint(start_time_tx, end_time_tx) for i in range(nb_tx)]:
                        tx_datetime_cnp = datetime.fromtimestamp(now_dt.timestamp() + txtime).strftime("%Y-%m-%d %H:%M:%S")

                        tx = gen_tx(
                                cid,
                                curr_date_str=curr_date_str,
                                tx_datetime=tx_datetime_cnp,
                                hackdiceroll=hackdiceroll,
                                hacked_customers_history=hacked_customers_history,
                                hacked_terminals_history=hacked_terminals_history,
                                cust_terminals_dict=cust_terminals_dict,
                                cust_mean_amount_dict=cust_mean_amount_dict,
                                cust_std_amount_dict=cust_std_amount_dict,
                                hack_txamount_prob=config["hack_txamount_prob"],
                                hack_txamount_multiplier_mean=config["hack_txamount_multiplier_mean"],
                                hack_txamount_multiplier_std=config["hack_txamount_multiplier_std"],
                                inflation_rate=config["inflation_rate"],
                                tx_hacked_cardnotpresent=True,
                            )
                        
                        txmsg = {
                            k: tx[k]
                            for k in [
                                "TX_ID",
                                "TX_TS",
                                "CUSTOMER_ID",
                                "TERMINAL_ID",
                                "TX_AMOUNT",
                                "CARDPRESENT_HACKED",
                                "CARDNOTPRESENT_HACKED",
                                "TERMINAL_HACKED",
                                "TX_FRAUD",
                            ]
                        }

                        queue_cardnotpresent_tx[tx_datetime_cnp] = queue_cardnotpresent_tx.get(tx_datetime_cnp, []) + [txmsg]

            # pop from queue any cardnotpresent_tx that have exceeded current time
            curr_ts = datetime.strptime(tx_datetime, "%Y-%m-%d %H:%M:%S")
            keys_to_pop_from_queue = [tx_datetime 
                                        for tx_datetime in queue_cardnotpresent_tx.keys() 
                                        if datetime.strptime(tx_datetime, "%Y-%m-%d %H:%M:%S") <= curr_ts
                                        ]
            for tx_datetime_to_pop in keys_to_pop_from_queue:
                popped = queue_cardnotpresent_tx.pop(tx_datetime_to_pop, [])
                for txmsg in popped:
                    #transmit the card-not-present fraud
                    print(txmsg)
                    num_tx_generated += 1
                    socket.emit("tx", {"data": txmsg})
                    sendpubsubmessage_tx(data=txmsg, project_id=PROJECT, topic=PUBSUB_TOPIC)
                    

            end_time = time.time()

            if (end_time - start_time) < (1 / config["tx_per_second"]):
                time.sleep((1 / config["tx_per_second"]) - (end_time - start_time))

        i += 1
    return "Done."
