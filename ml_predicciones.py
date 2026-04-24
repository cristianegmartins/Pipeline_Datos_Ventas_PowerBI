# =============================================================
# WINEDATA · MACHINE LEARNING
# Script: ml_predicciones.py
# Descripción: Entrena un modelo Random Forest para predecir
#              ventas mensuales por producto y segmento.
#              Guarda las predicciones en winedata_dw.
# =============================================================

import pandas as pd
import mysql.connector
from mysql.connector import Error
import warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from datetime import datetime

# -------------------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------------------
DW_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "winedata_dw",
    "user":     "etl_user",
    "password": "WineData2024!",
}

# -------------------------------------------------------------
# 1. EXTRAER DATOS DEL DW
# -------------------------------------------------------------

def extraer_datos(conn):
    """Extrae y cruza hechos_ventas con dimensiones."""
    print("  Extrayendo datos del Data Warehouse...")

    query = """
        SELECT
            h.id_hecho,
            h.cantidad,
            h.importe_neto,
            h.margen,
            c.anio,
            c.mes,
            c.trimestre,
            c.temporada,
            p.codigo_producto,
            p.nombre_producto,
            p.tipo_vino,
            p.categoria,
            cl.segmento
        FROM hechos_ventas h
        JOIN dim_calendario c  ON h.id_fecha    = c.id_fecha
        JOIN dim_producto   p  ON h.id_producto = p.id_producto
        JOIN dim_cliente    cl ON h.id_cliente  = cl.id_cliente
    """
    df = pd.read_sql(query, conn)
    print(f"  ✓ {len(df):,} registros extraídos\n")
    return df


# -------------------------------------------------------------
# 2. PREPARAR DATOS PARA ML
# -------------------------------------------------------------

def preparar_datos(df):
    """Agrupa por mes, producto y segmento para obtener ventas mensuales."""
    print("  Preparando datos para entrenamiento...")

    # Agrupar por mes, producto y segmento
    datos = df.groupby(
        ["anio", "mes", "trimestre", "temporada", "codigo_producto",
         "nombre_producto", "tipo_vino", "categoria", "segmento"]
    ).agg(
        total_cantidad  = ("cantidad",    "sum"),
        total_importe   = ("importe_neto","sum"),
        total_margen    = ("margen",      "sum"),
        num_pedidos     = ("id_hecho",    "count")
    ).reset_index()

    # Codificar variables categóricas con one-hot encoding
    datos_encoded = pd.get_dummies(
        datos,
        columns=["temporada", "codigo_producto", "tipo_vino", "categoria", "segmento"],
        drop_first=False
    )

    print(f"  ✓ {len(datos):,} filas agrupadas por mes/producto/segmento")
    return datos, datos_encoded


# -------------------------------------------------------------
# 3. ENTRENAR MODELO
# -------------------------------------------------------------

def entrenar_modelo(datos, datos_encoded):
    """Entrena Random Forest con datos 2022-2024 y valida con 2025."""
    print("\n  Entrenando modelo Random Forest...")

    # Variables de entrada (features)
    feature_cols = [c for c in datos_encoded.columns if c not in [
        "nombre_producto", "total_cantidad", "total_importe", "total_margen", "num_pedidos"
    ]]

    # Variable objetivo
    target = "total_cantidad"

    # Split: entrenamiento 2022-2024, validación 2025
    train = datos_encoded[datos_encoded["anio"] < 2025]
    test  = datos_encoded[datos_encoded["anio"] == 2025]

    X_train = train[feature_cols]
    y_train = train[target]
    X_test  = test[feature_cols]
    y_test  = test[target]

    # Entrenar modelo
    modelo = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    modelo.fit(X_train, y_train)

    # Métricas de validación
    y_pred = modelo.predict(X_test)
    mae    = mean_absolute_error(y_test, y_pred)
    r2     = r2_score(y_test, y_pred)

    print(f"  ✓ Modelo entrenado")
    print(f"    MAE  (error medio absoluto) : {mae:.1f} botellas")
    print(f"    R²   (precisión del modelo) : {r2:.3f}  (1.0 = perfecto)")

    return modelo, feature_cols


# -------------------------------------------------------------
# 4. GENERAR PREDICCIONES 2026
# -------------------------------------------------------------

def generar_predicciones(datos, datos_encoded, modelo, feature_cols):
    """Genera predicciones mensuales para 2026 por producto y segmento."""
    print("\n  Generando predicciones para 2026...")

    # Obtener combinaciones únicas de producto + segmento
    combos = datos[["codigo_producto", "nombre_producto", "tipo_vino",
                    "categoria", "segmento"]].drop_duplicates()

    temporadas = {
        1:"Temporada Baja", 2:"Temporada Baja", 3:"Semana Santa",
        4:"Semana Santa",   5:"Temporada Media",6:"Temporada Alta",
        7:"Temporada Alta", 8:"Temporada Alta", 9:"Temporada Media",
        10:"Temporada Media",11:"Temporada Baja",12:"Temporada Baja"
    }
    trimestres = {1:1,2:1,3:1,4:2,5:2,6:2,7:3,8:3,9:3,10:4,11:4,12:4}

    filas_pred = []
    for mes in range(1, 13):
        for _, combo in combos.iterrows():
            filas_pred.append({
                "anio":             2026,
                "mes":              mes,
                "trimestre":        trimestres[mes],
                "temporada":        temporadas[mes],
                "codigo_producto":  combo["codigo_producto"],
                "nombre_producto":  combo["nombre_producto"],
                "tipo_vino":        combo["tipo_vino"],
                "categoria":        combo["categoria"],
                "segmento":         combo["segmento"],
            })

    df_pred = pd.DataFrame(filas_pred)

    # Aplicar mismo encoding que los datos de entrenamiento
    df_pred_encoded = pd.get_dummies(
        df_pred,
        columns=["temporada", "codigo_producto", "tipo_vino", "categoria", "segmento"],
        drop_first=False
    )

    # Alinear columnas con las del modelo
    for col in feature_cols:
        if col not in df_pred_encoded.columns:
            df_pred_encoded[col] = 0
    df_pred_encoded = df_pred_encoded[feature_cols]

    # Predecir
    predicciones = modelo.predict(df_pred_encoded)
    df_pred["cantidad_predicha"] = predicciones.round(0).astype(int).clip(min=0)

    # Estimar importe predicho usando precio medio histórico por producto/segmento
    precio_medio = datos.groupby(
        ["codigo_producto", "segmento"]
    )["total_importe"].sum() / datos.groupby(
        ["codigo_producto", "segmento"]
    )["total_cantidad"].sum()
    precio_medio = precio_medio.reset_index().rename(columns={0: "precio_medio"})

    df_pred = df_pred.merge(precio_medio, on=["codigo_producto", "segmento"], how="left")
    df_pred["importe_predicho"] = (
        df_pred["cantidad_predicha"] * df_pred["precio_medio"]
    ).round(2)

    print(f"  ✓ {len(df_pred)} predicciones generadas (12 meses × {len(combos)} combinaciones)")
    return df_pred


# -------------------------------------------------------------
# 5. CREAR TABLA Y GUARDAR PREDICCIONES EN EL DW
# -------------------------------------------------------------

def crear_tabla_predicciones(conn):
    """Crea la tabla predicciones_ventas en winedata_dw."""
    cursor = conn.cursor()
    cursor.execute("""
        DROP TABLE IF EXISTS predicciones_ventas;
    """)
    cursor.execute("""
        CREATE TABLE predicciones_ventas (
            id_prediccion       INT AUTO_INCREMENT PRIMARY KEY,
            anio                INT,
            mes                 INT,
            trimestre           INT,
            temporada           VARCHAR(30),
            codigo_producto     VARCHAR(20),
            nombre_producto     VARCHAR(100),
            tipo_vino           VARCHAR(50),
            categoria           VARCHAR(20),
            segmento            VARCHAR(20),
            cantidad_predicha   INT,
            importe_predicho    DECIMAL(12,2),
            fecha_generacion    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) COMMENT 'Predicciones de ventas 2026 generadas por Random Forest';
    """)
    conn.commit()
    cursor.close()
    print("  ✓ Tabla predicciones_ventas creada en winedata_dw")


def guardar_predicciones(conn, df_pred):
    """Guarda las predicciones en la tabla del DW."""
    cols = ["anio", "mes", "trimestre", "temporada", "codigo_producto",
            "nombre_producto", "tipo_vino", "categoria", "segmento",
            "cantidad_predicha", "importe_predicho"]

    df_guardar = df_pred[cols].where(pd.notna(df_pred[cols]), None)
    datos = [tuple(row) for row in df_guardar.itertuples(index=False, name=None)]

    placeholders = ", ".join(["%s"] * len(cols))
    columnas     = ", ".join(cols)
    sql = f"INSERT INTO predicciones_ventas ({columnas}) VALUES ({placeholders})"

    cursor = conn.cursor()
    cursor.executemany(sql, datos)
    conn.commit()
    cursor.close()
    print(f"  ✓ {len(datos)} predicciones guardadas en winedata_dw\n")


# -------------------------------------------------------------
# 6. RESUMEN DE PREDICCIONES
# -------------------------------------------------------------

def mostrar_resumen(df_pred):
    """Muestra un resumen de las predicciones generadas."""
    print("=" * 55)
    print("RESUMEN PREDICCIONES 2026")
    print("=" * 55)

    resumen = df_pred.groupby("nombre_producto").agg(
        botellas_predichas = ("cantidad_predicha", "sum"),
        importe_predicho   = ("importe_predicho",  "sum")
    ).sort_values("botellas_predichas", ascending=False)

    for prod, row in resumen.iterrows():
        print(f"  {prod:<30} {int(row['botellas_predichas']):>6} bot · {row['importe_predicho']:>10,.0f} EUR")

    print("-" * 55)
    print(f"  {'TOTAL':<30} {int(resumen['botellas_predichas'].sum()):>6} bot · "
          f"{resumen['importe_predicho'].sum():>10,.0f} EUR")
    print("=" * 55)


# -------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# -------------------------------------------------------------

if __name__ == "__main__":
    inicio = datetime.now()
    print("=" * 55)
    print("WINEDATA · Machine Learning · Predicciones 2026")
    print(f"Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55 + "\n")

    # Conectar
    conn = mysql.connector.connect(**DW_CONFIG)
    print("  ✓ Conectado a winedata_dw\n")

    # Pipeline ML
    print("EXTRACCIÓN")
    df_raw = extraer_datos(conn)

    print("PREPARACIÓN")
    datos, datos_encoded = preparar_datos(df_raw)

    print("ENTRENAMIENTO")
    modelo, feature_cols = entrenar_modelo(datos, datos_encoded)

    print("PREDICCIÓN")
    df_pred = generar_predicciones(datos, datos_encoded, modelo, feature_cols)

    print("CARGA EN DATA WAREHOUSE")
    crear_tabla_predicciones(conn)
    guardar_predicciones(conn, df_pred)

    mostrar_resumen(df_pred)

    conn.close()
    fin = datetime.now()
    duracion = (fin - inicio).seconds
    print(f"\nTiempo de ejecución : {duracion} segundos")
    print(f"Fin: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✓ Predicciones listas para conectar en Power BI.")
