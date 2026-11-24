CREATE DATABASE IF NOT EXISTS mithun_restaurant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mithun_restaurant;

CREATE TABLE IF NOT EXISTS admins (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(60) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS settings (
  setting_key VARCHAR(80) PRIMARY KEY,
  setting_value VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE,
  active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  category_id INT NULL,
  name VARCHAR(120) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS orders (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  bill_no VARCHAR(40) NOT NULL UNIQUE,
  customer_name VARCHAR(120) NOT NULL,
  customer_mobile VARCHAR(15) NOT NULL,
  subtotal DECIMAL(10,2) NOT NULL,
  discount DECIMAL(10,2) NOT NULL DEFAULT 0,
  gst_rate DECIMAL(5,2) NOT NULL,
  gst_amount DECIMAL(10,2) NOT NULL,
  grand_total DECIMAL(10,2) NOT NULL,
  payment_method ENUM('Cash','UPI','Card') NOT NULL,
  created_at DATETIME NOT NULL,
  INDEX idx_orders_date (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  order_id BIGINT NOT NULL,
  product_id INT NULL,
  item_name VARCHAR(120) NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  line_total DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
) ENGINE=InnoDB;

INSERT IGNORE INTO settings (setting_key, setting_value) VALUES
('restaurant_name','Mithun Restaurant'),
('address','Mumbai, Maharashtra, India'),
('phone',''),
('gstin',''),
('gst_rate','5'),
('currency','INR');

INSERT IGNORE INTO categories (name) VALUES ('Pizza'),('Burgers'),('Meals'),('Drinks'),('Desserts');

INSERT INTO products (category_id,name,price)
SELECT c.id, x.name, x.price FROM categories c
JOIN (
 SELECT 'Pizza' cat,'Margherita Pizza' name,199.00 price UNION ALL
 SELECT 'Pizza','Farmhouse Pizza',249.00 UNION ALL
 SELECT 'Burgers','Veg Burger',99.00 UNION ALL
 SELECT 'Burgers','Cheese Burger',129.00 UNION ALL
 SELECT 'Meals','Veg Biryani',180.00 UNION ALL
 SELECT 'Drinks','Cold Drink',40.00 UNION ALL
 SELECT 'Desserts','Vanilla Ice Cream',60.00
) x ON x.cat=c.name
WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name=x.name);
