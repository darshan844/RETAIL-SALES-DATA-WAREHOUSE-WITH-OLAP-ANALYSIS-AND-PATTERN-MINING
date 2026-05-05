-- ============================================================================
-- OLAP-style analytical queries (MySQL)
-- Run against the populated retail_dw database after ETL load.
-- ============================================================================

USE retail_dw;

-- ----------------------------------------------------------------------------
-- 1) Total sales by year
-- Roll-up revenue (TotalAmount) to calendar year using Time_Dim.
-- ----------------------------------------------------------------------------
SELECT
    t.`Year` AS sales_year,
    ROUND(SUM(f.TotalAmount), 2) AS total_sales
FROM Sales_Fact AS f
JOIN Time_Dim AS t ON f.Time_ID = t.Time_ID
GROUP BY t.`Year`
ORDER BY t.`Year`;

-- ----------------------------------------------------------------------------
-- 2) Total sales by country
-- Geographic slice: sum revenue by customer country.
-- ----------------------------------------------------------------------------
SELECT
    c.Country,
    ROUND(SUM(f.TotalAmount), 2) AS total_sales
FROM Sales_Fact AS f
JOIN Customer_Dim AS c ON f.Customer_ID = c.Customer_ID
GROUP BY c.Country
ORDER BY total_sales DESC;

-- ----------------------------------------------------------------------------
-- 3) Monthly sales trend
-- Time series at year-month grain for trend charts.
-- ----------------------------------------------------------------------------
SELECT
    t.`Year`,
    t.`Month`,
    DATE_FORMAT(t.`Date`, '%Y-%m') AS month_key,
    ROUND(SUM(f.TotalAmount), 2) AS monthly_sales
FROM Sales_Fact AS f
JOIN Time_Dim AS t ON f.Time_ID = t.Time_ID
GROUP BY t.`Year`, t.`Month`, DATE_FORMAT(t.`Date`, '%Y-%m')
ORDER BY t.`Year`, t.`Month`;

-- ----------------------------------------------------------------------------
-- 4) Top 10 selling products (by total quantity sold)
-- Product ranking for basket analysis validation and merchandising insight.
-- ----------------------------------------------------------------------------
SELECT
    p.Product_ID,
    p.Product_Name,
    SUM(f.Quantity) AS total_quantity_sold
FROM Sales_Fact AS f
JOIN Product_Dim AS p ON f.Product_ID = p.Product_ID
GROUP BY p.Product_ID, p.Product_Name
ORDER BY total_quantity_sold DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- 5) Total revenue by product
-- Revenue measure aggregated at product grain.
-- ----------------------------------------------------------------------------
SELECT
    p.Product_ID,
    p.Product_Name,
    ROUND(SUM(f.TotalAmount), 2) AS total_revenue
FROM Sales_Fact AS f
JOIN Product_Dim AS p ON f.Product_ID = p.Product_ID
GROUP BY p.Product_ID, p.Product_Name
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------------------------
-- 6) Total transactions per country
-- Here "transactions" = number of fact rows (line items) per country.
-- (If invoice grain is required, add InvoiceNo to the fact table in a future revision.)
-- ----------------------------------------------------------------------------
SELECT
    c.Country,
    COUNT(*) AS total_line_items
FROM Sales_Fact AS f
JOIN Customer_Dim AS c ON f.Customer_ID = c.Customer_ID
GROUP BY c.Country
ORDER BY total_line_items DESC;
