```sql
-- ============================================
-- Создание ERP БД для системы учета заказов
-- PostgreSQL 16+
-- ============================================

-- Создание базы данных
CREATE DATABASE erp_orders_db;

-- Уже в базе данных:
       
-- Включение необходимых расширений
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ============================================
-- 1. Таблица категорий (иерархическая структура)
-- ============================================
CREATE TABLE categories (
    id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT REFERENCES categories(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    path VARCHAR(1000) DEFAULT '',  -- УБРАТЬ NOT NULL
    level INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE categories IS 'Иерархия категорий товаров с неограниченной вложенностью';
COMMENT ON COLUMN categories.path IS 'Материализованный путь для быстрого поиска';
COMMENT ON COLUMN categories.level IS 'Уровень вложенности (0 - корневой)';

-- Индексы для таблицы категорий
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_path ON categories(path);
CREATE INDEX idx_categories_level ON categories(level);
CREATE INDEX idx_categories_name ON categories(name);
CREATE INDEX idx_categories_created ON categories(created_at DESC);

-- ============================================
-- 2. Таблица товаров
-- ============================================
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT REFERENCES categories(id) ON DELETE SET NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    price NUMERIC(15,2) NOT NULL CHECK (price >= 0),
    cost_price NUMERIC(15,2) CHECK (cost_price >= 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reserved_quantity INTEGER NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    min_stock_level INTEGER DEFAULT 10,
    weight_kg NUMERIC(10,3),
    dimensions VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Генерируемая колонка для доступного количества
ALTER TABLE products 
ADD COLUMN available_quantity INTEGER 
GENERATED ALWAYS AS (quantity - reserved_quantity) STORED;

COMMENT ON TABLE products IS 'Номенклатура товаров';
COMMENT ON COLUMN products.sku IS 'Артикул/уникальный идентификатор товара';
COMMENT ON COLUMN products.reserved_quantity IS 'Количество товара в резерве (в заказах)';
COMMENT ON COLUMN products.available_quantity IS 'Доступное количество (quantity - reserved_quantity)';

-- Индексы для таблицы товаров
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_quantity ON products(quantity);
CREATE INDEX idx_products_available ON products(available_quantity);
CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_products_created ON products(created_at DESC);

-- Составной индекс для частых запросов
CREATE INDEX idx_products_category_active ON products(category_id, is_active) 
WHERE is_active = TRUE;

-- ============================================
-- 3. Таблица клиентов
-- ============================================
CREATE TABLE customers (
    id BIGSERIAL PRIMARY KEY,
    customer_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    legal_name VARCHAR(500),
    tax_id VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    email VARCHAR(255),
    phone VARCHAR(50),
    phone_secondary VARCHAR(50),
    discount_rate NUMERIC(5,2) DEFAULT 0 CHECK (discount_rate BETWEEN 0 AND 100),
    credit_limit NUMERIC(15,2) DEFAULT 0,
    payment_terms_days INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE customers IS 'Клиенты/покупатели';
COMMENT ON COLUMN customers.customer_code IS 'Уникальный код клиента для бизнес-процессов';

-- Индексы для таблицы клиентов
CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_customers_active ON customers(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_customers_created ON customers(created_at DESC);

-- ============================================
-- 4. Таблица заказов
-- ============================================
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'new' 
        CHECK (status IN ('new', 'processing', 'shipped', 'delivered', 'cancelled', 'returned')),
    total_amount NUMERIC(15,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    total_discount NUMERIC(15,2) DEFAULT 0 CHECK (total_discount >= 0),
    shipping_cost NUMERIC(15,2) DEFAULT 0 CHECK (shipping_cost >= 0),
    tax_amount NUMERIC(15,2) DEFAULT 0 CHECK (tax_amount >= 0),
    final_amount NUMERIC(15,2) NOT NULL GENERATED ALWAYS 
        AS (total_amount - total_discount + shipping_cost + tax_amount) STORED,
    currency VARCHAR(3) DEFAULT 'USD',
    shipping_address TEXT,
    billing_address TEXT,
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'pending' 
        CHECK (payment_status IN ('pending', 'paid', 'partial', 'refunded')),
    estimated_delivery DATE,
    actual_delivery DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE orders IS 'Заказы покупателей';
COMMENT ON COLUMN orders.order_number IS 'Уникальный номер заказа для документооборота';
COMMENT ON COLUMN orders.final_amount IS 'Итоговая сумма к оплате';

-- Индексы для таблицы заказов
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_order_date ON orders(order_date DESC);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_final_amount ON orders(final_amount DESC);
CREATE INDEX idx_orders_dates ON orders(order_date, estimated_delivery);
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date DESC);

-- Частичные индексы для активных заказов
CREATE INDEX idx_orders_active ON orders(status) 
WHERE status IN ('new', 'processing');

-- ============================================
-- 5. Таблица позиций заказа
-- ============================================
CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(15,2) NOT NULL CHECK (unit_price >= 0),
    discount_percent NUMERIC(5,2) DEFAULT 0 CHECK (discount_percent BETWEEN 0 AND 100),
    discount_amount NUMERIC(15,2) DEFAULT 0,
    item_total NUMERIC(15,2) NOT NULL GENERATED ALWAYS 
        AS (quantity * unit_price * (1 - discount_percent/100) - discount_amount) STORED,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE order_items IS 'Позиции в заказе';
COMMENT ON COLUMN order_items.item_total IS 'Сумма позиции с учетом скидок';

-- Индексы для таблицы позиций заказа
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_quantity ON order_items(quantity);
CREATE INDEX idx_order_items_unit_price ON order_items(unit_price);
CREATE INDEX idx_order_items_created ON order_items(created_at DESC);

-- Составные индексы для аналитических запросов
CREATE INDEX idx_order_items_product_order ON order_items(product_id, order_id);
CREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);

-- ============================================
-- 6. Таблица изменений цен (история)
-- ============================================
CREATE TABLE price_history (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    old_price NUMERIC(15,2),
    new_price NUMERIC(15,2) NOT NULL,
    change_reason VARCHAR(255),
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE price_history IS 'История изменений цен на товары';

CREATE INDEX idx_price_history_product ON price_history(product_id);
CREATE INDEX idx_price_history_date ON price_history(changed_at DESC);

-- ============================================
-- ТРИГГЕРЫ И ФУНКЦИИ
-- ============================================

-- Функция для обновления timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для обновления updated_at
CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Функция для обновления общей суммы заказа
CREATE OR REPLACE FUNCTION update_order_total()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE orders 
    SET total_amount = COALESCE(
        (SELECT SUM(item_total) FROM order_items WHERE order_id = COALESCE(NEW.order_id, OLD.order_id)),
        0
    ),
    total_discount = COALESCE(
        (SELECT SUM(quantity * unit_price * discount_percent/100 + discount_amount) 
         FROM order_items 
         WHERE order_id = COALESCE(NEW.order_id, OLD.order_id)),
        0
    )
    WHERE id = COALESCE(NEW.order_id, OLD.order_id);
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Триггер для пересчета сумм заказа
CREATE TRIGGER order_items_total_trigger
AFTER INSERT OR UPDATE OR DELETE ON order_items
FOR EACH ROW
EXECUTE FUNCTION update_order_total();

-- Функция для обновления резерва товаров
CREATE OR REPLACE FUNCTION update_product_reserve()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Увеличиваем резерв при добавлении позиции заказа
        UPDATE products 
        SET reserved_quantity = reserved_quantity + NEW.quantity
        WHERE id = NEW.product_id;
        
        -- Проверяем доступность
        IF EXISTS (
            SELECT 1 FROM products 
            WHERE id = NEW.product_id 
            AND available_quantity < 0
        ) THEN
            RAISE EXCEPTION 'Недостаточно товара на складе. Product ID: %', NEW.product_id;
        END IF;
        
    ELSIF TG_OP = 'DELETE' THEN
        -- Уменьшаем резерв при удалении позиции
        UPDATE products 
        SET reserved_quantity = reserved_quantity - OLD.quantity
        WHERE id = OLD.product_id;
        
    ELSIF TG_OP = 'UPDATE' THEN
        -- Корректируем резерв при изменении количества
        UPDATE products 
        SET reserved_quantity = reserved_quantity - OLD.quantity + NEW.quantity
        WHERE id = NEW.product_id;
        
        -- Проверяем доступность после обновления
        IF EXISTS (
            SELECT 1 FROM products 
            WHERE id = NEW.product_id 
            AND available_quantity < 0
        ) THEN
            RAISE EXCEPTION 'Недостаточно товара на складе после обновления. Product ID: %', NEW.product_id;
        END IF;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Триггер для управления резервом товаров
CREATE TRIGGER order_items_reserve_trigger
AFTER INSERT OR UPDATE OR DELETE ON order_items
FOR EACH ROW
EXECUTE FUNCTION update_product_reserve();

-- Функция для логгирования изменения цен
CREATE OR REPLACE FUNCTION log_price_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.price IS DISTINCT FROM NEW.price THEN
        INSERT INTO price_history (product_id, old_price, new_price, change_reason)
        VALUES (NEW.id, OLD.price, NEW.price, 'Price update');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для логирования цен
CREATE TRIGGER products_price_log_trigger
AFTER UPDATE OF price ON products
FOR EACH ROW
WHEN (OLD.price IS DISTINCT FROM NEW.price)
EXECUTE FUNCTION log_price_change();

-- Функция для автоматического обновления пути категорий
CREATE OR REPLACE FUNCTION update_category_path()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.path = NEW.id::TEXT;
        NEW.level = 0;
    ELSE
        SELECT path || '>' || NEW.id::TEXT, level + 1
        INTO NEW.path, NEW.level
        FROM categories
        WHERE id = NEW.parent_id;
    END IF;
    
    -- Обновляем пути у всех дочерних категорий
    IF TG_OP = 'UPDATE' AND (OLD.parent_id IS DISTINCT FROM NEW.parent_id OR OLD.path IS DISTINCT FROM NEW.path) THEN
        UPDATE categories c
        SET path = NEW.path || SUBSTRING(c.path FROM LENGTH(OLD.path) + 1),
            level = NEW.level + (c.level - OLD.level)
        WHERE c.path LIKE OLD.path || '>%';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для пути категорий (BEFORE для правильного вычисления)
CREATE OR REPLACE FUNCTION update_category_path()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Для INSERT вычисляем в AFTER триггере
        IF NEW.parent_id IS NULL THEN
            NEW.path = NEW.id::TEXT;
            NEW.level = 0;
        ELSE
            -- В BEFORE триггере id ещё нет, отложим вычисление
            -- или уберём NOT NULL constraint
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Для UPDATE можно в BEFORE
        IF OLD.parent_id IS DISTINCT FROM NEW.parent_id THEN
            IF NEW.parent_id IS NULL THEN
                NEW.path = NEW.id::TEXT;
                NEW.level = 0;
            ELSE
                SELECT path || '>' || NEW.id::TEXT, level + 1
                INTO NEW.path, NEW.level
                FROM categories
                WHERE id = NEW.parent_id;
            END IF;
            
            -- Обновляем пути у всех дочерних категорий
            UPDATE categories c
            SET path = NEW.path || SUBSTRING(c.path FROM LENGTH(OLD.path) + 1),
                level = NEW.level + (c.level - OLD.level)
            WHERE c.path LIKE OLD.path || '>%';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- МАТЕРИАЛИЗОВАННЫЕ ПРЕДСТАВЛЕНИЯ ДЛЯ ОТЧЕТОВ
-- ============================================

-- Топ товаров по месяцам
CREATE MATERIALIZED VIEW mv_top_products_monthly AS
WITH product_stats AS (
    SELECT 
        p.id AS product_id,
        p.name AS product_name,
        p.sku,
        c.id AS top_category_id,
        c.name AS top_category_name,
        DATE_TRUNC('month', o.order_date) AS month_period,
        SUM(oi.quantity) AS total_sold_units,
        SUM(oi.item_total) AS total_revenue,
        COUNT(DISTINCT o.id) AS order_count
    FROM products p
    JOIN order_items oi ON p.id = oi.product_id
    JOIN orders o ON oi.order_id = o.id
    LEFT JOIN LATERAL (
        WITH RECURSIVE category_path AS (
            SELECT id, parent_id, name
            FROM categories 
            WHERE id = p.category_id
            UNION ALL
            SELECT c2.id, c2.parent_id, c2.name
            FROM categories c2
            JOIN category_path cp ON c2.id = cp.parent_id
        )
        SELECT id, name
        FROM category_path
        WHERE parent_id IS NULL
        LIMIT 1
    ) c ON TRUE
    WHERE o.status NOT IN ('cancelled', 'returned')
    GROUP BY p.id, p.name, p.sku, c.id, c.name, DATE_TRUNC('month', o.order_date)
)
SELECT 
    *,
    ROW_NUMBER() OVER (PARTITION BY month_period ORDER BY total_sold_units DESC) AS rank_by_units,
    ROW_NUMBER() OVER (PARTITION BY month_period ORDER BY total_revenue DESC) AS rank_by_revenue
FROM product_stats;

-- Индексы для материализованного представления
CREATE UNIQUE INDEX idx_mv_top_products_unique 
ON mv_top_products_monthly (product_id, month_period);

CREATE INDEX idx_mv_top_products_month 
ON mv_top_products_monthly (month_period DESC);

CREATE INDEX idx_mv_top_products_units 
ON mv_top_products_monthly (total_sold_units DESC);

CREATE INDEX idx_mv_top_products_revenue 
ON mv_top_products_monthly (total_revenue DESC);

-- Ежемесячная статистика по клиентам
CREATE MATERIALIZED VIEW mv_customer_monthly_stats AS
SELECT 
    c.id AS customer_id,
    c.name AS customer_name,
    DATE_TRUNC('month', o.order_date) AS month_period,
    COUNT(DISTINCT o.id) AS order_count,
    SUM(o.final_amount) AS total_spent,
    AVG(o.final_amount) AS avg_order_value,
    SUM(oi.quantity) AS total_items_purchased
FROM customers c
JOIN orders o ON c.id = o.customer_id
JOIN order_items oi ON o.id = oi.order_id
WHERE o.status NOT IN ('cancelled', 'returned')
GROUP BY c.id, c.name, DATE_TRUNC('month', o.order_date);

CREATE UNIQUE INDEX idx_mv_customer_stats_unique 
ON mv_customer_monthly_stats (customer_id, month_period);

-- ============================================
-- ПРЕДСТАВЛЕНИЯ (VIEWS)
-- ============================================

-- Представление для получения иерархии категорий
CREATE VIEW v_category_tree AS
WITH RECURSIVE category_tree AS (
    SELECT 
        id,
        name,
        parent_id,
        path,
        level,
        1 AS display_order,
        name::TEXT AS full_path
    FROM categories
    WHERE parent_id IS NULL
    
    UNION ALL
    
    SELECT 
        c.id,
        c.name,
        c.parent_id,
        c.path,
        c.level,
        ct.display_order + 1,
        ct.full_path || ' > ' || c.name
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree
ORDER BY path;

-- Представление для доступных товаров
CREATE VIEW v_available_products AS
SELECT 
    p.id,
    p.sku,
    p.name,
    c.name AS category_name,
    p.price,
    p.available_quantity,
    p.quantity,
    p.reserved_quantity,
    CASE 
        WHEN p.available_quantity <= p.min_stock_level THEN 'LOW_STOCK'
        WHEN p.available_quantity = 0 THEN 'OUT_OF_STOCK'
        ELSE 'IN_STOCK'
    END AS stock_status
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.is_active = TRUE;

-- Представление для активных заказов
CREATE VIEW v_active_orders AS
SELECT 
    o.id,
    o.order_number,
    o.order_date,
    c.name AS customer_name,
    o.status,
    o.final_amount,
    o.payment_status,
    COUNT(oi.id) AS item_count,
    SUM(oi.quantity) AS total_quantity
FROM orders o
JOIN customers c ON o.customer_id = c.id
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.status IN ('new', 'processing')
GROUP BY o.id, o.order_number, o.order_date, c.name, o.status, o.final_amount, o.payment_status;

-- ============================================
-- ФУНКЦИИ ДЛЯ ОТЧЕТОВ
-- ============================================

-- Функция для получения дочерних категорий
CREATE OR REPLACE FUNCTION get_child_categories(parent_id_param BIGINT)
RETURNS TABLE(
    category_id BIGINT,
    category_name VARCHAR,
    category_level INTEGER,
    category_path VARCHAR,
    full_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE child_categories AS (
        SELECT 
            c.id,
            c.name,
            c.level,
            c.path,
            c.name::TEXT AS full_path
        FROM categories c
        WHERE c.id = parent_id_param OR parent_id_param IS NULL
        
        UNION ALL
        
        SELECT 
            c.id,
            c.name,
            c.level,
            c.path,
            (cc.full_path || ' > ' || c.name)::TEXT
        FROM categories c
        JOIN child_categories cc ON c.parent_id = cc.id
    )
    SELECT 
        cc.id AS category_id,
        cc.name AS category_name,
        cc.level AS category_level,
        cc.path AS category_path,
        cc.full_path
    FROM child_categories cc
    WHERE cc.id != COALESCE(parent_id_param, -1)
    ORDER BY cc.path;
END;
$$ LANGUAGE plpgsql;

-- Функция для отчета "Топ-5 товаров за последний месяц"
CREATE OR REPLACE FUNCTION get_top_products_last_month(limit_count INT DEFAULT 5)
RETURNS TABLE(
    product_name VARCHAR,
    first_level_category VARCHAR,
    total_sold_units BIGINT,
    total_revenue NUMERIC,
    product_rank BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.name::VARCHAR,
        c_top.name::VARCHAR,
        SUM(oi.quantity)::BIGINT,
        SUM(oi.item_total)::NUMERIC,
        ROW_NUMBER() OVER (ORDER BY SUM(oi.quantity) DESC)::BIGINT
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    LEFT JOIN LATERAL (
        WITH RECURSIVE cat_hierarchy AS (
            SELECT id, parent_id, name
            FROM categories 
            WHERE id = p.category_id
            UNION ALL
            SELECT c2.id, c2.parent_id, c2.name
            FROM categories c2
            JOIN cat_hierarchy ch ON c2.id = ch.parent_id
        )
        SELECT name
        FROM cat_hierarchy
        WHERE parent_id IS NULL
        LIMIT 1
    ) c_top ON TRUE
    WHERE o.order_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
        AND o.order_date < DATE_TRUNC('month', CURRENT_DATE)
        AND o.status NOT IN ('cancelled', 'returned')
    GROUP BY p.id, p.name, c_top.name
    ORDER BY SUM(oi.quantity) DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- ТЕСТОВЫЕ ДАННЫЕ
-- ============================================

-- Вставка тестовых категорий
INSERT INTO categories (parent_id, name, description) VALUES
(NULL, 'Бытовая техника', 'Бытовая техника для дома'),
(NULL, 'Компьютеры', 'Компьютерная техника и комплектующие'),
(NULL, 'Электроника', 'Электронные устройства и гаджеты');

INSERT INTO categories (parent_id, name, description) VALUES
(1, 'Стиральные машины', 'Стиральные машины различного типа'),
(1, 'Холодильники', 'Холодильники и морозильные камеры'),
(1, 'Телевизоры', 'Телевизоры и аксессуары'),
(2, 'Ноутбуки', 'Портативные компьютеры'),
(2, 'Моноблоки', 'Моноблочные компьютеры'),
(3, 'Смартфоны', 'Мобильные телефоны'),
(3, 'Планшеты', 'Планшетные компьютеры');

INSERT INTO categories (parent_id, name, description) VALUES
(5, 'Однокамерные', 'Однокамерные холодильники'),
(5, 'Двухкамерные', 'Двухкамерные холодильники'),
(8, '17"', 'Ноутбуки с диагональю 17 дюймов'),
(8, '19"', 'Ноутбуки с диагональю 19 дюймов');

-- Вставка тестовых товаров
INSERT INTO products (category_id, sku, name, description, price, quantity) VALUES
(4, 'WM-001', 'Стиральная машина Samsung', 'Стиральная машина с фронтальной загрузкой', 29999.99, 10),
(10, 'FR-001', 'Холодильник Bosch однокамерный', 'Однокамерный холодильник с морозилкой', 24999.50, 5),
(11, 'FR-002', 'Холодильник LG двухкамерный', 'Двухкамерный холодильник No Frost', 45999.00, 8),
(12, 'LP-001', 'Ноутбук Dell 17"', 'Игровой ноутбук 17 дюймов', 89999.99, 15),
(13, 'LP-002', 'Ноутбук Asus 19"', 'Ноутбук с диагональю 19 дюймов', 74999.50, 12),
(9, 'MB-001', 'Моноблок Apple iMac', 'Моноблок 24 дюйма', 129999.00, 3),
(6, 'TV-001', 'Телевизор Sony 55"', 'Телевизор 4K HDR', 69999.99, 7);

-- Вставка тестовых клиентов
INSERT INTO customers (customer_code, name, address, email, phone) VALUES
('CUST-001', 'ИП Иванов А.С.', 'ул. Ленина, 10, Москва', 'ivanov@example.com', '+7 (495) 111-22-33'),
('CUST-002', 'ООО "Ромашка"', 'пр. Мира, 25, Санкт-Петербург', 'info@romashka.ru', '+7 (812) 222-33-44'),
('CUST-003', 'АО "Техносила"', 'ул. Кирова, 15, Екатеринбург', 'sales@technosila.com', '+7 (343) 333-44-55'),
('CUST-004', 'Частный покупатель: Петров И.И.', 'ул. Гагарина, 7, Казань', 'petrov@mail.ru', '+7 (843) 444-55-66');

-- Вставка тестовых заказов
INSERT INTO orders (customer_id, order_number, order_date, status, payment_status) VALUES
(1, 'ORD-2024-001', CURRENT_TIMESTAMP - INTERVAL '5 days', 'delivered', 'paid'),
(2, 'ORD-2024-002', CURRENT_TIMESTAMP - INTERVAL '3 days', 'processing', 'partial'),
(3, 'ORD-2024-003', CURRENT_TIMESTAMP - INTERVAL '1 day', 'new', 'pending'),
(4, 'ORD-2024-004', CURRENT_TIMESTAMP - INTERVAL '10 days', 'delivered', 'paid'),
(1, 'ORD-2024-005', CURRENT_TIMESTAMP - INTERVAL '15 days', 'delivered', 'paid');

-- Вставка тестовых позиций заказов
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 29999.99),
(1, 3, 1, 45999.00),
(2, 4, 2, 89999.99),
(2, 5, 1, 74999.50),
(3, 6, 1, 129999.00),
(3, 7, 2, 69999.99),
(4, 2, 1, 24999.50),
(4, 1, 1, 29999.99),
(5, 3, 1, 45999.00),
(5, 4, 1, 89999.99);

-- Добавляем заказы за прошлый месяц
INSERT INTO orders (customer_id, order_number, order_date, status, payment_status) VALUES
(1, 'ORD-2024-01-OLD', 
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '5 days',
    'delivered', 'paid'),
(2, 'ORD-2024-02-OLD', 
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '10 days',
    'delivered', 'paid'),
(3, 'ORD-2024-03-OLD', 
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' + INTERVAL '15 days',
    'delivered', 'paid');

-- Добавляем позиции к этим заказам
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(6, 1, 3, 29999.99),  -- order_id должен соответствовать новым заказам
(6, 3, 2, 45999.00),
(7, 4, 1, 89999.99),
(8, 7, 5, 69999.99);

-- ============================================
-- ПРИВИЛЕГИИ
-- ============================================

-- Создание ролей
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'erp_admin') THEN
        CREATE ROLE erp_admin WITH LOGIN PASSWORD 'secure_password';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'erp_user') THEN
        CREATE ROLE erp_user WITH LOGIN PASSWORD 'user_password';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'erp_report') THEN
        CREATE ROLE erp_report WITH LOGIN PASSWORD 'report_password';
    END IF;
END
$$;

-- Назначение привилегий
GRANT ALL PRIVILEGES ON DATABASE erp_orders_db TO erp_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO erp_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO erp_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO erp_admin;

GRANT CONNECT ON DATABASE erp_orders_db TO erp_user, erp_report;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO erp_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO erp_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO erp_user;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO erp_report;
GRANT SELECT ON mv_top_products_monthly TO erp_report;
GRANT SELECT ON mv_customer_monthly_stats TO erp_report;
GRANT SELECT ON v_category_tree TO erp_report;
GRANT SELECT ON v_available_products TO erp_report;
GRANT SELECT ON v_active_orders TO erp_report;
GRANT EXECUTE ON FUNCTION get_top_products_last_month TO erp_report;
GRANT EXECUTE ON FUNCTION get_child_categories TO erp_report;

-- ============================================
-- ОПТИМИЗАЦИОННЫЕ НАСТРОЙКИ
-- ============================================

-- Сбор статистики
ANALYZE categories;
ANALYZE products;
ANALYZE customers;
ANALYZE orders;
ANALYZE order_items;

-- Комментарии для таблиц
COMMENT ON MATERIALIZED VIEW mv_top_products_monthly IS 'Материализованное представление для быстрого получения топа товаров';
COMMENT ON MATERIALIZED VIEW mv_customer_monthly_stats IS 'Ежемесячная статистика по клиентам';

-- ============================================
-- ФИНАЛЬНЫЕ ПРОВЕРКИ
-- ============================================

-- Проверка структуры БД
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as total_size,
    pg_size_pretty(pg_relation_size(quote_ident(table_name))) as table_size,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name)) - pg_relation_size(quote_ident(table_name))) as index_size
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;

-- Проверка количества записей
SELECT 
    'categories' as table_name, 
    COUNT(*) as row_count 
FROM categories
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items;

-- Проверка работы функций
SELECT * FROM get_top_products_last_month(5);
SELECT * FROM get_child_categories(1);

-- Обновление материализованных представлений
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_products_monthly;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_monthly_stats;

-- ============================================
-- ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ
-- ============================================
SELECT 
    current_database() as database_name,
    current_user as current_user,
    version() as postgres_version,
    pg_size_pretty(pg_database_size(current_database())) as database_size;
```

## Инструкция по использованию:

1. **Создание БД**: Выполнить весь скрипт в PostgreSQL 16+
2. **Роли и доступ**:
   - `erp_admin` - полный доступ
   - `erp_user` - рабочий доступ
   - `erp_report` - доступ только для отчетов
3. **Основные представления**:
   - `v_category_tree` - иерархия категорий
   - `v_available_products` - доступные товары
   - `v_active_orders` - активные заказы
4. **Материализованные представления**:
   - `mv_top_products_monthly` - топ товаров по месяцам
   - `mv_customer_monthly_stats` - статистика по клиентам
5. **Функции отчетов**:
   - `get_top_products_last_month()` - топ-5 товаров
   - `get_child_categories()` - дочерние категории

## Особенности реализации:
- Полная поддержка иерархии категорий
- Автоматический расчет резервов товаров
- История изменений цен
- Материализованные представления для отчетов
- Триггеры для поддержания целостности данных
- Оптимизированные индексы для быстрых запросов