from google.cloud import storage
import sys
import os
import time
import pandas as pd
import numpy as np
import json
import math
from datetime import datetime, timedelta
from batch.gen_customer_profiles import generate_customer_profiles_table
from batch.gen_terminal_profiles import generate_terminal_profiles_table
from batch.gen_customerterminal_profiles import generate_customerterminal_profiles
from batch.gen_transactions import generate_transactions_table
from batch.gen_hacked_customerterminals import generate_hacked_dict
from helperfxns.fxns import load_json_from_gcs, uploadfile_gcs, transfer_gcstobq

# Create data directory if doesn't exist
SAVE_DIRECTORY = "data"
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)
if not os.path.exists(SAVE_DIRECTORY + "/tx"):
    os.makedirs(SAVE_DIRECTORY + "/tx")


# defaults

PROJECT = "fraudfinderdemo"
BUCKET = PROJECT
PREFIX = "datagen"


def batch(PROJECT, socket):
    print("Starting batch()...")

    start_time = time.time()

    config = load_json_from_gcs(PROJECT, BUCKET, f"{PREFIX}/config.json")

    nb_days = (
        datetime.strptime(config["end_date"], "%Y-%m-%d")
        - datetime.strptime(config["start_date"], "%Y-%m-%d")
    ).days + 1

    ## Generate CUSTOMER PROFILES and save file
    customer_profiles_table = generate_customer_profiles_table(
        config["num_customers"], SAVE_DIRECTORY
    )

    ## Generate TERMINAL PROFILES and save file
    terminal_profiles_table = generate_terminal_profiles_table(
        config["num_terminals"], SAVE_DIRECTORY
    )

    ## Generate CUSTOMER-TERMINAL PROFILES and save file
    customerterminal_profiles_table = generate_customerterminal_profiles(
        customer_profiles_table,
        terminal_profiles_table,
        config["radius"],
        SAVE_DIRECTORY,
    )

    ## Generate dictionary of hacked customers between START_DATE and END_DATE and save file
    hacked_customers_history = generate_hacked_dict(
        id_list=list(customer_profiles_table["CUSTOMER_ID"].values),
        target="customers",
        start_date=config["start_date"],
        end_date=config["end_date"],
        perc_to_hack=config["cust_tohack_perc"],
        hacked_days_mean=config["cust_hacked_days_mean"],
        hacked_days_std=config["cust_hacked_days_std"],
        save_directory=SAVE_DIRECTORY,
    )

    ## Generate dictionary of hacked terminals between START_DATE and END_DATE and save file
    hacked_terminals_history = generate_hacked_dict(
        id_list=list(terminal_profiles_table["TERMINAL_ID"].values),
        target="terminals",
        start_date=config["start_date"],
        end_date=config["end_date"],
        perc_to_hack=config["term_tohack_perc"],
        hacked_days_mean=config["term_hacked_days_mean"],
        hacked_days_std=config["term_hacked_days_std"],
        save_directory=SAVE_DIRECTORY,
    )

    ## Generate historical transactions between START_DATE and END_DATE and save file
    datelist = [
        (
            datetime.strptime(config["start_date"], "%Y-%m-%d") + timedelta(days=i)
        ).strftime("%Y-%m-%d")
        for i in range(nb_days)
    ]

    fp_tx_csv = generate_transactions_table(
        datelist,
        customerterminal_profiles_table,
        hacked_customers_history,
        hacked_terminals_history,
        config,
        SAVE_DIRECTORY,
    )

    ## Split CSV into two CSV files
    fp_tx_only = f"{SAVE_DIRECTORY}/tx/tx_only.csv"
    pd.read_csv(
        fp_tx_csv,
        dtype={"CUSTOMER_ID": object, "TERMINAL_ID": object},
        usecols=["TX_ID", "TX_TS", "CUSTOMER_ID", "TERMINAL_ID", "TX_AMOUNT"],
    ).sort_values("TX_TS").to_csv(fp_tx_only, index=False)

    fp_tx_labels = f"{SAVE_DIRECTORY}/tx/tx_labels.csv"
    pd.read_csv(
        fp_tx_csv,
        dtype={"CUSTOMER_ID": object, "TERMINAL_ID": object},
        usecols=[
            "TX_ID",
            "TX_TS",
            "CARDPRESENT_HACKED",
            "CARDNOTPRESENT_HACKED",
            "TERMINAL_HACKED",
            "TX_FRAUD",
        ],
    ).sort_values("TX_TS").drop("TX_TS", 1).to_csv(fp_tx_labels, index=False)

    ## Upload hacked customer/terminal files to GCS

    uri_hacked_customers_history = uploadfile_gcs(
        localfilepath=f"{SAVE_DIRECTORY}/hacked_customers_history.txt",
        destfilepath=f"{PREFIX}/hacked_customers_history.txt",
        dest_bucket=BUCKET,
        # mco - suggest setting this once to one comment bucket and use path to distinguish between datagen, demographics, etc.
    )

    uri_hacked_terminals_history = uploadfile_gcs(
        localfilepath=f"{SAVE_DIRECTORY}/hacked_terminals_history.txt",
        destfilepath=f"{PREFIX}/hacked_terminals_history.txt",
        dest_bucket=BUCKET,
    )

    ## Upload demographic files to GCS

    uri_customerprofiles = uploadfile_gcs(
        localfilepath=f"{SAVE_DIRECTORY}/customer_profiles.csv",
        destfilepath=f"{PREFIX}/demographics/customer_profiles.csv",
        dest_bucket=BUCKET,
    )

    uri_terminalprofiles = uploadfile_gcs(
        localfilepath=f"{SAVE_DIRECTORY}/terminal_profiles.csv",
        destfilepath=f"{PREFIX}/demographics/terminal_profiles.csv",
        dest_bucket=BUCKET,
    )

    uri_customerterminalprofiles = uploadfile_gcs(
        localfilepath=f"{SAVE_DIRECTORY}/customer_with_terminal_profiles.csv",
        destfilepath=f"{PREFIX}/demographics/customer_with_terminal_profiles.csv",
        dest_bucket=BUCKET,
    )

    ## Upload local tx files to GCS

    uri_tx_only = uploadfile_gcs(
        localfilepath=fp_tx_only,
        destfilepath=f"{PREFIX}/tx/tx_only.csv",
        dest_bucket=BUCKET,
    )

    uri_tx_labels = uploadfile_gcs(
        localfilepath=fp_tx_labels,
        destfilepath=f"{PREFIX}/tx/tx_labels.csv",
        dest_bucket=BUCKET,
    )

    ## Transfer GCS to BigQuery

    ### to BQ table: tx
    schemadict_tx_only = {
        "TX_ID": "STRING",
        "TX_TS": "TIMESTAMP",
        "CUSTOMER_ID": "STRING",
        "TERMINAL_ID": "STRING",
        "TX_AMOUNT": "NUMERIC",
    }
    transfer_gcstobq(
        gs_uri=f"gs://{BUCKET}/{PREFIX}/tx/tx_only.csv",  # uri_tx_only,
        schemadict=schemadict_tx_only,
        bq_dataset_id=config["bq_dataset_tx"],
        bq_table_id="tx",
        project_id=PROJECT,
        partition_field="TX_TS",
    )

    ### to BQ table: txfraud
    schemadict_tx_labels = {
        "TX_ID": "STRING",
        "CARDPRESENT_HACKED": "INT64",
        "CARDNOTPRESENT_HACKED": "INT64",
        "TERMINAL_HACKED": "INT64",
        "TX_FRAUD": "INT64",
    }

    transfer_gcstobq(
        gs_uri=f"gs://{PROJECT}/{PREFIX}/tx/tx_labels.csv",  # uri_tx_labels,
        schemadict=schemadict_tx_labels,
        bq_dataset_id=config["bq_dataset_tx"],
        bq_table_id="txlabels",
        project_id=PROJECT,
    )

    ### to BQ table: demographics

    #### customers
    schemadict_customers = {
        "CUSTOMER_ID": "STRING",
        "x_customer_id": "FLOAT64",
        "y_customer_id": "FLOAT64",
        "mean_amount": "FLOAT64",
        "std_amount": "FLOAT64",
        "mean_nb_tx_per_day": "FLOAT64",
        "mean_nb_tx_per_sec": "FLOAT64",
    }

    transfer_gcstobq(
        gs_uri=f"gs://{BUCKET}/{PREFIX}/demographics/customer_profiles.csv",  # uri_tx_labels,
        schemadict=schemadict_customers,
        bq_dataset_id="demographics",
        bq_table_id="customers",
        project_id=PROJECT,
    )

    #### terminals
    schemadict_terminals = {
        "TERMINAL_ID": "STRING",
        "x_terminal_id": "FLOAT64",
        "y_terminal__id": "FLOAT64",
    }

    transfer_gcstobq(
        gs_uri=f"gs://{BUCKET}/{PREFIX}/demographics/terminal_profiles.csv",  # uri_tx_labels,
        schemadict=schemadict_terminals,
        bq_dataset_id="demographics",
        bq_table_id="terminals",
        project_id=PROJECT,
    )

    #### customer-terminals
    schemadict_customersterminals = {
        "CUSTOMER_ID": "STRING",
        "x_customer_id": "FLOAT64",
        "y_customer_id": "FLOAT64",
        "mean_amount": "FLOAT64",
        "std_amount": "FLOAT64",
        "mean_nb_tx_per_day": "FLOAT64",
        "mean_nb_tx_per_sec": "FLOAT64",
        "available_terminals": "STRING",
        "nb_terminals": "INT64",
    }

    transfer_gcstobq(
        gs_uri=f"gs://{PROJECT}/{PREFIX}/demographics/customer_with_terminal_profiles.csv",  # uri_tx_labels,
        schemadict=schemadict_customersterminals,
        bq_dataset_id="demographics",
        bq_table_id="customersterminals",
        project_id=PROJECT,
    )

    print(
        f"-----------------------Done {np.round(time.time()-start_time,1)}s elapsed-----------------------"
    )
    return "Done."


if __name__ == "__main__":
    batch()
