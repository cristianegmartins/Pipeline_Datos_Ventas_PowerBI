-- =============================================================
-- WINEDATA · STAGING AREA
-- Script: 02_create_staging_tables.sql
-- Descripción: Crea las 8 tablas de staging replicando las
--              columnas de los CSV exportados desde Business
--              Central. Datos en crudo, sin transformaciones.
-- =============================================================

USE winedata_staging;

-- -------------------------------------------------------------
-- T18 · Customer
-- -------------------------------------------------------------
DROP TABLE IF EXISTS stg_customer;
CREATE TABLE stg_customer (
    No_                    VARCHAR(20),
    Name                   VARCHAR(100),
    City                   VARCHAR(50),
    County                 VARCHAR(50),
    Post_Code              VARCHAR(10),
    Country_Region_Code    VARCHAR(5),
    Customer_Posting_Group VARCHAR(20),
    Salesperson_Code       VARCHAR(10),
    Segment                VARCHAR(20),
    _loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- T13 · Salesperson / Purchaser
-- -------------------------------------------------------------
DROP TABLE IF EXISTS stg_salesperson;
CREATE TABLE stg_salesperson (
    Code                   VARCHAR(10),
    Name                   VARCHAR(100),
    Department             VARCHAR(50),
    Region                 VARCHAR(50),
    _loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- T27 · Item (Productos)
-- -------------------------------------------------------------
DROP TABLE IF EXISTS stg_item;
CREATE TABLE stg_item (
    No_                    VARCHAR(20),
    Description            VARCHAR(100),
    Item_Category_Code     VARCHAR(20),
    Base_Unit_of_Measure   VARCHAR(10),
    Unit_Price             DECIMAL(10,2),
    Unit_Cost              DECIMAL(10,2),
    Tipo_Vino              VARCHAR(50),
    Subzona                VARCHAR(50),
    Volumen_cl             INT,
    _loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- T5722 · Item Category
-- -------------------------------------------------------------
DROP TABLE IF EXISTS stg_item_category;
CREATE TABLE stg_item_category (
    Code                   VARCHAR(20),
    Description            VARCHAR(100),
    _loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- T112 · Sales Invoice Header
-- -------------------------------------------------------------
DROP TABLE IF EXISTS stg_sales_invoice_header;
CREATE TABLE stg_sales_invoice_header (
    No_                          VARCHAR(20),
    Sell_to_Customer_No_         VARCHAR(20),
    Sell_to_Customer_Name        VARCHAR(100),
    Sell_to_City                 VARCHAR(50),
    Sell_to_Post_Code            VARCHAR(10),
    Sell_to_Country_Region_Code  VARCHAR(5),
    Bill_to_Customer_No_         VARCHAR(20),
    Posting_Date                 DATE,
    Document_Date                DATE,
    Due_Date                     DATE,
    Salesperson_Code             VARCHAR(10),
    Amount                       DECIMAL(12,2),
    Amount_Including_VAT         DECIMAL(12,2),
    Currency_Code                VARCHAR(5),
    Status                       VARCHAR(20),
    _loaded_at                   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- T113 · Sales Invoice Line
-- -------------------------------------------------------------
DROP TABLE IF EXISTS stg_sales_invoice_line;
CREATE TABLE stg_sales_invoice_line (
    Document_No_           VARCHAR(20),
    Line_No_               INT,
    Sell_to_Customer_No_   VARCHAR(20),
    Type                   VARCHAR(20),
    No_                    VARCHAR(20),
    Description            VARCHAR(100),
    Quantity               INT,
    Unit_of_Measure_Code   VARCHAR(10),
    Unit_Price             DECIMAL(10,2),
    Line_Discount_Pct      DECIMAL(5,2),
    Line_Amount            DECIMAL(12,2),
    Unit_Cost_LCY          DECIMAL(10,2),
    Line_Cost              DECIMAL(12,2),
    VAT_Pct                DECIMAL(5,2),
    Amount_Including_VAT   DECIMAL(12,2),
    Posting_Date           DATE,
    Salesperson_Code       VARCHAR(10),
    _loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- T110 · Sales Shipment Header
-- -------------------------------------------------------------
DROP TABLE IF EXISTS stg_sales_shipment_header;
CREATE TABLE stg_sales_shipment_header (
    No_                          VARCHAR(20),
    Sell_to_Customer_No_         VARCHAR(20),
    Sell_to_Customer_Name        VARCHAR(100),
    Posting_Date                 DATE,
    Shipment_Date                DATE,
    Salesperson_Code             VARCHAR(10),
    Ship_to_City                 VARCHAR(50),
    Ship_to_Post_Code            VARCHAR(10),
    Ship_to_Country_Region_Code  VARCHAR(5),
    _loaded_at                   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- T111 · Sales Shipment Line
-- -------------------------------------------------------------
DROP TABLE IF EXISTS stg_sales_shipment_line;
CREATE TABLE stg_sales_shipment_line (
    Document_No_           VARCHAR(20),
    Line_No_               INT,
    Sell_to_Customer_No_   VARCHAR(20),
    No_                    VARCHAR(20),
    Description            VARCHAR(100),
    Quantity               INT,
    Unit_of_Measure_Code   VARCHAR(10),
    Qty_Invoiced           INT,
    Posting_Date           DATE,
    _loaded_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Verificación: contar tablas creadas
-- -------------------------------------------------------------
SELECT table_name, table_rows
FROM information_schema.tables
WHERE table_schema = 'winedata_staging'
ORDER BY table_name;
