def get_list_terminals_within_radius(
    customer_profile, x_y_terminals, r, terminal_id_list
):
    """
    function to return list of terminals within input radius of customer
    """
    import numpy as np

    # Use numpy arrays in the following to speed up computations

    # Location (x,y) of customer as numpy array
    x_y_customer = customer_profile[["x_loc_customer_id", "y_loc_customer_id"]].values.astype(
        float
    )

    # Squared difference in coordinates between customer and terminal locations
    squared_diff_x_y = np.square(x_y_customer - x_y_terminals)

    # Sum along rows and compute suared root to get distance
    dist_x_y = np.sqrt(np.sum(squared_diff_x_y, axis=1))

    # Filter list of terminals within distance of r
    terminal_id_array = np.array(terminal_id_list)
    dist_filter = list(dist_x_y < r)

    tid_list = list(terminal_id_array[dist_filter])
    return tid_list


def generate_customerterminal_profiles(
    customer_profiles_table, terminal_profiles_table, radius, save_directory
):
    """
    function to combine customer profiles and terminal profiles and generate customer-terminal profiles,
    returns a dataframe with one row per customer and associated terminals
    """
    import time
    import numpy as np
    import pandas as pd
    from pandarallel import pandarallel

    pandarallel.initialize()

    start_time = time.time()

    terminal_id_list = list(terminal_profiles_table["TERMINAL_ID"].values)
    x_y_terminals = terminal_profiles_table[
        ["x_terminal_id", "y_terminal_id"]
    ].values.astype(float)

    # "find and save all terminals within a given distance from each customer"
    # With Pandarallel
    customer_profiles_table[
        "available_terminals"
    ] = customer_profiles_table.parallel_apply(
        lambda x: get_list_terminals_within_radius(
            x, x_y_terminals=x_y_terminals, r=radius, terminal_id_list=terminal_id_list
        ),
        axis=1,
    )
    customer_profiles_table[
        "nb_terminals"
        # mco - I prefer "num" over "nb" as I find it more inituitive
    ] = customer_profiles_table.available_terminals.apply(len)

    print(
        "[generate_customerterminal_profiles] --Time to associate terminals to customers: {0:.2}s".format(
            time.time() - start_time
        )
    )
    #     print(f"--Distribution of # of terminals per customer: \n{customer_profiles_table.apply(lambda x : len(x['available_terminals']), axis=1).describe()}")
    print(
        f"[generate_customerterminal_profiles] --Count of customers with zero terminals: {len(customer_profiles_table[customer_profiles_table.available_terminals.astype(str) == '[]'])}"
    )

    # Write to CSV
    fp_customerterminal_profiles = (
        f"{save_directory}/customer_with_terminal_profiles.csv"
    )
    customer_profiles_table.to_csv(fp_customerterminal_profiles, index=False)
    print(
        f"[generate_customerterminal_profiles] Saved to: {fp_customerterminal_profiles}"
    )

    return customer_profiles_table
