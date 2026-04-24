# =============================================================
# WINEDATA · ETL PIPELINE
# Script: etl_winedata.py
# Descripción: Extrae datos de winedata_staging, transforma
#              y carga el modelo Star Schema en winedata_dw.
# Orden de carga: dim_calendario → dim_cliente → dim_producto
#                 → dim_vendedor → hechos_ventas
# =============================================================

import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import date, timedelta
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------------------
STG_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "winedata_staging",
    "user":     "etl_user",
    "password": "WineData2024!",
}

DW_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "winedata_dw",
    "user":     "etl_user",
    "password": "WineData2024!",
}


# -------------------------------------------------------------
# HELPERS DE CONEXIÓN
# -------------------------------------------------------------

def conectar(config):
    """Abre y devuelve una conexión MySQL."""
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"  ✗ Error de conexión a {config['database']}: {e}")
        raise


def leer_tabla(conn, tabla):
    """Lee una tabla completa de MySQL y la devuelve como DataFrame."""
    return pd.read_sql(f"SELECT * FROM {tabla}", conn)


def truncar_y_cargar(conn, tabla, df, batch_size=500):
    """Trunca la tabla y carga el DataFrame por lotes."""
    cursor = conn.cursor()
    cursor.execute(f"SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute(f"TRUNCATE TABLE {tabla};")
    cursor.execute(f"SET FOREIGN_KEY_CHECKS = 1;")

    if df.empty:
        cursor.close()
        return 0

    # Reemplazar NaN por None
    df = df.where(pd.notna(df), None)

    columnas = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    sql = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"

    datos = [tuple(row) for row in df.itertuples(index=False, name=None)]
    for i in range(0, len(datos), batch_size):
        cursor.executemany(sql, datos[i:i + batch_size])

    conn.commit()
    cursor.close()
    return len(df)


# -------------------------------------------------------------
# 1. EXTRACCIÓN DESDE STAGING
# -------------------------------------------------------------

def extraer_staging(conn_stg):
    """Lee todas las tablas staging y las devuelve en un dict."""
    print("  Extrayendo datos de staging...")
    tablas = {
        "customer":          leer_tabla(conn_stg, "stg_customer"),
        "salesperson":       leer_tabla(conn_stg, "stg_salesperson"),
        "item":              leer_tabla(conn_stg, "stg_item"),
        "item_category":     leer_tabla(conn_stg, "stg_item_category"),
        "inv_header":        leer_tabla(conn_stg, "stg_sales_invoice_header"),
        "inv_line":          leer_tabla(conn_stg, "stg_sales_invoice_line"),
        "shp_header":        leer_tabla(conn_stg, "stg_sales_shipment_header"),
        "shp_line":          leer_tabla(conn_stg, "stg_sales_shipment_line"),
    }
    for nombre, df in tablas.items():
        print(f"    {nombre:<20} {len(df):>6} filas")
    return tablas


# -------------------------------------------------------------
# 2. LIMPIEZA GENERAL
# -------------------------------------------------------------

def limpiar_df(df):
    """Limpieza básica aplicable a cualquier DataFrame."""
    # Eliminar duplicados completos
    df = df.drop_duplicates()
    # Normalizar textos: strip solo en columnas string
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    # Eliminar columna de auditoría de staging si existe
    if "_loaded_at" in df.columns:
        df = df.drop(columns=["_loaded_at"])
    return df


# -------------------------------------------------------------
# 3. TRANSFORMAR dim_calendario
# -------------------------------------------------------------

def build_dim_calendario():
    """Genera una fila por día para el rango 2022-2025."""
    print("  Construyendo dim_calendario...")

    meses_es = {
        1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril",
        5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto",
        9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
    }
    dias_es = {
        0:"Lunes", 1:"Martes", 2:"Miércoles", 3:"Jueves",
        4:"Viernes", 5:"Sábado", 6:"Domingo"
    }

    def temporada(mes):
        if mes in [6, 7, 8]:
            return "Temporada Alta"
        elif mes in [3, 4]:
            return "Semana Santa"
        elif mes in [12, 1, 2]:
            return "Temporada Baja"
        else:
            return "Temporada Media"

    filas = []
    fecha_actual = date(2022, 1, 1)
    fecha_fin    = date(2025, 12, 31)

    while fecha_actual <= fecha_fin:
        filas.append({
            "id_fecha":     int(fecha_actual.strftime("%Y%m%d")),
            "fecha":        fecha_actual.isoformat(),
            "anio":         fecha_actual.year,
            "trimestre":    (fecha_actual.month - 1) // 3 + 1,
            "mes":          fecha_actual.month,
            "nombre_mes":   meses_es[fecha_actual.month],
            "semana":       fecha_actual.isocalendar()[1],
            "dia":          fecha_actual.day,
            "nombre_dia":   dias_es[fecha_actual.weekday()],
            "es_fin_semana": 1 if fecha_actual.weekday() >= 5 else 0,
            "temporada":    temporada(fecha_actual.month),
        })
        fecha_actual += timedelta(days=1)

    return pd.DataFrame(filas)


# -------------------------------------------------------------
# 4. TRANSFORMAR dim_cliente
# -------------------------------------------------------------

def build_dim_cliente(stg):
    """Construye dim_cliente desde stg_customer."""
    print("  Construyendo dim_cliente...")
    df = limpiar_df(stg["customer"].copy())

    dim = pd.DataFrame()
    dim["codigo_cliente"] = df["No_"]
    dim["nombre"]         = df["Name"].fillna("Desconocido")
    dim["ciudad"]         = df["City"].fillna("Desconocido")
    dim["provincia"]      = df["County"].fillna("Desconocido")
    dim["codigo_postal"]  = df["Post_Code"].fillna("")
    dim["pais"]           = df["Country_Region_Code"].fillna("ES")
    dim["tipo_cliente"]   = df["Customer_Posting_Group"].fillna("NACIONAL")
    dim["segmento"]       = df["Segment"].fillna("Desconocido")

    dim = dim.drop_duplicates(subset=["codigo_cliente"]).reset_index(drop=True)
    dim.insert(0, "id_cliente", range(1, len(dim) + 1))
    return dim


# -------------------------------------------------------------
# 5. TRANSFORMAR dim_producto
# -------------------------------------------------------------

def build_dim_producto(stg):
    """Construye dim_producto cruzando stg_item con stg_item_category."""
    print("  Construyendo dim_producto...")
    item = limpiar_df(stg["item"].copy())
    cat  = limpiar_df(stg["item_category"].copy())

    # Cruzar producto con categoría
    df = item.merge(
        cat.rename(columns={"Code": "Item_Category_Code", "Description": "desc_cat"}),
        on="Item_Category_Code",
        how="left"
    )

    dim = pd.DataFrame()
    dim["codigo_producto"]  = df["No_"]
    dim["nombre_producto"]  = df["Description"].fillna("Desconocido")
    dim["categoria"]        = df["Item_Category_Code"].fillna("SIN_CAT")
    dim["descripcion_cat"]  = df["desc_cat"].fillna("")
    dim["tipo_vino"]        = df["Tipo_Vino"].fillna("")
    dim["subzona"]          = df["Subzona"].fillna("")
    dim["volumen_cl"]       = pd.to_numeric(df["Volumen_cl"], errors="coerce").fillna(75).astype(int)
    dim["precio_base"]      = pd.to_numeric(df["Unit_Price"], errors="coerce").fillna(0).round(2)
    dim["coste_base"]       = pd.to_numeric(df["Unit_Cost"], errors="coerce").fillna(0).round(2)

    dim = dim.drop_duplicates(subset=["codigo_producto"]).reset_index(drop=True)
    dim.insert(0, "id_producto", range(1, len(dim) + 1))
    return dim


# -------------------------------------------------------------
# 6. TRANSFORMAR dim_vendedor
# -------------------------------------------------------------

def build_dim_vendedor(stg):
    """Construye dim_vendedor desde stg_salesperson."""
    print("  Construyendo dim_vendedor...")
    df = limpiar_df(stg["salesperson"].copy())

    dim = pd.DataFrame()
    dim["codigo_vendedor"]  = df["Code"]
    dim["nombre_vendedor"]  = df["Name"].fillna("Desconocido")
    dim["departamento"]     = df["Department"].fillna("")
    dim["region"]           = df["Region"].fillna("")

    dim = dim.drop_duplicates(subset=["codigo_vendedor"]).reset_index(drop=True)
    dim.insert(0, "id_vendedor", range(1, len(dim) + 1))
    return dim


# -------------------------------------------------------------
# 7. TRANSFORMAR hechos_ventas
# -------------------------------------------------------------

def build_hechos_ventas(stg, dim_cliente, dim_producto, dim_vendedor):
    """Construye la tabla de hechos cruzando líneas de factura con dimensiones."""
    print("  Construyendo hechos_ventas...")

    # Líneas de factura
    lines = limpiar_df(stg["inv_line"].copy())
    hdrs  = limpiar_df(stg["inv_header"].copy())

    # Convertir tipos numéricos
    for col in ["Quantity", "Unit_Price", "Line_Discount_Pct",
                "Line_Amount", "Unit_Cost_LCY", "Line_Cost",
                "VAT_Pct", "Amount_Including_VAT"]:
        lines[col] = pd.to_numeric(lines[col], errors="coerce").fillna(0)

    # Convertir fecha
    lines["Posting_Date"] = pd.to_datetime(lines["Posting_Date"], errors="coerce")

    # Calcular métricas
    lines["importe_neto"]    = (lines["Line_Amount"]).round(2)
    lines["importe_bruto"]   = (lines["Quantity"] * lines["Unit_Price"]).round(2)
    lines["coste_total"]     = (lines["Quantity"] * lines["Unit_Cost_LCY"]).round(2)
    lines["margen"]          = (lines["importe_neto"] - lines["coste_total"]).round(2)
    lines["margen_pct"]      = (
        lines["margen"] / lines["importe_neto"].replace(0, float("nan"))
    ).fillna(0).round(4)

    # id_fecha en formato YYYYMMDD
    lines["id_fecha"] = lines["Posting_Date"].dt.strftime("%Y%m%d").astype(int)

    # Cruzar con número de albarán desde cabecera de envío
    hdrs_shp = limpiar_df(stg["shp_header"].copy())[["No_", "Sell_to_Customer_No_"]]
    hdrs_shp = hdrs_shp.rename(columns={"No_": "num_albaran_ref"})

    # Mapas de dimensiones (código → id numérico)
    map_cliente  = dict(zip(dim_cliente["codigo_cliente"],  dim_cliente["id_cliente"]))
    map_producto = dict(zip(dim_producto["codigo_producto"], dim_producto["id_producto"]))
    map_vendedor = dict(zip(dim_vendedor["codigo_vendedor"], dim_vendedor["id_vendedor"]))

    # Asignar claves foráneas
    lines["id_cliente"]  = lines["Sell_to_Customer_No_"].map(map_cliente)
    lines["id_producto"] = lines["No_"].map(map_producto)
    lines["id_vendedor"] = lines["Salesperson_Code"].map(map_vendedor)

    # Eliminar filas sin clave (no deberían existir)
    lines = lines.dropna(subset=["id_cliente", "id_producto", "id_vendedor", "id_fecha"])
    lines["id_cliente"]  = lines["id_cliente"].astype(int)
    lines["id_producto"] = lines["id_producto"].astype(int)
    lines["id_vendedor"] = lines["id_vendedor"].astype(int)

    # Construir DataFrame final
    hechos = pd.DataFrame()
    hechos["id_cliente"]      = lines["id_cliente"]
    hechos["id_producto"]     = lines["id_producto"]
    hechos["id_vendedor"]     = lines["id_vendedor"]
    hechos["id_fecha"]        = lines["id_fecha"]
    hechos["num_factura"]     = lines["Document_No_"]
    hechos["num_albaran"]     = None
    hechos["linea_factura"]   = lines["Line_No_"]
    hechos["cantidad"]        = lines["Quantity"].astype(int)
    hechos["precio_unitario"] = lines["Unit_Price"].round(2)
    hechos["descuento_pct"]   = lines["Line_Discount_Pct"].round(2)
    hechos["importe_bruto"]   = lines["importe_bruto"]
    hechos["importe_neto"]    = lines["importe_neto"]
    hechos["iva_pct"]         = lines["VAT_Pct"].round(2)
    hechos["importe_con_iva"] = lines["Amount_Including_VAT"].round(2)
    hechos["coste_unitario"]  = lines["Unit_Cost_LCY"].round(2)
    hechos["coste_total"]     = lines["coste_total"]
    hechos["margen"]          = lines["margen"]
    hechos["margen_pct"]      = lines["margen_pct"]

    return hechos.reset_index(drop=True)


# -------------------------------------------------------------
# 8. VERIFICACIÓN FINAL
# -------------------------------------------------------------

def verificar_dw(conn_dw):
    """Muestra el recuento de filas de cada tabla del DW."""
    print("\n" + "=" * 55)
    print("VERIFICACIÓN DATA WAREHOUSE")
    print("=" * 55)
    tablas = [
        "dim_calendario",
        "dim_cliente",
        "dim_producto",
        "dim_vendedor",
        "hechos_ventas",
    ]
    cursor = conn_dw.cursor()
    for tabla in tablas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
        filas = cursor.fetchone()[0]
        print(f"  {tabla:<25} {filas:>6} filas")
    cursor.close()

    # Muestra de métricas clave
    print("\n  --- Métricas de muestra ---")
    cursor = conn_dw.cursor()
    cursor.execute("""
        SELECT
            SUM(cantidad)       AS total_botellas,
            SUM(importe_neto)   AS total_ventas_eur,
            SUM(margen)         AS total_margen_eur,
            ROUND(AVG(margen_pct) * 100, 1) AS margen_medio_pct
        FROM hechos_ventas;
    """)
    row = cursor.fetchone()
    if row:
        print(f"  Total botellas vendidas : {int(row[0]):>10,}")
        print(f"  Total ventas (EUR)      : {float(row[1]):>12,.2f}")
        print(f"  Total margen (EUR)      : {float(row[2]):>12,.2f}")
        print(f"  Margen medio            : {float(row[3]):>9.1f} %")
    cursor.close()
    print("=" * 55)


# -------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# -------------------------------------------------------------

if __name__ == "__main__":
    inicio = datetime.now()
    print("=" * 55)
    print("WINEDATA · ETL Pipeline")
    print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55 + "\n")

    # Conectar
    print("Conectando a bases de datos...")
    conn_stg = conectar(STG_CONFIG)
    conn_dw  = conectar(DW_CONFIG)
    print("  ✓ Staging y DW conectados\n")

    # Extraer
    print("EXTRACCIÓN")
    stg = extraer_staging(conn_stg)

    # Transformar
    print("\nTRANSFORMACIÓN")
    dim_cal  = build_dim_calendario()
    dim_cli  = build_dim_cliente(stg)
    dim_prod = build_dim_producto(stg)
    dim_vend = build_dim_vendedor(stg)
    hechos   = build_hechos_ventas(stg, dim_cli, dim_prod, dim_vend)

    # Cargar en orden (respetar foreign keys)
    print("\nCARGA EN DATA WAREHOUSE")
    tablas_carga = [
        ("dim_calendario", dim_cal),
        ("dim_cliente",    dim_cli),
        ("dim_producto",   dim_prod),
        ("dim_vendedor",   dim_vend),
        ("hechos_ventas",  hechos),
    ]
    for nombre, df in tablas_carga:
        n = truncar_y_cargar(conn_dw, nombre, df)
        print(f"  ✓ {nombre:<25} {n:>6} filas cargadas")

    # Verificar
    verificar_dw(conn_dw)

    # Cerrar conexiones
    conn_stg.close()
    conn_dw.close()

    fin = datetime.now()
    duracion = (fin - inicio).seconds
    print(f"\nTiempo de ejecución : {duracion} segundos")
    print(f"Fin: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✓ Data Warehouse cargado y listo para Power BI.")
