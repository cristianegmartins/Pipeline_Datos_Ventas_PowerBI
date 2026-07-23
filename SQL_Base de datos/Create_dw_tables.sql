-- =============================================================
-- WINEDATA · DATA WAREHOUSE
-- Script: 04_create_dw_tables.sql
-- Descripción: Crea la base de datos winedata_dw y las 5
--              tablas del modelo Star Schema:
--              4 dimensiones + 1 tabla de hechos central.
-- =============================================================

-- -------------------------------------------------------------
-- Crear base de datos
-- -------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS winedata_dw
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE winedata_dw;

-- Permisos para el usuario ETL
GRANT ALL PRIVILEGES ON winedata_dw.* TO 'etl_user'@'localhost';

-- Permisos de solo lectura para Power BI
-- (ejecutar cuando se cree el usuario de Power BI)
-- GRANT SELECT ON winedata_dw.* TO 'powerbi_user'@'localhost';

FLUSH PRIVILEGES;


-- =============================================================
-- DIMENSIONES
-- =============================================================

-- -------------------------------------------------------------
-- dim_cliente
-- Origen: stg_customer (T18)
-- -------------------------------------------------------------
DROP TABLE IF EXISTS dim_cliente;
CREATE TABLE dim_cliente (
    id_cliente          INT             NOT NULL AUTO_INCREMENT,
    codigo_cliente      VARCHAR(20)     NOT NULL,
    nombre              VARCHAR(100),
    ciudad              VARCHAR(50),
    provincia           VARCHAR(50),
    codigo_postal       VARCHAR(10),
    pais                VARCHAR(5),
    tipo_cliente        VARCHAR(20),
    segmento            VARCHAR(20),
    PRIMARY KEY (id_cliente),
    UNIQUE KEY uq_codigo_cliente (codigo_cliente)
) COMMENT 'Dimensión de clientes · restaurantes, vinotecas, supermercados';


-- -------------------------------------------------------------
-- dim_producto
-- Origen: stg_item (T27) + stg_item_category (T5722)
-- -------------------------------------------------------------
DROP TABLE IF EXISTS dim_producto;
CREATE TABLE dim_producto (
    id_producto         INT             NOT NULL AUTO_INCREMENT,
    codigo_producto     VARCHAR(20)     NOT NULL,
    nombre_producto     VARCHAR(100),
    categoria           VARCHAR(20),
    descripcion_cat     VARCHAR(100),
    tipo_vino           VARCHAR(50),
    subzona             VARCHAR(50),
    volumen_cl          INT,
    precio_base         DECIMAL(10,2),
    coste_base          DECIMAL(10,2),
    PRIMARY KEY (id_producto),
    UNIQUE KEY uq_codigo_producto (codigo_producto)
) COMMENT 'Dimensión de productos · vinos Seganfredo';


-- -------------------------------------------------------------
-- dim_vendedor
-- Origen: stg_salesperson (T13)
-- -------------------------------------------------------------
DROP TABLE IF EXISTS dim_vendedor;
CREATE TABLE dim_vendedor (
    id_vendedor         INT             NOT NULL AUTO_INCREMENT,
    codigo_vendedor     VARCHAR(10)     NOT NULL,
    nombre_vendedor     VARCHAR(100),
    departamento        VARCHAR(50),
    region              VARCHAR(50),
    PRIMARY KEY (id_vendedor),
    UNIQUE KEY uq_codigo_vendedor (codigo_vendedor)
) COMMENT 'Dimensión de vendedores · equipo comercial';


-- -------------------------------------------------------------
-- dim_calendario
-- Generada automáticamente por el ETL para 2022-2025
-- -------------------------------------------------------------
DROP TABLE IF EXISTS dim_calendario;
CREATE TABLE dim_calendario (
    id_fecha            INT             NOT NULL,
    fecha               DATE            NOT NULL,
    anio                INT,
    trimestre           INT,
    mes                 INT,
    nombre_mes          VARCHAR(20),
    semana              INT,
    dia                 INT,
    nombre_dia          VARCHAR(20),
    es_fin_semana       TINYINT(1),
    temporada           VARCHAR(20),
    PRIMARY KEY (id_fecha),
    UNIQUE KEY uq_fecha (fecha)
) COMMENT 'Dimensión calendario 2022-2025 · con estacionalidad Rías Baixas';


-- =============================================================
-- TABLA DE HECHOS
-- =============================================================

-- -------------------------------------------------------------
-- hechos_ventas
-- Origen: stg_sales_invoice_line (T113) + cabeceras
-- Tabla central del Star Schema
-- -------------------------------------------------------------
DROP TABLE IF EXISTS hechos_ventas;
CREATE TABLE hechos_ventas (
    id_hecho            INT             NOT NULL AUTO_INCREMENT,

    -- Claves foráneas a dimensiones
    id_cliente          INT             NOT NULL,
    id_producto         INT             NOT NULL,
    id_vendedor         INT             NOT NULL,
    id_fecha            INT             NOT NULL,

    -- Identificadores de trazabilidad (origen ERP)
    num_factura         VARCHAR(20),
    num_albaran         VARCHAR(20),
    linea_factura       INT,

    -- Métricas de venta
    cantidad            INT,
    precio_unitario     DECIMAL(10,2),
    descuento_pct       DECIMAL(5,2),
    importe_bruto       DECIMAL(12,2),
    importe_neto        DECIMAL(12,2),
    iva_pct             DECIMAL(5,2),
    importe_con_iva     DECIMAL(12,2),

    -- Métricas de coste y rentabilidad
    coste_unitario      DECIMAL(10,2),
    coste_total         DECIMAL(12,2),
    margen              DECIMAL(12,2),
    margen_pct          DECIMAL(7,4),

    PRIMARY KEY (id_hecho),
    CONSTRAINT fk_cliente   FOREIGN KEY (id_cliente)  REFERENCES dim_cliente(id_cliente),
    CONSTRAINT fk_producto  FOREIGN KEY (id_producto) REFERENCES dim_producto(id_producto),
    CONSTRAINT fk_vendedor  FOREIGN KEY (id_vendedor) REFERENCES dim_vendedor(id_vendedor),
    CONSTRAINT fk_fecha     FOREIGN KEY (id_fecha)    REFERENCES dim_calendario(id_fecha),
    INDEX idx_fecha     (id_fecha),
    INDEX idx_cliente   (id_cliente),
    INDEX idx_producto  (id_producto),
    INDEX idx_vendedor  (id_vendedor)
) COMMENT 'Tabla de hechos central · ventas 2022-2025 Bodega Seganfredo';


-- =============================================================
-- Verificación: listar tablas creadas
-- =============================================================
SELECT
    table_name      AS tabla,
    table_comment   AS descripcion
FROM information_schema.tables
WHERE table_schema = 'winedata_dw'
ORDER BY table_name;
