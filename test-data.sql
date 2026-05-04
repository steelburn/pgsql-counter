-- PostgreSQL Test Data
-- This script populates the database with realistic test data for migration testing

-- ============================================================
-- POPULATE USERS TABLE
-- ============================================================
INSERT INTO public.users (username, email, first_name, last_name) VALUES
('john_doe', 'john.doe@example.com', 'John', 'Doe'),
('jane_smith', 'jane.smith@example.com', 'Jane', 'Smith'),
('bob_wilson', 'bob.wilson@example.com', 'Bob', 'Wilson'),
('alice_johnson', 'alice.johnson@example.com', 'Alice', 'Johnson'),
('charlie_brown', 'charlie.brown@example.com', 'Charlie', 'Brown'),
('diana_prince', 'diana.prince@example.com', 'Diana', 'Prince'),
('edward_norton', 'edward.norton@example.com', 'Edward', 'Norton'),
('fiona_apple', 'fiona.apple@example.com', 'Fiona', 'Apple'),
('george_martin', 'george.martin@example.com', 'George', 'Martin'),
('hannah_montana', 'hannah.montana@example.com', 'Hannah', 'Montana');

-- Add 490 more users to reach 500
INSERT INTO public.users (username, email, first_name, last_name)
SELECT 
    'user_' || seq::text,
    'user' || seq::text || '@example.com',
    'FirstName' || seq::text,
    'LastName' || seq::text
FROM GENERATE_SERIES(11, 500) seq;

-- ============================================================
-- POPULATE CATEGORIES TABLE
-- ============================================================
INSERT INTO public.categories (name, description) VALUES
('Electronics', 'Electronic devices and gadgets'),
('Clothing', 'Apparel and fashion items'),
('Books', 'Physical and digital books'),
('Home & Garden', 'Home improvement and garden products'),
('Sports & Outdoors', 'Sports equipment and outdoor gear'),
('Toys & Games', 'Toys, games, and entertainment'),
('Beauty & Personal Care', 'Cosmetics and personal care items'),
('Food & Beverage', 'Food products and beverages');

-- ============================================================
-- POPULATE PRODUCTS TABLE
-- ============================================================
INSERT INTO public.products (name, description, price, category, stock_quantity) VALUES
('Laptop Pro 15', 'High-performance laptop with 16GB RAM', 1299.99, 'Electronics', 25),
('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 29.99, 'Electronics', 150),
('USB-C Cable', 'Durable USB-C charging cable, 6ft', 12.99, 'Electronics', 500),
('T-Shirt', 'Cotton crew neck t-shirt', 19.99, 'Clothing', 200),
('Jeans', 'Classic blue denim jeans', 49.99, 'Clothing', 100),
('Running Shoes', 'Professional running shoes', 89.99, 'Sports & Outdoors', 75),
('Python Programming', 'Learn Python from basics to advanced', 39.99, 'Books', 300),
('React Guide', 'Complete guide to React.js', 44.99, 'Books', 250),
('Coffee Maker', 'Programmable coffee maker, 12 cups', 79.99, 'Home & Garden', 45),
('Plant Pot', 'Ceramic plant pot, 10 inches', 24.99, 'Home & Garden', 120);

-- Add 40 more products to reach 50
INSERT INTO public.products (name, description, price, category, stock_quantity)
SELECT 
    'Product ' || seq::text,
    'Description for product ' || seq::text,
    10.00 + (seq % 100) * 0.99,
    CASE seq % 8
        WHEN 0 THEN 'Electronics'
        WHEN 1 THEN 'Clothing'
        WHEN 2 THEN 'Books'
        WHEN 3 THEN 'Home & Garden'
        WHEN 4 THEN 'Sports & Outdoors'
        WHEN 5 THEN 'Toys & Games'
        WHEN 6 THEN 'Beauty & Personal Care'
        ELSE 'Food & Beverage'
    END,
    100 + (seq % 500)
FROM GENERATE_SERIES(11, 50) seq;

-- ============================================================
-- POPULATE ORDERS TABLE
-- ============================================================
INSERT INTO public.orders (user_id, total_amount, status, shipping_address) VALUES
(1, 1299.99, 'completed', '123 Main St, New York, NY 10001'),
(2, 89.99, 'completed', '456 Oak Ave, Los Angeles, CA 90001'),
(3, 159.97, 'pending', '789 Pine Rd, Chicago, IL 60601'),
(4, 229.95, 'shipped', '321 Elm St, Houston, TX 77001'),
(5, 49.99, 'completed', '654 Maple Dr, Phoenix, AZ 85001'),
(6, 89.99, 'pending', '987 Cedar Ln, Philadelphia, PA 19101'),
(7, 1299.99, 'shipped', '147 Birch Way, San Antonio, TX 78201'),
(8, 39.99, 'completed', '258 Spruce St, San Diego, CA 92101'),
(9, 159.97, 'pending', '369 Walnut Ave, Dallas, TX 75201'),
(10, 299.96, 'shipped', '741 Oak St, San Jose, CA 95101');

-- Add 190 more orders to reach 200
INSERT INTO public.orders (user_id, total_amount, status, shipping_address)
SELECT 
    (seq % 500) + 1,
    100.00 + (seq % 1000) * 0.99,
    CASE seq % 4
        WHEN 0 THEN 'completed'
        WHEN 1 THEN 'pending'
        WHEN 2 THEN 'shipped'
        ELSE 'cancelled'
    END,
    'Address ' || seq::text || ', City, State 00000'
FROM GENERATE_SERIES(11, 200) seq;

-- ============================================================
-- POPULATE ORDER_ITEMS TABLE
-- ============================================================
INSERT INTO public.order_items (order_id, product_id, quantity, unit_price)
SELECT 
    (seq % 200) + 1,
    (seq % 50) + 1,
    1 + (seq % 5),
    10.00 + (seq % 100) * 0.99
FROM GENERATE_SERIES(1, 1500) seq;

-- ============================================================
-- POPULATE INVENTORY TABLE
-- ============================================================
INSERT INTO public.inventory (product_id, warehouse_location, quantity_available, quantity_reserved)
SELECT 
    seq,
    'Warehouse-' || ((seq % 5) + 1)::text || ', Shelf-' || ((seq % 20) + 1)::text,
    100 + (seq % 500),
    10 + (seq % 50)
FROM GENERATE_SERIES(1, 50) seq;

-- ============================================================
-- POPULATE REVIEWS TABLE
-- ============================================================
INSERT INTO public.reviews (product_id, user_id, rating, title, comment, helpful_count)
SELECT 
    ((seq % 50) + 1),
    ((seq % 500) + 1),
    ((seq % 5) + 1),
    'Review ' || seq::text,
    'This is a great product! Highly recommended.',
    seq % 100
FROM GENERATE_SERIES(1, 800) seq;

-- ============================================================
-- POPULATE ACTIVITY_LOGS TABLE
-- ============================================================
INSERT INTO public.activity_logs (user_id, action, table_name, record_id, new_values)
SELECT 
    ((seq % 500) + 1),
    CASE seq % 4
        WHEN 0 THEN 'INSERT'
        WHEN 1 THEN 'UPDATE'
        WHEN 2 THEN 'DELETE'
        ELSE 'SELECT'
    END,
    CASE seq % 6
        WHEN 0 THEN 'users'
        WHEN 1 THEN 'products'
        WHEN 2 THEN 'orders'
        WHEN 3 THEN 'order_items'
        WHEN 4 THEN 'reviews'
        ELSE 'categories'
    END,
    seq % 100,
    jsonb_build_object('action', 'update', 'record_id', seq)
FROM GENERATE_SERIES(1, 5000) seq;

-- ============================================================
-- POPULATE AUDIT_TRAIL TABLE
-- ============================================================
INSERT INTO public.audit_trail (entity_type, entity_id, operation, changed_by, details)
SELECT 
    CASE seq % 6
        WHEN 0 THEN 'User'
        WHEN 1 THEN 'Product'
        WHEN 2 THEN 'Order'
        WHEN 3 THEN 'Order_Item'
        WHEN 4 THEN 'Review'
        ELSE 'Category'
    END,
    seq % 100,
    CASE seq % 3
        WHEN 0 THEN 'CREATE'
        WHEN 1 THEN 'UPDATE'
        ELSE 'DELETE'
    END,
    ((seq % 500) + 1),
    jsonb_build_object('change', 'audit entry', 'ref', seq)
FROM GENERATE_SERIES(1, 3000) seq;

-- ============================================================
-- POPULATE SESSIONS TABLE
-- ============================================================
INSERT INTO public.sessions (user_id, token, ip_address, user_agent, expires_at)
SELECT 
    ((seq % 500) + 1),
    'token_' || MD5(seq::text || CURRENT_TIMESTAMP::text),
    '192.168.' || (seq % 256)::text || '.' || ((seq * 7) % 256)::text,
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    CURRENT_TIMESTAMP + INTERVAL '7 days'
FROM GENERATE_SERIES(1, 1000) seq;

-- ============================================================
-- POPULATE PAYMENT_METHODS TABLE
-- ============================================================
INSERT INTO public.payment_methods (user_id, payment_type, last_four, expiry_month, expiry_year, is_default)
SELECT 
    ((seq % 500) + 1),
    CASE seq % 3
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'debit_card'
        ELSE 'paypal'
    END,
    (1000 + (seq % 9000))::text,
    (seq % 12) + 1,
    2025 + (seq % 5),
    seq % 3 = 0
FROM GENERATE_SERIES(1, 1200) seq;

-- ============================================================
-- POPULATE NOTIFICATIONS TABLE
-- ============================================================
INSERT INTO public.notifications (user_id, type, title, message, is_read)
SELECT 
    ((seq % 500) + 1),
    CASE seq % 5
        WHEN 0 THEN 'order'
        WHEN 1 THEN 'promotion'
        WHEN 2 THEN 'system'
        WHEN 3 THEN 'review'
        ELSE 'message'
    END,
    'Notification Title ' || seq::text,
    'This is notification message number ' || seq::text,
    seq % 2 = 0
FROM GENERATE_SERIES(1, 2000) seq;

-- ============================================================
-- POPULATE COUPONS TABLE
-- ============================================================
INSERT INTO public.coupons (code, discount_type, discount_value, max_uses, times_used, valid_from, valid_until) VALUES
('SAVE10', 'percentage', 10.00, 1000, 250, CURRENT_TIMESTAMP - INTERVAL '30 days', CURRENT_TIMESTAMP + INTERVAL '30 days'),
('SAVE20', 'percentage', 20.00, 500, 150, CURRENT_TIMESTAMP - INTERVAL '15 days', CURRENT_TIMESTAMP + INTERVAL '15 days'),
('FLAT50', 'fixed', 50.00, 300, 75, CURRENT_TIMESTAMP - INTERVAL '7 days', CURRENT_TIMESTAMP + INTERVAL '7 days'),
('FREESHIPPING', 'fixed', 9.99, 2000, 500, CURRENT_TIMESTAMP - INTERVAL '60 days', CURRENT_TIMESTAMP + INTERVAL '60 days'),
('WELCOME15', 'percentage', 15.00, 100, 45, CURRENT_TIMESTAMP - INTERVAL '1 day', CURRENT_TIMESTAMP + INTERVAL '30 days');

-- ============================================================
-- SUMMARY OF INSERTED DATA
-- ============================================================
-- Users: 500
-- Products: 50
-- Orders: 200
-- Order Items: 1500 (variable quantity)
-- Inventory: 50
-- Reviews: 800
-- Activity Logs: 5000
-- Audit Trail: 3000
-- Sessions: 1000
-- Payment Methods: 1200
-- Notifications: 2000
-- Coupons: 5
-- Categories: 8
-- TOTAL RECORDS: ~18,808
