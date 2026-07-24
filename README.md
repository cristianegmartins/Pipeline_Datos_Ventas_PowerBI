PROYECTO WINEDATA ** prueba - [Dashboard Power BI](Power BI_Cuadro de Mando/Winedata.pbix)

WineData es un proyecto de analítica de datos end-to-end desarrollado como Proyecto Fin de Ciclo del Grado Superior en Desarrollo de Aplicaciones Web (DAW).
Simula el sistema de inteligencia de negocio de una bodega gallega ficticia, cubriendo todo el pipeline de datos: desde la extracción de datos de venta de un ERP (Microsoft Business Central),
pasando por un proceso ETL en Python, un Data Warehouse con arquitectura Star Schema en MySQL, hasta un dashboard interactivo en Power BI con predicciones de ventas mediante Machine Learning (Random Forest · scikit-learn). 

Proyecto presentado en mayo/2026 | Calificación: 90/100.

---------------------------
HERRAMIENTAS Y TECNOLOGÍAS

· Python · pandas · scikit-learn 
· MySQL · MariaDB · XAMPP
· Power BI · Microsoft Fabric
· ETL · Star Schema · Data Warehouse
· Machine Learning · Random Forest
· Git · GitHub · MySQL Workbench · VS Code
· Scrum · Trello

---------------------------
PROCESO ETL

El proceso ETL se divide en tres fases:

1. Extracción
Los datos (ficticios) se obtienen desde archivos CSV proporcionados por el ERP Microsoft Business Central, seguindo el padrón del ERP (Datos primarios), utilizado en la bodega.
El script (SQL_Base de datos/create_staging_tables.sql) carga estos datos en una base de datos temporal.

2. Transformación
El script (Phyton_ETL/etl_winedata.py) realiza:
· Limpieza de datos.
· Conversión de tipos.
· Normalización de campos.
· Unión entre tablas.
· Cálculo de métricas necesarias para el DW.

3. Carga
Los datos transformados se insertan en las tablas del Data Warehouse (SQL_Base de datos/Create_dw_tables.sql).

---------------------------
DATA WAREHOUSE (DW)

El DW está diseñado siguiendo un enfoque **estrella (star schema)**, con:

· **Tablas de hechos**: ventas, envíos, líneas de factura.
· **Tablas de dimensiones**: clientes, productos, categorías, comerciales, fechas.

El script SQL principal incluye:
· Creación de tablas
· Relaciones
· Índices
· Inserción de datos transformados

---------------------------
PREDICCIONES CON MACHINE LEARNING

El archivo (Phyton_ETL/ml_predicciones.py) implementa un modelo de predicción basado en scikit-learn.

Incluye:
· Preparación del dataset
· División train/test
· Entrenamiento del modelo
· Evaluación
· Generación de predicciones finales

Las predicciones se integran posteriormente en Power BI para visualización.

---------------------------
VISUALIZACIÓN EN POWER BI

El proyecto incluye capturas del dashboard final, donde se muestran:
· Tendencias de ventas
· Predicciones generadas por el modelo ML
· Análisis por cliente, producto y categoría

Visualización del cuadro de mando: (Power BI_Cuadro de Mando/Winedata.pbix)

---------------------------
REQUISITOS

Python
· Python 3.10+
· pandas
· numpy
· scikit-learn
· mysql-connector-python

Base de datos
· MySQL / MariaDB
· XAMPP (como servidor local)
· MySQL Workbench (gestión visual)

Conector
·MySQL Connector/NET 8.0.28 (específico para compatibilidad con Power BI y MariaDB vía XAMPP)

Visualización
· Power BI Desktop
· Microsoft Fabric (publicación del dashboard)

Control de versiones
· Git
· GitHub

Entorno de desarrollo
· VS Code

Gestión del proyecto
· Trello

---------------------------
FLUJO DEL PROYECTO

ERP (BC) → Staging Area → ETL → Data Warehouse → Machine Learning → Power BI 

* El ML va después del Data Warehouse porque el modelo se alimenta de los datos ya limpios y transformados que están en winedata_dw.
Las predicciones generadas se guardan de vuelta en el DW en la tabla predicciones_ventas, antes de llegar a Power BI.
