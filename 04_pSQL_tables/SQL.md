## SQL Запросы

### 1. Сумма товаров по клиентам

```sql
-- 1. Получение информации о сумме товаров заказанных под каждого клиента
SELECT 
    c.name AS "Наименование клиента",
    COALESCE(SUM(o.final_amount), 0) AS "Общая сумма заказов",
    COUNT(DISTINCT o.id) AS "Количество заказов",
    COALESCE(SUM(oi.quantity), 0) AS "Общее количество товаров"
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id 
    AND o.status NOT IN ('cancelled', 'returned')
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY c.id, c.name
ORDER BY "Общая сумма заказов" DESC;
```

### 2. Количество дочерних элементов первого уровня

```sql
-- 2. Найти количество дочерних элементов первого уровня вложенности
SELECT 
    parent.id AS "ID категории",
    parent.name AS "Название категории",
    COUNT(child.id) AS "Количество прямых дочерних категорий"
FROM categories parent
LEFT JOIN categories child ON child.parent_id = parent.id
WHERE parent.parent_id IS NULL  -- только корневые категории
GROUP BY parent.id, parent.name
ORDER BY parent.name;

-- Альтернативный вариант с использованием материализованного пути
SELECT 
    id AS "ID категории",
    name AS "Название категории",
    (SELECT COUNT(*) 
     FROM categories child 
     WHERE child.parent_id = categories.id) AS "Количество дочерних"
FROM categories
WHERE parent_id IS NULL
ORDER BY name;
```

### 3. Топ-5 самых покупаемых товаров за последний месяц

```sql
-- 3. Через существующую функцию
SELECT * FROM get_top_products_last_month(5);

-----------------------------------------------
    
-- Или через View для отчета "Топ-5 самых покупаемых товаров за последний месяц"
CREATE OR REPLACE VIEW v_top_products_last_month AS
WITH last_month AS (
    SELECT DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AS start_date,
           DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 second' AS end_date
)
SELECT 
    p.name AS "Наименование товара",
    c_top.name AS "Категория 1-го уровня",
    SUM(oi.quantity) AS "Общее количество проданных штук",
    SUM(oi.item_total) AS "Общая выручка"
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
CROSS JOIN last_month lm
-- Получение категории первого уровня через рекурсивный запрос
LEFT JOIN LATERAL (
    WITH RECURSIVE category_hierarchy AS (
        SELECT id, parent_id, name
        FROM categories 
        WHERE id = p.category_id
        UNION ALL
        SELECT c2.id, c2.parent_id, c2.name
        FROM categories c2
        JOIN category_hierarchy ch ON c2.id = ch.parent_id
    )
    SELECT name
    FROM category_hierarchy
    WHERE parent_id IS NULL
    LIMIT 1
) c_top ON TRUE
WHERE o.order_date >= lm.start_date 
    AND o.order_date <= lm.end_date
    AND o.status NOT IN ('cancelled', 'returned')
GROUP BY p.id, p.name, c_top.name
ORDER BY "Общее количество проданных штук" DESC
LIMIT 5;

-- Запуск отчета
SELECT * FROM v_top_products_last_month;
```

