# =============================================================
# WINEDATA · STAGING AREA
# Script: load_staging.py
# Descripción: Carga los 8 CSV exportados desde Business
#              Central en las tablas staging de MySQL.
#              Política: truncate and load (borra y recarga).
# =============================================================

import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# -------------------------------------------------------------
# CONFIGURACIÓN — cambia estos valores por los tuyos
# -------------------------------------------------------------
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "winedata_staging",
    "user":     "etl_user",
    "password": "WineData2024!",
}

# Carpeta donde están los CSV (usa la ruta completa si es necesario)
# Ejemplo Windows: r"C:\Users\TuNombre\Desktop\winedata_csv"
CSV_FOLDER = r"C:\Winedata\winedata_csv"

# Mapa: tabla staging → nombre del archivo CSV
TABLAS = {
    "stg_customer":               "T18_Customer.csv",
    "stg_salesperson":            "T13_Salesperson_Purchaser.csv",
    "stg_item":                   "T27_Item.csv",
    "stg_item_category":          "T5722_Item_Category.csv",
    "stg_sales_invoice_header":   "T112_Sales_Invoice_Header.csv",
    "stg_sales_invoice_line":     "T113_Sales_Invoice_Line.csv",
    "stg_sales_shipment_header":  "T110_Sales_Shipment_Header.csv",
    "stg_sales_shipment_line":    "T111_Sales_Shipment_Line.csv",
}

# Columnas de fecha por tabla (para conversión correcta)
FECHAS = {
    "stg_sales_invoice_header":  ["Posting_Date", "Document_Date", "Due_Date"],
    "stg_sales_invoice_line":    ["Posting_Date"],
    "stg_sales_shipment_header": ["Posting_Date", "Shipment_Date"],
    "stg_sales_shipment_line":   ["Posting_Date"],
}


# -------------------------------------------------------------
# FUNCIONES
# -------------------------------------------------------------

def conectar():
    """Crea y devuelve la conexión a MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print(f"✓ Conectado a MySQL — base de datos: {DB_CONFIG['database']}\n")
            return conn
    except Error as e:
        print(f"✗ Error de conexión: {e}")
        raise


def truncar_tabla(cursor, tabla):
    """Borra todos los datos de la tabla antes de recargar."""
    cursor.execute(f"TRUNCATE TABLE {tabla};")


def cargar_csv(conn, tabla, fichero):
    """Lee el CSV, convierte fechas y carga en la tabla staging."""
    ruta = os.path.join(CSV_FOLDER, fichero)

    if not os.path.exists(ruta):
        print(f"  ✗ Archivo no encontrado: {ruta}")
        return 0

    # Leer CSV
    df = pd.read_csv(ruta, encoding="utf-8")

    # Convertir columnas de fecha a formato MySQL (YYYY-MM-DD)
    for col in FECHAS.get(tabla, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
            df[col] = df[col].where(df[col].notna(), None)

    # Reemplazar NaN por None (MySQL NULL)
    df = df.where(pd.notna(df), None)

    cursor = conn.cursor()

    # Truncar antes de cargar
    truncar_tabla(cursor, tabla)

    # Construir INSERT dinámico
    columnas = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    sql = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"

    # Insertar por lotes de 500 filas
    datos = [tuple(fila) for fila in df.itertuples(index=False, name=None)]
    batch_size = 500
    for i in range(0, len(datos), batch_size):
        cursor.executemany(sql, datos[i:i + batch_size])

    conn.commit()
    cursor.close()
    return len(df)


def verificar_carga(conn):
    """Muestra el recuento de filas de cada tabla staging."""
    print("\n" + "=" * 50)
    print("VERIFICACIÓN DE CARGA")
    print("=" * 50)
    cursor = conn.cursor()
    for tabla in TABLAS.keys():
        cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
        filas = cursor.fetchone()[0]
        print(f"  {tabla:<35} {filas:>6} filas")
    cursor.close()
    print("=" * 50)


# -------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# -------------------------------------------------------------

if __name__ == "__main__":
    inicio = datetime.now()
    print("=" * 50)
    print("WINEDATA · Carga Staging Area")
    print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50 + "\n")

    conn = conectar()
    total_filas = 0

    for tabla, fichero in TABLAS.items():
        print(f"  Cargando {tabla}...")
        filas = cargar_csv(conn, tabla, fichero)
        print(f"  ✓ {filas} filas cargadas\n")
        total_filas += filas

    verificar_carga(conn)
    conn.close()

    fin = datetime.now()
    duracion = (fin - inicio).seconds
    print(f"\nTotal filas cargadas : {total_filas}")
    print(f"Tiempo de ejecución  : {duracion} segundos")
    print(f"Fin: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✓ Staging Area cargada correctamente.")
