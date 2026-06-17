import numpy as np
import pandas as pd
from pandas import json_normalize


def json_to_dataframe(data, column_mapping):
    df = json_normalize(data)

    df_selected = pd.DataFrame()

    for col_name, json_path in column_mapping.items():
        if json_path in df.columns:
            df_selected[col_name] = df[json_path]
        else:
            df_selected[col_name] = np.nan

    return df_selected
