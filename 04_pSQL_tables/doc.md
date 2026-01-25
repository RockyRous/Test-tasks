# Документация по проектированию и оптимизации базы данных ERP системы учета заказов

## 1. Обоснование проектирования БД

### 1.1. Архитектурные решения

**Иерархия категорий**
Выбран подход **Path Enumeration** (поле `path`) вместо Nested Sets по следующим причинам:
- Проще в реализации и поддержке
- Легко читается и отлаживается
- Поддерживает неограниченный уровень вложенности
- Эффективен для частых запросов вверх/вниз по иерархии
- Добавлен индекс `idx_categories_path` для быстрого поиска

**Ограничения и проверки:**
- `CHECK (price >= 0)` - защита от отрицательных цен
- `CHECK (quantity >= 0)` - запрет отрицательного количества
- `CHECK (discount_rate BETWEEN 0 AND 100)` - контроль диапазона скидок
- Внешние ключи с каскадными операциями для целостности данных

### 1.2. Оптимизация производительности

**Индексы:**
1. **B-tree индексы** для точных совпадений (первичные ключи, внешние ключи)
2. **Частичные индексы** для фильтрации активных записей:
   - `idx_products_active WHERE is_active = TRUE`
   - `idx_orders_active WHERE status IN ('new', 'processing')`
3. **Составные индексы** для часто используемых комбинаций:
   - `idx_products_category_active` для фильтрации по категории + активность
   - `idx_orders_customer_date` для истории заказов клиента

**Генерируемые столбцы:**
- `available_quantity` - автоматический расчет доступного количества
- `final_amount` - итоговая сумма заказа с учетом скидок и налогов
- `item_total` - сумма позиции заказа

### 1.3. Целостность данных

**Триггерная система:**
1. **Автоматическое обновление timestamps** - `update_updated_at_column()`
2. **Синхронизация сумм заказов** - `update_order_total()`
3. **Управление резервами товаров** - `update_product_reserve()`
4. **Логирование изменений цен** - `log_price_change()`
5. **Обновление путей категорий** - `update_category_path()`

## 2. Соответствие Требованиям

### 2.1. Номенклатура (products)
**Наименование** - поле `name VARCHAR(500) NOT NULL`
**Количество** - поля `quantity`, `reserved_quantity`, `available_quantity`
**Цена** - поле `price NUMERIC(15,2)` с историей в `price_history`

### 2.2. Каталог номенклатуры (categories)
**Неограниченная вложенность** - рекурсивная структура с `parent_id`
**Иерархическое хранение** - поля `path` и `level` для быстрого доступа
**Гибкое добавление** - можно добавлять категории любого уровня

**Пример соответствия структуре из ТЗ:**
```
Бытовая техника (id=1, parent_id=NULL, path='1', level=0)
  ├─ Стиральные машины (id=4, parent_id=1, path='1>4', level=1)
  ├─ Холодильники (id=5, parent_id=1, path='1>5', level=1)
  │     ├─ Однокамерные (id=10, parent_id=5, path='1>5>10', level=2)
  │     └─ Двухкамерные (id=11, parent_id=5, path='1>5>11', level=2)
  └─ Телевизоры (id=6, parent_id=1, path='1>6', level=1)
```

### 2.3. Клиенты (customers)
**Наименование** - поля `name`, `legal_name`
**Адрес** - поля `address`, `city`, `country`, `postal_code`
**Контактная информация** - `email`, `phone`, `phone_secondary`

### 2.4. Заказы покупателей (orders + order_items)
**Разный набор товаров** - таблица `order_items` связывает заказы с товарами
**Гибкая конфигурация** - можно добавлять любое количество позиций
**Автоматический расчет** - суммы пересчитываются триггерами


Данная архитектура обеспечивает:
- ✅ Полное соответствие требованиям ТЗ
- ✅ Высокую производительность при росте данных
- ✅ Гибкость для будущих изменений
- ✅ Простота администрирования и поддержки

---

### Анализ и оптимизация запроса

**Текущие проблемы производительности:**
1. **Рекурсивный запрос в LATERAL JOIN** - вычисляется для каждой строки
2. **Агрегация по большому объему данных** - все заказы за месяц
3. **Отсутствие индекса для временных диапазонов** - фильтрация по `order_date`
4. **JOIN через несколько таблиц** - 4 таблицы для одного отчета

**Предлагаемые оптимизации:**

**1. Добавить материализованное представление с ежедневным обновлением:**
```sql
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT 
    DATE(o.order_date) AS sale_date,
    oi.product_id,
    p.category_id,
    SUM(oi.quantity) AS daily_quantity,
    SUM(oi.item_total) AS daily_revenue
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status NOT IN ('cancelled', 'returned')
GROUP BY DATE(o.order_date), oi.product_id, p.category_id;

CREATE UNIQUE INDEX idx_mv_daily_sales ON mv_daily_sales (sale_date, product_id);
CREATE INDEX idx_mv_daily_sales_date ON mv_daily_sales (sale_date DESC);
CREATE INDEX idx_mv_daily_sales_product ON mv_daily_sales (product_id);

-- Ежедневное обновление через задание cron
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales;
```

**2. Добавить столбец "первая категория" в таблицу products:**
```sql
-- Добавляем denormalized поле для быстрого доступа
ALTER TABLE products ADD COLUMN top_category_id BIGINT;
ALTER TABLE products ADD CONSTRAINT fk_products_top_category 
    FOREIGN KEY (top_category_id) REFERENCES categories(id);

-- Обновляем данные триггером при изменении категории
CREATE OR REPLACE FUNCTION update_product_top_category()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.category_id IS DISTINCT FROM OLD.category_id THEN
        WITH RECURSIVE category_path AS (
            SELECT id, parent_id
            FROM categories 
            WHERE id = NEW.category_id
            UNION ALL
            SELECT c2.id, c2.parent_id
            FROM categories c2
            JOIN category_path cp ON c2.id = cp.parent_id
        )
        SELECT id INTO NEW.top_category_id
        FROM category_path
        WHERE parent_id IS NULL
        LIMIT 1;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_top_category
    BEFORE INSERT OR UPDATE OF category_id ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_top_category();
```

**3. Оптимизированный запрос с использованием подготовленных данных:**
```sql
-- Создаем индекс для временных запросов
CREATE INDEX idx_orders_date_status ON orders(order_date, status) 
WHERE status NOT IN ('cancelled', 'returned');

-- Оптимизированный запрос отчета
SELECT 
    p.name AS "Наименование товара",
    c_top.name AS "Категория 1-го уровня",
    SUM(oi.quantity) AS "Общее количество проданных штук"
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
JOIN categories c_top ON p.top_category_id = c_top.id  -- Быстрый доступ без рекурсии
WHERE o.order_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
    AND o.order_date < DATE_TRUNC('month', CURRENT_DATE)
    AND o.status NOT IN ('cancelled', 'returned')
GROUP BY p.id, p.name, c_top.id, c_top.name
ORDER BY SUM(oi.quantity) DESC
LIMIT 5;
```

**4. Кэширование через Redis для часто запрашиваемых отчетов:**
```sql
-- Функция для получения отчета с кэшированием
CREATE OR REPLACE FUNCTION get_cached_top_products()
RETURNS JSON AS $$
DECLARE
    cache_key TEXT := 'top_products_' || DATE_TRUNC('month', CURRENT_DATE);
    cached_result JSON;
BEGIN
    -- Попытка получить из кэша (псевдокод)
    -- SELECT value INTO cached_result FROM redis_cache WHERE key = cache_key;
    
    IF cached_result IS NULL THEN
        -- Выполняем запрос и кэшируем на 1 час
        SELECT json_agg(row_to_json(t)) INTO cached_result
        FROM (
            SELECT * FROM v_top_products_last_month
        ) t;
        
        -- INSERT INTO redis_cache (key, value, expires_at) 
        -- VALUES (cache_key, cached_result, NOW() + INTERVAL '1 hour');
    END IF;
    
    RETURN cached_result;
END;
$$ LANGUAGE plpgsql;
```

### Тестовые запросы
```sql
-- Проверка работы системы
SELECT * FROM v_available_products;
SELECT * FROM v_active_orders;
SELECT * FROM get_top_products_last_month(5);

-- Мониторинг производительности
SELECT * FROM pg_stat_user_tables;
EXPLAIN ANALYZE SELECT * FROM v_top_products_last_month;
```

### Ежедневное обслуживание
```sql
-- Обновление материализованных представлений (запускать по расписанию)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_products_monthly;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_monthly_stats;

-- Сбор статистики для оптимизатора
ANALYZE orders;
ANALYZE order_items;
ANALYZE products;
```