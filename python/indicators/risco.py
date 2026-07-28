def calcular_risco(df):
    if df.empty:
        return df
    df = df.copy()
    df["risco"] = df.get("valor", 0) * 1.5
    return df
