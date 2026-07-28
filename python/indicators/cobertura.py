def calcular_cobertura(df):
    if df.empty:
        return df
    df = df.copy()
    df["cobertura"] = df.get("valor", 0) * 0.8
    return df
