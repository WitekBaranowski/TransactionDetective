def generate_hacked_dict(
    id_list,
    target,
    start_date,
    end_date,
    perc_to_hack,
    hacked_days_mean,
    hacked_days_std,
    save_directory,
):
    """
    INPUT:
    id_list: list of customer/terminal ids
    target: "customers" or "terminals" as a string
    start_date: string ("YYYY-MM-DD") for the first day of hacked customers/terminals
    # mco - can this be some null value, indicating "always hacked"?
    end_date: string ("YYYY-MM-DD") for the last day of hacked customers/terminals
    # mco - can this be some null value, indicating "hacked forever"?
    perc_to_hack: percentage chance to hack customer/terminal
    # mco - expressing this as a probability rather than a percentage might be simpler (in which case this var should be called prob_to_hack)
    hacked_days_mean: average hack duration, in days
    hacked_days_std: std hack duration, in days

    OUTPUT:
    a dictionary with keys as a specific date, and value as a dict containing as its keys and values:
        key=CUSTOMER_ID/TERMINAL_ID and value=date that the customer should no longer be hacked
    """
    import random
    import numpy as np
    import json
    from datetime import datetime, timedelta
    from helperfxns.fxns import add_hacked, remove_hacked, update_hacked

    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

    hacked_dict_all = {}
    hacked_dict_current = {}

    curr_date_dt = start_date_dt - timedelta(
        days = 2 * hacked_days_mean
    )  # start a bit before to warm start, as # of hacked terms/custs require some days to ramp and stablize

    while curr_date_dt <= end_date_dt:
        hacked_dict_current = add_hacked(
            hacked_dict_current,
            id_list=id_list,
            current_date=curr_date_dt,
            perc_to_hack=perc_to_hack,
            hacked_days_mean=hacked_days_mean,
            hacked_days_std=hacked_days_std,
        )
        hacked_dict_current = remove_hacked(
            hacked_dict_current, current_date=curr_date_dt
        )

        if curr_date_dt >= start_date_dt:
            # only add to hacked_dict_all after warm start
            hacked_dict_all[curr_date_dt.strftime("%Y-%m-%d")] = hacked_dict_current

        curr_date_dt += timedelta(days=1)

    print(
        f"[generate_hacked_dict] Number {target} hacked on final day: {len(hacked_dict_current.keys())}"
    )

    # Write to file
    fp_hacked = f"{save_directory}/hacked_{target}_history.txt"
    with open(fp_hacked, "w") as f:
        json.dump(hacked_dict_all, f)
    print(f"[generate_hacked_dict] Saved to: {fp_hacked}")

    return hacked_dict_all
