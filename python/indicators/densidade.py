def calcular_densidade(df):
    if df.empty:
        return df
    df = df.copy()
    df["densidade"] = df.get("valor", 0) / max(1, len(df))
    return df
