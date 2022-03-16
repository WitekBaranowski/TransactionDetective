def generate_customer_profiles_table(n_customers, save_directory, random_state=0):
    """
    function to generate customer profiles and return as dataframe
    """
    import numpy as np
    import pandas as pd
    import time
    from helperfxns.fxns import hashid
    
    start_time = time.time()
    np.random.seed(random_state)

    #set parameters
    MEAN_AMOUNT_RANGE = (5,100) #min-max range of mean tx amount for customer
    MEAN_NUM_TX_PER_DAY_RANGE = (0,4) #min-max range of mean number of tx per day for customer


    customer_id_properties = []

    #Generate customer properties from random distributions
    for customer_id in range(n_customers):
        # as function call args or constant variables.
        x_loc_customer_id = np.random.uniform(0, 100)
        y_loc_customer_id = np.random.uniform(0, 100)

        mean_amount = np.random.uniform(MEAN_AMOUNT_RANGE[0],
                                        MEAN_AMOUNT_RANGE[1]) 
        std_amount = np.sqrt(mean_amount)

        mean_num_tx_per_day = np.random.uniform(MEAN_NUM_TX_PER_DAY_RANGE[0],
                                                MEAN_NUM_TX_PER_DAY_RANGE[1])

        customer_id_properties.append(
            [
                customer_id,
                x_loc_customer_id,
                y_loc_customer_id,
                mean_amount,
                std_amount,
                mean_num_tx_per_day,
            ]
        )
    customer_profiles_table = pd.DataFrame(
        customer_id_properties,
        columns=[
        "CUSTOMER_ID",
        "x_loc_customer_id",
        "y_loc_customer_id",
            "mean_amount",
            "std_amount",
            "mean_num_tx_per_day",
        ],
    )
    
    # MEAN_AMOUNT_RANGE = (5,100) #min-max range of mean tx amount for customer
    # MEAN_NUM_TX_PER_DAY_RANGE = (0,4) #min-max range of mean number of tx per day for customer

    # customer_id = range(n_customers)
    # # x_loc_customer_id = rng.choice((10**16), size=n_customers, replace=False)/(10**14)
    # # y_loc_customer_id = rng.choice((10**16), size=n_customers, replace=False)/(10**14)
    # x_loc_customer_id = [np.random.uniform(0,100) for _ in range(n_customers)]
    # y_loc_customer_id = [np.random.uniform(0,100) for _ in range(n_customers)]
    # mean_amount = [np.random.uniform(MEAN_AMOUNT_RANGE[0], MEAN_AMOUNT_RANGE[1]) for _ in range(n_customers)]
    # std_amount = [np.sqrt(x) for x in mean_amount]
    # mean_num_tx_per_day = [np.random.uniform(MEAN_NUM_TX_PER_DAY_RANGE[0], [MEAN_NUM_TX_PER_DAY_RANGE[1]]) for _ in range(n_customers)]

    # customer_profiles_table = pd.DataFrame(list(zip(customer_id,
    #                                                 x_loc_customer_id,
    #                                                 y_loc_customer_id,
    #                                                 mean_amount,
    #                                                 std_amount,
    #                                                 mean_num_tx_per_day
    #                                                 )),
    #                                         columns =["CUSTOMER_ID", 
    #                                                 "x_loc_customer_id",
    #                                                 "y_loc_customer_id",
    #                                                 "mean_amount",
    #                                                 "std_amount",
    #                                                 "mean_num_tx_per_day"])
  

    # converts CUSTOMER_ID into a 16-digit unique id
    customer_profiles_table["CUSTOMER_ID"] = customer_profiles_table[
        "CUSTOMER_ID"
    ].apply(lambda x: hashid(x, 16))

    # convert mean num transactions per day to transactions per second
    customer_profiles_table["mean_num_tx_per_sec"] = customer_profiles_table[
        "mean_num_tx_per_day"
    ] / (24 * 60 * 60)

    fp_customer_profiles = f"{save_directory}/customer_profiles.csv"
    customer_profiles_table.to_csv(fp_customer_profiles, index=False)
    print(f"[generate_customer_profiles_table] Saved to: {fp_customer_profiles}")
    
    print(
        "[generate_customer_profiles_table] Time to generate customer profiles table: {0:.2}s".format(
            time.time() - start_time
        )
    )

    return customer_profiles_table
