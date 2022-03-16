def generate_terminal_profiles_table(n_terminals, save_directory, random_state=0):
    """
    function to generate terminal profiles and return as dataframe
    """
    import numpy as np
    import pandas as pd
    import time
    from helperfxns.fxns import hashid

    start_time = time.time()

    np.random.seed(random_state)

    terminal_id_properties = []

    # Generate terminal properties from random distributions
    for terminal_id in range(n_terminals):

        x_terminal_id = np.random.uniform(0, 100)
        y_terminal_id = np.random.uniform(0, 100)

        terminal_id_properties.append([terminal_id, x_terminal_id, y_terminal_id])

    terminal_profiles_table = pd.DataFrame(
        terminal_id_properties,
        columns=["TERMINAL_ID", "x_terminal_id", "y_terminal_id"],
    )

    terminal_profiles_table["TERMINAL_ID"] = terminal_profiles_table[
        "TERMINAL_ID"
    ].apply(lambda x: hashid(x, 8))

    print(
        "[generate_terminal_profiles_table] Time to generate terminal profiles table: {0:.2}s".format(
            time.time() - start_time
        )
    )
    # Write to CSV
    fp_terminal_profiles = f"{save_directory}/terminal_profiles.csv"
    terminal_profiles_table.to_csv(fp_terminal_profiles, index=False)
    print(f"[generate_terminal_profiles_table] Saved to: {fp_terminal_profiles}")

    return terminal_profiles_table
