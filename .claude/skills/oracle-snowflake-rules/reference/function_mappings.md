# Oracle to Snowflake Function Mappings

Complete reference for converting Oracle functions to Snowflake equivalents.

## Table of Contents
- [NULL Handling](#null-handling)
- [String Functions](#string-functions)
- [Date & Time Functions](#date--time-functions)
- [Numeric Functions](#numeric-functions)
- [Conversion Functions](#conversion-functions)
- [Conditional Functions](#conditional-functions)
- [Aggregate Functions](#aggregate-functions)
- [Analytical Functions](#analytical-functions)

---

## NULL Handling

| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `NVL(expr1, expr2)` | `COALESCE(expr1, expr2)` | COALESCE is ANSI standard |
| `NVL2(expr, val1, val2)` | `IFF(expr IS NOT NULL, val1, val2)` | Or use CASE WHEN |
| `NULLIF(expr1, expr2)` | `NULLIF(expr1, expr2)` | Same in both |

**Examples:**
```sql
-- Oracle
SELECT NVL(commission, 0) FROM sales;
SELECT NVL2(manager_id, 'Has Manager', 'No Manager') FROM employees;

-- Snowflake
SELECT COALESCE(commission, 0) FROM sales;
SELECT IFF(manager_id IS NOT NULL, 'Has Manager', 'No Manager') FROM employees;
```

---

## String Functions

| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `SUBSTR(str, pos, len)` | `SUBSTR(str, pos, len)` | Same in both |
| `INSTR(str, substr)` | `POSITION(substr IN str)` | Different syntax |
| `LENGTH(str)` | `LENGTH(str)` | Same in both |
| `UPPER(str)` | `UPPER(str)` | Same in both |
| `LOWER(str)` | `LOWER(str)` | Same in both |
| `TRIM(str)` | `TRIM(str)` | Same in both |
| `LTRIM(str)` | `LTRIM(str)` | Same in both |
| `RTRIM(str)` | `RTRIM(str)` | Same in both |
| `LPAD(str, len, pad)` | `LPAD(str, len, pad)` | Same in both |
| `RPAD(str, len, pad)` | `RPAD(str, len, pad)` | Same in both |
| `REPLACE(str, old, new)` | `REPLACE(str, old, new)` | Same in both |
| `TRANSLATE(str, from, to)` | `TRANSLATE(str, from, to)` | Same in both |
| `CONCAT(str1, str2)` | `CONCAT(str1, str2)` | Or use \|\| operator |
| `str1 \|\| str2` | `str1 \|\| str2` | Concatenation - same |

**Examples:**
```sql
-- Oracle
SELECT INSTR('hello world', 'world') FROM dual;
SELECT SUBSTR(name, 1, 10) FROM customers;

-- Snowflake
SELECT POSITION('world' IN 'hello world');
SELECT SUBSTR(name, 1, 10) FROM customers;
```

---

## Date & Time Functions

| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `SYSDATE` | `CURRENT_TIMESTAMP()` | Oracle returns DATE, Snowflake returns TIMESTAMP |
| `SYSTIMESTAMP` | `CURRENT_TIMESTAMP()` | Same function in Snowflake |
| `CURRENT_DATE` | `CURRENT_DATE()` | Note parentheses in Snowflake |
| `TRUNC(date)` | `DATE_TRUNC('DAY', date)` | Different syntax |
| `TRUNC(date, 'MONTH')` | `DATE_TRUNC('MONTH', date)` | Argument order reversed |
| `TRUNC(date, 'YEAR')` | `DATE_TRUNC('YEAR', date)` | Argument order reversed |
| `ADD_MONTHS(date, n)` | `DATEADD(MONTH, n, date)` | Different function name |
| `MONTHS_BETWEEN(d1, d2)` | `DATEDIFF(MONTH, d2, d1)` | Note argument order! |
| `EXTRACT(YEAR FROM date)` | `EXTRACT(YEAR FROM date)` | Same in both |
| `EXTRACT(MONTH FROM date)` | `EXTRACT(MONTH FROM date)` | Same in both |
| `TO_DATE(str, fmt)` | `TO_DATE(str, fmt)` | Mostly same, check format codes |
| `TO_CHAR(date, fmt)` | `TO_CHAR(date, fmt)` | Mostly same, check format codes |
| `LAST_DAY(date)` | `LAST_DAY(date)` | Same in both |
| `NEXT_DAY(date, day)` | No direct equivalent | Use DATEADD with logic |

**Important Notes:**
- **MONTHS_BETWEEN**: Arguments are reversed! `MONTHS_BETWEEN(d1, d2)` → `DATEDIFF(MONTH, d2, d1)`
- **Date arithmetic**: Oracle allows `date + 1` for adding days. Snowflake prefers `DATEADD(DAY, 1, date)`
- **Julian dates**: Oracle's `TO_DATE(number, 'J')` has no direct Snowflake equivalent

**Examples:**
```sql
-- Oracle
SELECT SYSDATE FROM dual;
SELECT TRUNC(created_date) FROM orders;
SELECT ADD_MONTHS(start_date, 3) FROM contracts;
SELECT MONTHS_BETWEEN(end_date, start_date) FROM contracts;

-- Snowflake
SELECT CURRENT_TIMESTAMP();
SELECT DATE_TRUNC('DAY', created_date) FROM orders;
SELECT DATEADD(MONTH, 3, start_date) FROM contracts;
SELECT DATEDIFF(MONTH, start_date, end_date) FROM contracts;
```

**Date Format Codes:**
Most Oracle date format codes work in Snowflake, but verify these:
- `YYYY`, `MM`, `DD` - Same
- `HH24`, `MI`, `SS` - Same
- `J` (Julian) - Not supported in Snowflake

---

## Numeric Functions

| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `ROUND(num, dec)` | `ROUND(num, dec)` | Same in both |
| `TRUNC(num, dec)` | `TRUNC(num, dec)` | Same in both |
| `CEIL(num)` | `CEIL(num)` | Same in both |
| `FLOOR(num)` | `FLOOR(num)` | Same in both |
| `MOD(m, n)` | `MOD(m, n)` | Same in both |
| `ABS(num)` | `ABS(num)` | Same in both |
| `SIGN(num)` | `SIGN(num)` | Same in both |
| `POWER(m, n)` | `POWER(m, n)` | Same in both |
| `SQRT(num)` | `SQRT(num)` | Same in both |
| `EXP(num)` | `EXP(num)` | Same in both |
| `LN(num)` | `LN(num)` | Same in both |
| `LOG(base, num)` | `LOG(base, num)` | Same in both |

**Examples:**
```sql
-- Same in both Oracle and Snowflake
SELECT ROUND(price, 2) FROM products;
SELECT TRUNC(amount, 0) FROM transactions;
```

---

## Conversion Functions

| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `TO_CHAR(num)` | `TO_CHAR(num)` | Same in both |
| `TO_CHAR(date, fmt)` | `TO_CHAR(date, fmt)` | Same in both |
| `TO_NUMBER(str)` | `TO_NUMBER(str)` | Same in both |
| `TO_DATE(str, fmt)` | `TO_DATE(str, fmt)` | Same in both |
| `CAST(expr AS type)` | `CAST(expr AS type)` | Same in both |
| `CONVERT(type, expr)` | `TRY_CAST(expr AS type)` | TRY_CAST returns NULL on error |

**Examples:**
```sql
-- Oracle
SELECT TO_CHAR(123.45) FROM dual;
SELECT TO_NUMBER('123.45') FROM dual;
SELECT CAST(price AS NUMBER(10,2)) FROM products;

-- Snowflake (same)
SELECT TO_CHAR(123.45);
SELECT TO_NUMBER('123.45');
SELECT CAST(price AS NUMBER(10,2)) FROM products;
```

---

## Conditional Functions

| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `DECODE(expr, val1, res1, val2, res2, default)` | `CASE WHEN expr=val1 THEN res1 WHEN expr=val2 THEN res2 ELSE default END` | CASE is standard |
| `CASE WHEN ... END` | `CASE WHEN ... END` | Same in both |
| `GREATEST(val1, val2, ...)` | `GREATEST(val1, val2, ...)` | Same in both |
| `LEAST(val1, val2, ...)` | `LEAST(val1, val2, ...)` | Same in both |

**DECODE Translation:**
```sql
-- Oracle
SELECT DECODE(status, 'A', 'Active', 'I', 'Inactive', 'Unknown') FROM accounts;

-- Snowflake
SELECT CASE
  WHEN status = 'A' THEN 'Active'
  WHEN status = 'I' THEN 'Inactive'
  ELSE 'Unknown'
END FROM accounts;

-- Alternative using IFF (for simple cases)
SELECT IFF(status = 'A', 'Active', 'Inactive') FROM accounts;
```

---

## Aggregate Functions

| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `COUNT(*)` | `COUNT(*)` | Same in both |
| `SUM(expr)` | `SUM(expr)` | Same in both |
| `AVG(expr)` | `AVG(expr)` | Same in both |
| `MIN(expr)` | `MIN(expr)` | Same in both |
| `MAX(expr)` | `MAX(expr)` | Same in both |
| `STDDEV(expr)` | `STDDEV(expr)` | Same in both |
| `VARIANCE(expr)` | `VARIANCE(expr)` | Same in both |
| `LISTAGG(expr, delim)` | `LISTAGG(expr, delim)` | Same in both |

**Examples:**
```sql
-- Same in both Oracle and Snowflake
SELECT
  COUNT(*) as total,
  SUM(amount) as total_amount,
  AVG(amount) as avg_amount
FROM transactions;
```

---

## Analytical Functions

| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `ROW_NUMBER() OVER (...)` | `ROW_NUMBER() OVER (...)` | Same in both |
| `RANK() OVER (...)` | `RANK() OVER (...)` | Same in both |
| `DENSE_RANK() OVER (...)` | `DENSE_RANK() OVER (...)` | Same in both |
| `LAG(expr, offset) OVER (...)` | `LAG(expr, offset) OVER (...)` | Same in both |
| `LEAD(expr, offset) OVER (...)` | `LEAD(expr, offset) OVER (...)` | Same in both |
| `FIRST_VALUE(expr) OVER (...)` | `FIRST_VALUE(expr) OVER (...)` | Same in both |
| `LAST_VALUE(expr) OVER (...)` | `LAST_VALUE(expr) OVER (...)` | Same in both |

**ROWNUM Replacement:**
```sql
-- Oracle
SELECT * FROM contracts WHERE ROWNUM <= 10;

-- Snowflake
SELECT * FROM contracts
QUALIFY ROW_NUMBER() OVER (ORDER BY contract_id) <= 10;

-- Or with LIMIT
SELECT * FROM contracts ORDER BY contract_id LIMIT 10;
```

---

## Special Oracle Constructs

### DUAL Table
```sql
-- Oracle
SELECT SYSDATE FROM dual;

-- Snowflake (no FROM clause needed for expressions)
SELECT CURRENT_TIMESTAMP();
```

### Sequences
```sql
-- Oracle
SELECT contract_seq.NEXTVAL FROM dual;

-- Snowflake (same)
SELECT contract_seq.NEXTVAL;
```

### Pseudo-Columns
| Oracle | Snowflake | Notes |
|--------|-----------|-------|
| `ROWNUM` | `ROW_NUMBER() OVER (ORDER BY ...)` | Must specify ordering |
| `ROWID` | No equivalent | Snowflake doesn't have ROWID |
| `LEVEL` (in CONNECT BY) | Use recursive CTE | Different approach |

---

## Common Patterns

### Pattern 1: NULL with Arithmetic
```sql
-- Oracle
SELECT quantity * NVL(price, 0) FROM orders;

-- Snowflake
SELECT quantity * COALESCE(price, 0) FROM orders;
```

### Pattern 2: Date Comparison
```sql
-- Oracle
WHERE TRUNC(created_date) = TRUNC(SYSDATE)

-- Snowflake
WHERE DATE_TRUNC('DAY', created_date) = DATE_TRUNC('DAY', CURRENT_TIMESTAMP())
```

### Pattern 3: String Search
```sql
-- Oracle
WHERE INSTR(description, 'error') > 0

-- Snowflake
WHERE POSITION('error' IN description) > 0
-- Or using CONTAINS
WHERE CONTAINS(description, 'error')
```

### Pattern 4: Conditional Aggregation
```sql
-- Oracle
SELECT SUM(DECODE(status, 'A', amount, 0)) FROM transactions;

-- Snowflake
SELECT SUM(CASE WHEN status = 'A' THEN amount ELSE 0 END) FROM transactions;
-- Or using IFF
SELECT SUM(IFF(status = 'A', amount, 0)) FROM transactions;
```

---

## Functions to Avoid / Not Supported

These Oracle functions have no direct Snowflake equivalent:

- `CONNECT BY` - Use recursive CTEs instead
- `ROWID` - No concept in Snowflake
- `DBMS_*` packages - Use Snowflake equivalents or stored procedures
- Oracle-specific types (e.g., `XMLTYPE`, `SDO_GEOMETRY`) - Use Snowflake types
- `MERGE` statement - Supported in Snowflake but syntax differs

---

## Performance Considerations

1. **Window functions**: Snowflake executes window functions efficiently. Use them instead of self-joins.
2. **QUALIFY clause**: Snowflake's QUALIFY is more efficient than subqueries for filtering window function results.
3. **COALESCE vs NVL**: COALESCE is ANSI standard and performs the same in Snowflake.

---

## Quick Reference Summary

**Most Common Translations:**
- `NVL` → `COALESCE`
- `DECODE` → `CASE WHEN`
- `SYSDATE` → `CURRENT_TIMESTAMP()`
- `TRUNC(date)` → `DATE_TRUNC('DAY', date)`
- `ADD_MONTHS` → `DATEADD`
- `MONTHS_BETWEEN` → `DATEDIFF` (reversed args!)
- `INSTR` → `POSITION`
- `ROWNUM` → `ROW_NUMBER() OVER` or `LIMIT`
- `(+)` → `LEFT/RIGHT JOIN`
- `FROM dual` → (omit FROM clause)
