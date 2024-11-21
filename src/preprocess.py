import pandas as pd

def preprocess_excel(file_path):
    df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")

    df["Tier"] = df["Tier"].fillna(method="ffill")
    df["M&M"] = df["M&M"].fillna(method="ffill")
    meaningful_columns = ["Tier", "Description", "Data type", "Allowed values", "Cardinality/Required?"]
    df = df[meaningful_columns].dropna(how="all")

    return df
