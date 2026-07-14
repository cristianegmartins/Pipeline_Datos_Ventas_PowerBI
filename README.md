🍷 Proyecto WineData — ETL, Data Warehouse y Predicciones de Ventas

Este proyecto implementa un flujo completo de creación de un Staging Area, ETL (Extracción, Transformación y Carga), 
la creación de un Data Warehouse (DW) y un módulo de Machine Learning para generar predicciones basadas en datos de ventas 
de una bodega ficticia, llamada SEGANFREDO.

El objetivo es construir una arquitectura analítica que permita:
- Centralizar datos de ventas procedentes del ERP Microsoft Business Central.
- Transformarlos y limpiarlos para análisis.
- Crear un Data Warehouse optimizado.
- Generar predicciones mediante modelos de Machine Learning.
- Visualizar resultados en herramientas como Power BI.


---

 🚀 1. Proceso ETL

El proceso ETL se divide en tres fases:

🔹 Extracción
Los datos se obtienen desde archivos CSV proporcionados por el ERP Microsoft Business Central, utilizado en la bodega.  
El script `load_staging.py` carga estos datos en una base de datos temporal (staging).

🔹 Transformación
El script `etl_winedata.py` realiza:
- Limpieza de datos
- Conversión de tipos
- Normalización de campos
- Unión entre tablas
- Cálculo de métricas necesarias para el DW

🔹 Carga
Los datos transformados se insertan en las tablas del Data Warehouse.

---

🏛️ 2. Data Warehouse (DW)

El DW está diseñado siguiendo un enfoque **estrella (star schema)**, con:

- **Tablas de hechos**: ventas, envíos, líneas de factura.
- **Tablas de dimensiones**: clientes, productos, categorías, comerciales, fechas.

El script SQL principal incluye:
- Creación de tablas
- Relaciones
- Índices
- Inserción de datos transformados

🤖 3. Predicciones con Machine Learning

El archivo `ml_predicciones.py` implementa un modelo de predicción basado en scikit-learn.

Incluye:
- Preparación del dataset
- División train/test
- Entrenamiento del modelo
- Evaluación
- Generación de predicciones finales

Las predicciones se integran posteriormente en Power BI para visualización.

📊 4. Visualización en Power BI

El proyecto incluye capturas del dashboard final, donde se muestran:
- Tendencias de ventas
- Predicciones generadas por el modelo ML
- Análisis por cliente, producto y categoría

---
🛠️ 5. Requisitos

Python
- Python 3.10+
- pandas
- numpy
- scikit-learn
- sqlalchemy
- mysql-connector-python (o el driver que uses)

Base de datos
- MySQL / MariaDB
  
6. Cómo ejecutar el proyecto
1. Cargar datos en staging
2. Ejecutar el ETL
3. Entrenar y generar predicciones

Autor: Cristiane G. Martins
Analista de Datos | Business Inteligence 
Proyecto académico y profesional para análisis de datos de venta de bodega | Calificación 9,0 | Junio 2026
DAW | CESUR
