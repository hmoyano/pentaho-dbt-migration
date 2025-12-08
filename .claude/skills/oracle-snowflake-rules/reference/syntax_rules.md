# Oracle to Snowflake Syntax Translation Rules

This document covers Oracle-specific syntax patterns and their Snowflake equivalents.

## Table of Contents
- [Outer Join Operator (+)](#outer-join-operator-)
- [DUAL Table](#dual-table)
- [Date Arithmetic](#date-arithmetic)
- [ROWNUM Pseudo-Column](#rownum-pseudo-column)
- [Hierarchical Queries (CONNECT BY)](#hierarchical-queries-connect-by)
- [Sequences](#sequences)
- [MERGE Statement](#merge-statement)
- [Subquery Factoring (WITH Clause)](#subquery-factoring-with-clause)
- [String Literals](#string-literals)
- [Comments](#comments)

---

## Outer Join Operator (+)

Oracle's `(+)` operator for outer joins must be converted to ANSI SQL JOIN syntax.

### Left Outer Join

**Oracle:**
```sql
SELECT a.*, b.name
FROM orders a, customers b
WHERE a.customer_id = b.customer_id(+);
```

**Snowflake:**
```sql
SELECT a.*, b.name
FROM orders a
LEFT JOIN customers b ON a.customer_id = b.customer_id;
```

### Right Outer Join

**Oracle:**
```sql
SELECT a.*, b.name
FROM orders a, customers b
WHERE a.customer_id(+) = b.customer_id;
```

**Snowflake:**
```sql
SELECT a.*, b.name
FROM orders a
RIGHT JOIN customers b ON a.customer_id = b.customer_id;
```

### Multiple Table Outer Joins

**Oracle:**
```sql
SELECT a.*, b.name, c.description
FROM orders a, customers b, products c
WHERE a.customer_id = b.customer_id(+)
  AND a.product_id = c.product_id(+);
```

**Snowflake:**
```sql
SELECT a.*, b.name, c.description
FROM orders a
LEFT JOIN customers b ON a.customer_id = b.customer_id
LEFT JOIN products c ON a.product_id = c.product_id;
```

### Complex Outer Join Conditions

**Oracle:**
```sql
SELECT a.*, b.*
FROM table1 a, table2 b
WHERE a.id = b.id(+)
  AND b.status(+) = 'A'
  AND b.date(+) >= SYSDATE - 30;
```

**Snowflake:**
```sql
SELECT a.*, b.*
FROM table1 a
LEFT JOIN table2 b
  ON a.id = b.id
  AND b.status = 'A'
  AND b.date >= CURRENT_TIMESTAMP() - INTERVAL '30 days';
```

**Translation Rules:**
1. Identify which table has `(+)` - this becomes the "optional" side
2. If column has `(+)`, use LEFT JOIN (left table is preserved)
3. If multiple columns from same table have `(+)`, they all go in ON clause
4. Convert comma-separated FROM to explicit JOINs

---

## DUAL Table

Oracle's `DUAL` table is a dummy table for selecting expressions. Snowflake doesn't require it.

**Oracle:**
```sql
SELECT SYSDATE FROM dual;
SELECT 1 + 1 FROM dual;
SELECT seq.NEXTVAL FROM dual;
```

**Snowflake:**
```sql
SELECT CURRENT_TIMESTAMP();
SELECT 1 + 1;
SELECT seq.NEXTVAL;
```

**Translation Rule:**
Remove `FROM dual` entirely when selecting expressions that don't reference tables.

**Exception - When DUAL is Actually Needed:**
If the query needs to generate a single row result:
```sql
-- Oracle
SELECT 'Constant Value' as col FROM dual;

-- Snowflake (if you need exactly one row)
SELECT 'Constant Value' as col;
-- Or explicitly
SELECT 'Constant Value' as col FROM (SELECT 1);
```

---

## Date Arithmetic

Oracle and Snowflake handle date arithmetic differently.

### Adding/Subtracting Days

**Oracle:**
```sql
SELECT hire_date + 30 FROM employees;
SELECT hire_date - 7 FROM employees;
SELECT SYSDATE - hire_date FROM employees;  -- Returns number of days
```

**Snowflake:**
```sql
SELECT DATEADD(DAY, 30, hire_date) FROM employees;
SELECT DATEADD(DAY, -7, hire_date) FROM employees;
SELECT DATEDIFF(DAY, hire_date, CURRENT_TIMESTAMP()) FROM employees;
```

### Adding Months/Years

**Oracle:**
```sql
SELECT ADD_MONTHS(start_date, 3) FROM contracts;
SELECT ADD_MONTHS(start_date, -12) FROM contracts;
```

**Snowflake:**
```sql
SELECT DATEADD(MONTH, 3, start_date) FROM contracts;
SELECT DATEADD(YEAR, -1, start_date) FROM contracts;
```

### Date Truncation

**Oracle:**
```sql
SELECT TRUNC(hire_date) FROM employees;
SELECT TRUNC(hire_date, 'MONTH') FROM employees;
SELECT TRUNC(hire_date, 'YEAR') FROM employees;
```

**Snowflake:**
```sql
SELECT DATE_TRUNC('DAY', hire_date) FROM employees;
SELECT DATE_TRUNC('MONTH', hire_date) FROM employees;
SELECT DATE_TRUNC('YEAR', hire_date) FROM employees;
```

### Interval Literals

**Oracle:**
```sql
SELECT order_date + INTERVAL '5' DAY FROM orders;
SELECT order_date - INTERVAL '2' MONTH FROM orders;
```

**Snowflake:**
```sql
SELECT DATEADD(DAY, 5, order_date) FROM orders;
SELECT DATEADD(MONTH, -2, order_date) FROM orders;
-- Or using INTERVAL (Snowflake also supports this)
SELECT order_date + INTERVAL '5 days' FROM orders;
```

### Julian Date Conversion

**Oracle:**
```sql
SELECT TO_DATE(date_field, 'J') FROM table;
SELECT TO_CHAR(date_field, 'J') FROM table;
```

**Snowflake:**
```sql
-- No direct equivalent for Julian dates
-- Convert using formula: Julian - 2440588 = Unix epoch days
SELECT DATEADD(DAY, date_field - 2440588, '1970-01-01'::DATE) FROM table;
```

---

## ROWNUM Pseudo-Column

Oracle's `ROWNUM` is a pseudo-column that must be replaced with window functions or LIMIT.

### Simple ROWNUM

**Oracle:**
```sql
SELECT * FROM customers WHERE ROWNUM <= 10;
```

**Snowflake:**
```sql
SELECT * FROM customers LIMIT 10;
```

### ROWNUM with Ordering

**Oracle:**
```sql
SELECT * FROM
  (SELECT * FROM customers ORDER BY created_date DESC)
WHERE ROWNUM <= 10;
```

**Snowflake:**
```sql
SELECT * FROM customers
ORDER BY created_date DESC
LIMIT 10;

-- Or using QUALIFY
SELECT * FROM customers
QUALIFY ROW_NUMBER() OVER (ORDER BY created_date DESC) <= 10;
```

### ROWNUM in Subquery

**Oracle:**
```sql
SELECT a.*, b.rank_num
FROM customers a,
     (SELECT customer_id, ROWNUM as rank_num
      FROM customers
      ORDER BY revenue DESC) b
WHERE a.customer_id = b.customer_id;
```

**Snowflake:**
```sql
SELECT a.*,
       ROW_NUMBER() OVER (ORDER BY a.revenue DESC) as rank_num
FROM customers a;
```

### ROWNUM for Pagination

**Oracle:**
```sql
SELECT *
FROM (
  SELECT a.*, ROWNUM rnum
  FROM (SELECT * FROM customers ORDER BY customer_id) a
  WHERE ROWNUM <= 20
)
WHERE rnum >= 11;
```

**Snowflake:**
```sql
SELECT * FROM customers
ORDER BY customer_id
LIMIT 10 OFFSET 10;

-- Or using QUALIFY
SELECT * FROM customers
QUALIFY ROW_NUMBER() OVER (ORDER BY customer_id) BETWEEN 11 AND 20;
```

---

## Hierarchical Queries (CONNECT BY)

Oracle's `CONNECT BY` must be converted to recursive CTEs in Snowflake.

### Simple Hierarchy

**Oracle:**
```sql
SELECT employee_id, manager_id, level
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id;
```

**Snowflake:**
```sql
WITH RECURSIVE emp_hierarchy AS (
  -- Anchor: root nodes
  SELECT employee_id, manager_id, 1 as level
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive: children
  SELECT e.employee_id, e.manager_id, eh.level + 1
  FROM employees e
  INNER JOIN emp_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT * FROM emp_hierarchy;
```

### Hierarchy with Path

**Oracle:**
```sql
SELECT employee_id,
       manager_id,
       level,
       SYS_CONNECT_BY_PATH(employee_name, '/') as path
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id;
```

**Snowflake:**
```sql
WITH RECURSIVE emp_hierarchy AS (
  -- Anchor
  SELECT
    employee_id,
    manager_id,
    employee_name,
    1 as level,
    employee_name as path
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive
  SELECT
    e.employee_id,
    e.manager_id,
    e.employee_name,
    eh.level + 1,
    eh.path || '/' || e.employee_name
  FROM employees e
  INNER JOIN emp_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT * FROM emp_hierarchy;
```

### Hierarchy with Filtering

**Oracle:**
```sql
SELECT employee_id, manager_id
FROM employees
START WITH employee_id = 100
CONNECT BY PRIOR manager_id = employee_id;
```

**Snowflake:**
```sql
WITH RECURSIVE emp_hierarchy AS (
  -- Start from specific employee
  SELECT employee_id, manager_id, 1 as level
  FROM employees
  WHERE employee_id = 100

  UNION ALL

  -- Walk up the tree
  SELECT e.employee_id, e.manager_id, eh.level + 1
  FROM employees e
  INNER JOIN emp_hierarchy eh ON e.employee_id = eh.manager_id
)
SELECT * FROM emp_hierarchy;
```

---

## Sequences

Sequences work similarly in both databases, but with slight syntax differences.

### Creating Sequences

**Oracle:**
```sql
CREATE SEQUENCE order_seq
  START WITH 1
  INCREMENT BY 1
  NOCACHE;
```

**Snowflake:**
```sql
CREATE SEQUENCE order_seq
  START = 1
  INCREMENT = 1;
-- Note: Snowflake sequences are always cached
```

### Using Sequences

**Oracle:**
```sql
SELECT order_seq.NEXTVAL FROM dual;
SELECT order_seq.CURRVAL FROM dual;

INSERT INTO orders (order_id, ...)
VALUES (order_seq.NEXTVAL, ...);
```

**Snowflake:**
```sql
SELECT order_seq.NEXTVAL;
SELECT order_seq.CURRVAL;

INSERT INTO orders (order_id, ...)
VALUES (order_seq.NEXTVAL, ...);
```

**Note:** The usage is the same, just omit `FROM dual` in Snowflake.

---

## MERGE Statement

The MERGE statement has different syntax between Oracle and Snowflake.

**Oracle:**
```sql
MERGE INTO target t
USING source s
ON (t.id = s.id)
WHEN MATCHED THEN
  UPDATE SET t.value = s.value
WHEN NOT MATCHED THEN
  INSERT (id, value)
  VALUES (s.id, s.value);
```

**Snowflake:**
```sql
MERGE INTO target t
USING source s
ON t.id = s.id
WHEN MATCHED THEN
  UPDATE SET t.value = s.value
WHEN NOT MATCHED THEN
  INSERT (id, value)
  VALUES (s.id, s.value);
```

**Differences:**
- Oracle uses `ON (condition)` with parentheses
- Snowflake uses `ON condition` without parentheses
- Otherwise, syntax is very similar

---

## Subquery Factoring (WITH Clause)

Common Table Expressions (CTEs) work the same in both.

**Oracle:**
```sql
WITH
  regional_sales AS (
    SELECT region, SUM(amount) as total
    FROM orders
    GROUP BY region
  ),
  top_regions AS (
    SELECT region FROM regional_sales
    WHERE total > 1000000
  )
SELECT * FROM top_regions;
```

**Snowflake:**
```sql
-- Exact same syntax
WITH
  regional_sales AS (
    SELECT region, SUM(amount) as total
    FROM orders
    GROUP BY region
  ),
  top_regions AS (
    SELECT region FROM regional_sales
    WHERE total > 1000000
  )
SELECT * FROM top_regions;
```

**No translation needed** - CTEs use identical syntax.

---

## String Literals

### Standard String Literals

**Oracle and Snowflake (same):**
```sql
SELECT 'Hello World' FROM table;
SELECT 'It''s escaped' FROM table;  -- Double single-quote for escaping
```

### Alternative Quoting

**Oracle:**
```sql
SELECT q'[It's easier with Q notation]' FROM dual;
SELECT q'{Text with "quotes"}' FROM dual;
```

**Snowflake:**
```sql
-- Use standard escaping
SELECT 'It''s easier with escaping';
-- Or use double-dollar quoting
SELECT $$Text with "quotes"$$;
```

---

## Comments

Both databases support SQL comments the same way.

```sql
-- Single line comment (same in both)
SELECT * FROM table;

/* Multi-line comment
   works the same
   in both databases */
SELECT * FROM table;
```

---

## Hints

Oracle hints are ignored by Snowflake.

**Oracle:**
```sql
SELECT /*+ PARALLEL(8) */ * FROM large_table;
SELECT /*+ INDEX(t idx_name) */ * FROM table t;
```

**Snowflake:**
```sql
-- Hints are ignored, remove them
SELECT * FROM large_table;
SELECT * FROM table t;

-- Snowflake uses different performance tuning:
-- - Clustering keys
-- - Query optimization settings
-- - Warehouse sizing
```

**Translation Rule:**
Remove all Oracle hints (`/*+ ... */`). Snowflake has different optimization mechanisms.

---

## Table Aliases

### Oracle Allows Optional AS

**Oracle:**
```sql
SELECT * FROM customers c;
SELECT * FROM customers AS c;  -- Both valid
```

**Snowflake:**
```sql
SELECT * FROM customers c;
SELECT * FROM customers AS c;  -- Both valid
```

**No translation needed** - both syntaxes work in both databases.

---

## MINUS vs EXCEPT

**Oracle:**
```sql
SELECT id FROM table1
MINUS
SELECT id FROM table2;
```

**Snowflake:**
```sql
SELECT id FROM table1
EXCEPT
SELECT id FROM table2;
```

**Translation Rule:**
Replace `MINUS` with `EXCEPT`.

---

## INSERT ALL

Oracle's `INSERT ALL` has no direct Snowflake equivalent.

**Oracle:**
```sql
INSERT ALL
  INTO target1 VALUES (col1, col2)
  INTO target2 VALUES (col1, col3)
SELECT col1, col2, col3 FROM source;
```

**Snowflake:**
```sql
-- Use separate INSERT statements
INSERT INTO target1 SELECT col1, col2 FROM source;
INSERT INTO target2 SELECT col1, col3 FROM source;
```

---

## Common Translation Patterns

### Pattern 1: Comma Joins to ANSI Joins

**Oracle:**
```sql
SELECT a.*, b.*, c.*
FROM table1 a, table2 b, table3 c
WHERE a.id = b.id
  AND b.id = c.id
  AND a.status = 'A';
```

**Snowflake:**
```sql
SELECT a.*, b.*, c.*
FROM table1 a
INNER JOIN table2 b ON a.id = b.id
INNER JOIN table3 c ON b.id = c.id
WHERE a.status = 'A';
```

### Pattern 2: Subquery in FROM with ROWNUM

**Oracle:**
```sql
SELECT * FROM
  (SELECT a.*, ROWNUM rn FROM table a ORDER BY created_date)
WHERE rn <= 100;
```

**Snowflake:**
```sql
SELECT * FROM table
ORDER BY created_date
LIMIT 100;
```

### Pattern 3: Date Range Filters

**Oracle:**
```sql
WHERE TRUNC(created_date) BETWEEN
  TRUNC(SYSDATE - 30) AND TRUNC(SYSDATE);
```

**Snowflake:**
```sql
WHERE DATE_TRUNC('DAY', created_date) BETWEEN
  DATE_TRUNC('DAY', DATEADD(DAY, -30, CURRENT_TIMESTAMP()))
  AND DATE_TRUNC('DAY', CURRENT_TIMESTAMP());
```

---

## Quick Reference

**Most Common Syntax Changes:**
- `(+)` → `LEFT/RIGHT JOIN`
- `FROM dual` → (remove FROM clause)
- `date + n` → `DATEADD(DAY, n, date)`
- `ROWNUM` → `LIMIT` or `ROW_NUMBER() OVER`
- `CONNECT BY` → `WITH RECURSIVE`
- `TRUNC(date)` → `DATE_TRUNC('DAY', date)`
- `SYSDATE` → `CURRENT_TIMESTAMP()`
- `MINUS` → `EXCEPT`
- Remove `/*+ hints */`
