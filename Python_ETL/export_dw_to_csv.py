# =============================================================
# WINEDATA · Export DW to CSV
# Script: export_dw_to_csv.py
# Descripción: Exporta las 5 tablas del Data Warehouse a CSV
#              para cargar en Power BI sin conector MySQL.
# =============================================================

import pandas as pd
import mysql.connector
import os

DW_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "winedata_dw",
    "user":     "etl_user",
    "password": "WineData2024!",
}

OUTPUT_FOLDER = r"C:\Winedata\powerbi_csv"

TABLAS = [
    "dim_calendario",
    "dim_cliente",
    "dim_producto",
    "dim_vendedor",
    "hechos_ventas",
]

if __name__ == "__main__":
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    conn = mysql.connector.connect(**DW_CONFIG)
    print("✓ Conectado a winedata_dw\n")

    for tabla in TABLAS:
        df = pd.read_sql(f"SELECT * FROM {tabla}", conn)
        ruta = os.path.join(OUTPUT_FOLDER, f"{tabla}.csv")
        df.to_csv(ruta, index=False, encoding="utf-8-sig")
        print(f"  ✓ {tabla:<25} {len(df):>6} filas → {ruta}")

    conn.close()
    print("\n✓ CSV listos en C:\\Winedata\\powerbi_csv")
