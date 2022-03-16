import pickle
from re import I

jobs = []


def batch_stop():
    global jobs
    print("\n\nStopping batch generation\n\n")
    for job in jobs:
        job.terminate()


def gen_day(
    curr_date_str,
    config,
    hacked_customers_history,
    hacked_terminals_history,
    save_directory,
):
    """
    for a given date, curr_date_str,
    generate n number of transactions where n is config["tx_per_day"]
    """
    import random
    from datetime import datetime, timedelta
    from helperfxns.fxns import gen_tx_amount, gen_tx_id, gen_tx
    import numpy as np
    import time

    print("start gen_day for", curr_date_str)

    curr_date_epoch = datetime.strptime(curr_date_str, "%Y-%m-%d").timestamp()
    custdata = pickle.load(open("custdata.p", "rb"))

    f = open(f"{save_directory}/daily/{curr_date_str}.txt", "w")
    tx_per_day = config["tx_per_day"]

    for cid, txtime, hackdiceroll in zip(
        random.choices(
            population=custdata["cust_ids_list"],
            weights=custdata["cust_weights_list"],
            k=tx_per_day,
        ),
        (random.randint(0, 86399) for i in range(tx_per_day)),
        (random.random() for i in range(tx_per_day)),
    ):
        tx_datetime = datetime.fromtimestamp(curr_date_epoch + txtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        tx = gen_tx(
            cid,
            curr_date_str,
            tx_datetime,
            hackdiceroll,
            hacked_customers_history,
            hacked_terminals_history,
            custdata["cust_terminals_dict"],
            custdata["cust_mean_amount_dict"],
            custdata["cust_std_amount_dict"],
            config["hack_txamount_prob"],
            config["hack_txamount_multiplier_mean"],
            config["hack_txamount_multiplier_std"],
            config["inflation_rate"],
        )
        tx_str = ",".join([str(val) for val in tx.values()])
        f.write(tx_str + "\n")

    # get list of hacked customers for current date
    curr_hackedcustlist = hacked_customers_history.get(curr_date_str, {}).keys()

    # generate card-not-present fraud tx for a subset of customers determined by a probability check
    for cid in (
        cid
        for cid in curr_hackedcustlist
        if random.random() <= config["cardnotpresent_hack_probability"]
    ):
        nb_tx = np.random.poisson(config["cardnotpresent_numfraudtx_mean"])

        # set start time and end_time
        start_time_tx = random.randint(0, 86399)
        end_time_tx = int(
            60
            * np.random.normal(
                config["cardnotpresent_duration_minutes_mean"],
                config["cardnotpresent_duration_minutes_std"],
            )
        )
        end_time_tx = (
            start_time_tx + end_time_tx
            if end_time_tx >= 0
            else start_time_tx
            + random.randint(1, 2 * 60 * config["cardnotpresent_duration_minutes_mean"])
        )

        

        for txtime in [random.randint(start_time_tx, end_time_tx) for i in range(nb_tx)]:
            tx_datetime = datetime.fromtimestamp(curr_date_epoch + txtime).strftime(
            "%Y-%m-%d %H:%M:%S"
            )
            # generate tx
            tx = gen_tx(
                cid,
                curr_date_str,
                tx_datetime,
                hackdiceroll,
                hacked_customers_history,
                hacked_terminals_history,
                custdata["cust_terminals_dict"],
                custdata["cust_mean_amount_dict"],
                custdata["cust_std_amount_dict"],
                config["hack_txamount_prob"],
                config["hack_txamount_multiplier_mean"],
                config["hack_txamount_multiplier_std"],
                config["inflation_rate"],
                tx_hacked_cardnotpresent=1,
            )
            tx_str = ",".join([str(val) for val in tx.values()])
            f.write(tx_str + "\n")
    print("done gen_day for", curr_date_str)


def generate_transactions_table(
    datelist,
    customerterminal_profiles_table,
    hacked_customers_history,
    hacked_terminals_history,
    config,
    save_directory,
):
    """
    generates transactions between start_date
    saves result to CSV
    """
    import multiprocessing
    import random
    import time
    import os
    import re
    import shutil

    print(f"[generate_transactions_table] Starting...")
    start_time = time.time()

    cust_ids_list = list(customerterminal_profiles_table["CUSTOMER_ID"].values)
    cust_weights_list = list(
        customerterminal_profiles_table["mean_num_tx_per_day"].values
    )
    custdf = customerterminal_profiles_table.set_index("CUSTOMER_ID")
    cust_terminals_dict = custdf["available_terminals"].to_dict()
    cust_mean_amount_dict = custdf["mean_amount"].to_dict()
    cust_std_amount_dict = custdf["std_amount"].to_dict()

    custdata = {
        "cust_ids_list": cust_ids_list,
        "cust_weights_list": cust_weights_list,
        "cust_terminals_dict": cust_terminals_dict,
        "cust_mean_amount_dict": cust_mean_amount_dict,
        "cust_std_amount_dict": cust_std_amount_dict,
    }
    pickle.dump(custdata, open("custdata.p", "wb"))

    # Create data directory if doesn't exist
    if not os.path.exists(save_directory + "/daily"):
        os.makedirs(save_directory + "/daily")

    # Multiprocess generation of tx
    global jobs
    jobs.clear()
    for date_str in datelist:

        job = multiprocessing.Process(
            target=gen_day,
            args=(
                date_str,
                config,
                hacked_customers_history,
                hacked_terminals_history,
                save_directory,
            ),
        )
        print(f"Starting process for {date_str}")
        job.start()
        jobs.append(job)

    for job in jobs:
        job.join()

    time_datageneration = time.time()
    print(
        f"[generate_transactions_table] data generation completed: {round(time_datageneration - start_time,2)}s elapsed"
    )

    ## Uncomment to merge into a single file
    # Merge all files by date
    destination = open(f"{save_directory}/tx/tx.csv", "wb")
    header = ",".join(
        [
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
    )
    destination.write((header + "\n").encode("utf-8"))
    for curr_date in datelist:
        pattern = f"{curr_date}\\.txt"
        x = [f for f in os.listdir(f"{save_directory}/daily") if re.match(pattern, f)]
        if len(x) > 0:
            for f in x:
                shutil.copyfileobj(
                    open(f"{save_directory}/daily/{f}", "rb"), destination
                )
    destination.close()
    print(
        f"[generate_transactions_table] Merge files completed: {round(time.time() - time_datageneration,2)}s elapsed"
    )

    return f"{save_directory}/tx/tx.csv"
