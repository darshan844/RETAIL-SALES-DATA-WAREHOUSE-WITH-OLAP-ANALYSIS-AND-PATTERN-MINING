-- create_retail.sql
-- Creates the project database and user for the Retail DW project.
-- Replace 'your_password' below with a strong password before running.

CREATE DATABASE IF NOT EXISTS retail_dw CHARACTER SET utf8mb4;

-- Replace 'your_password' with a strong password (keep the quotes)
CREATE USER IF NOT EXISTS 'retail_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON retail_dw.* TO 'retail_user'@'localhost';
FLUSH PRIVILEGES;

-- End of file
