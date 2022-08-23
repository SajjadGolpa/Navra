CREATE USER 'navra'@'localhost' IDENTIFIED BY 'N@vRa';
CREATE DATABASE navra_db;
CREATE TABLE Discount_Table (Discount_Code varchar(255), PersonID int);
GRANT INSERT, UPDATE, SELECT on navra_db.Discount_Table TO 'navra'@'localhost';