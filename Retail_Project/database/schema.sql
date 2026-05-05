-- ============================================================================
-- Retail Data Warehouse — Star Schema (MySQL 8+)
-- Supports OLAP-style slice/dice/roll-up via dimension joins on Sales_Fact
-- ============================================================================
-- Before running: CREATE DATABASE retail_dw CHARACTER SET utf8mb4;
-- USE retail_dw;

SET NAMES utf8mb4;

-- ----------------------------------------------------------------------------
-- TIME DIMENSION
-- One row per calendar day. Time_ID is a surrogate key for the fact table.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Time_Dim (
    Time_ID     INT AUTO_INCREMENT PRIMARY KEY,
    `Date`      DATE NOT NULL,
    Month       TINYINT NOT NULL COMMENT '1-12',
    Year        SMALLINT NOT NULL,
    UNIQUE KEY uq_time_date (`Date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COMMENT='Conformed date dimension for time-based analysis';

-- ----------------------------------------------------------------------------
-- PRODUCT DIMENSION
-- Product_ID uses the retail StockCode as the business/natural key (stable).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Product_Dim (
    Product_ID   VARCHAR(32) NOT NULL PRIMARY KEY,
    Product_Name VARCHAR(512) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COMMENT='Product master: one row per stock code';

-- ----------------------------------------------------------------------------
-- CUSTOMER DIMENSION
-- Customer_ID stores the source system customer identifier (string for safety).
-- Country supports geographic OLAP slices.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Customer_Dim (
    Customer_ID VARCHAR(64) NOT NULL PRIMARY KEY,
    Country     VARCHAR(128) NOT NULL,
    KEY idx_customer_country (Country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COMMENT='Customer attributes at grain of customer + country';

-- ----------------------------------------------------------------------------
-- SALES FACT TABLE
-- Grain: one row per invoice line (transaction line item).
-- Measures: Quantity, UnitPrice, TotalAmount
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Sales_Fact (
    Transaction_ID BIGINT AUTO_INCREMENT PRIMARY KEY,
    Product_ID       VARCHAR(32) NOT NULL,
    Customer_ID      VARCHAR(64) NOT NULL,
    Time_ID          INT NOT NULL,
    Quantity         INT NOT NULL,
    UnitPrice        DECIMAL(14, 4) NOT NULL,
    TotalAmount      DECIMAL(16, 4) NOT NULL,
    CONSTRAINT fk_sales_product FOREIGN KEY (Product_ID)
        REFERENCES Product_Dim (Product_ID),
    CONSTRAINT fk_sales_customer FOREIGN KEY (Customer_ID)
        REFERENCES Customer_Dim (Customer_ID),
    CONSTRAINT fk_sales_time FOREIGN KEY (Time_ID)
        REFERENCES Time_Dim (Time_ID),
    CONSTRAINT chk_qty_positive CHECK (Quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COMMENT='Fact table: sales line items';

-- OLAP query performance: common filter/group-by columns
CREATE INDEX idx_sales_time ON Sales_Fact (Time_ID);
CREATE INDEX idx_sales_product ON Sales_Fact (Product_ID);
CREATE INDEX idx_sales_customer ON Sales_Fact (Customer_ID);
