# Julian Date Handling in EKIP Tables

## CRITICAL: Julian Date Detection

**99% of date fields in EKIP tables are stored as Julian dates (NUMBER type), not standard DATE types.**

---

## Detection Rule

**A column is a Julian date if:**
1. Column name contains "DATE" (case-insensitive)
2. DATA_TYPE = "NUMBER" (in `config/tables_columns_info.csv`)
3. Table is from EKIP schema

**Verification Source:** `config/tables_columns_info.csv`

---

## Julian Date Count

**Total Julian date columns:** 159+ across all EKIP tables

**Common patterns:**
- `DATE_CREATION` (NUMBER)
- `DATE_MODIFICATION` (NUMBER)
- `DATE_STATUT` (NUMBER)
- `DATE_ARRETE` (NUMBER)
- `DATE_COMPTABLE` (NUMBER)
- `DATE_FIN` (NUMBER)
- `DATE_DEBUT` (NUMBER)
- All `DATE_*` columns in EKIP tables

---

## Conversion Formula

### Standard Conversion

```sql
DATEADD(DAY, julian_value - 2440588, '1970-01-01'::DATE)
```

**Explanation:**
- `2440588` = Julian day number for Unix epoch (1970-01-01)
- Subtracts epoch to get days since 1970-01-01
- Adds those days to epoch date

### Handle Zero/Null Values

Some Julian dates use `0` to represent NULL:

```sql
CASE
    WHEN julian_value = 0 THEN NULL
    ELSE DATEADD(DAY, julian_value - 2440588, '1970-01-01'::DATE)
END as converted_date
```

**Common in:** `HISTOSTAT.DATE_STATUT`, `AFFAIRE.DATE_MODIFICATION`

### Handle Already-Converted Dates

If source already has proper dates (rare in EKIP):

```sql
-- Check DATA_TYPE in tables_columns_info.csv
-- If DATA_TYPE = 'DATE' or 'TIMESTAMP_NTZ', do NOT convert
```

---

## Examples from tables_columns_info.csv

### EKIP_AFFAIRE

```csv
TABLE_NAME,ROW_COUNT,COLUMN_NAME,DATA_TYPE,ORDINAL_POSITION,IS_NULLABLE
EKIP_AFFAIRE,1280795,DATE_CREATION,NUMBER,40,YES
EKIP_AFFAIRE,1280795,DATE_MODIFICATION,NUMBER,41,YES
EKIP_AFFAIRE,1280795,DATE_SIGNATURE,NUMBER,116,YES
EKIP_AFFAIRE,1280795,DATE_FIN,NUMBER,117,YES
EKIP_AFFAIRE,1280795,DATE_MEL,NUMBER,118,YES
EKIP_AFFAIRE,1280795,DATE_RESILIATION,NUMBER,121,YES
```

**All these must be converted!**

### EKIP_HISTOSTAT

```csv
EKIP_HISTOSTAT,24819719,DATE_STATUT,NUMBER,5,YES
EKIP_HISTOSTAT,24819719,DATE_CREATION,NUMBER,10,YES
```

**Special handling:** `DATE_STATUT` can be `0` (represents NULL)

### EKIP_ARRAFF

```csv
EKIP_ARRAFF,48767520,DATE_ARRETE,NUMBER,3,YES
EKIP_ARRAFF,48767520,DATE_MEL,NUMBER,14,YES
EKIP_ARRAFF,48767520,DATE_CONTENTIEUX,NUMBER,15,YES
```

---

## DBT Model Conversion Examples

### Example 1: Basic Conversion

**Pentaho SQL:**
```sql
SELECT
    ID_AFFAIRE,
    DATE_CREATION,
    DATE_FIN
FROM ${EKIP_SCHEMA}.AFFAIRE
```

**DBT Model (CORRECT):**
```sql
select
    id_affaire,
    dateadd(day, date_creation - 2440588, '1970-01-01'::date) as date_creation,
    dateadd(day, date_fin - 2440588, '1970-01-01'::date) as date_fin
from {{ source('ekip', 'EKIP_AFFAIRE') }}
```

**DBT Model (WRONG):**
```sql
select
    id_affaire,
    date_creation,  -- ❌ Wrong! This is a Julian number, not a date
    date_fin        -- ❌ Wrong! This is a Julian number, not a date
from {{ source('ekip', 'EKIP_AFFAIRE') }}
```

### Example 2: With NULL Handling

```sql
select
    id_affaire,
    case
        when date_statut = 0 then null
        else dateadd(day, date_statut - 2440588, '1970-01-01'::date)
    end as date_statut
from {{ source('ekip', 'EKIP_HISTOSTAT') }}
```

### Example 3: Preserve Julian for Joins

If you need to join on Julian dates with other tables that also use Julian:

```sql
with source_data as (
    select
        id_affaire,
        date_arrete,  -- Keep as Julian NUMBER for join
        dateadd(day, date_arrete - 2440588, '1970-01-01'::date) as date_arrete_converted
    from {{ source('ekip', 'EKIP_ARRAFF') }}
),

periods as (
    select
        no_periode,
        date_finval  -- Also Julian NUMBER
    from {{ source('ekip', 'EKIP_PERIODE') }}
),

joined as (
    select
        s.id_affaire,
        s.date_arrete_converted,  -- Use converted date for output
        p.no_periode
    from source_data s
    left join periods p
        on s.date_arrete = p.date_finval  -- Join on Julian numbers
)

select * from joined
```

### Example 4: Date Filtering

**Filtering by date variable:**

```sql
where
    dateadd(day, date_creation - 2440588, '1970-01-01'::date)
        >= to_date('{{ var("ekip_history_initial_date") }}', 'YYYY-MM-DD')
```

**Or convert variable to Julian for comparison:**

```sql
where
    date_creation >= to_number(to_char(to_date('{{ var("ekip_history_initial_date") }}', 'YYYY-MM-DD'), 'J')) - 2440588 + 2440588
```

---

## Agent Requirements

### When Analyzing Pentaho SQL (pentaho-analyzer)

1. **Read** `config/tables_columns_info.csv`
2. **Identify** all Julian date columns (column name contains "DATE", DATA_TYPE = "NUMBER")
3. **Flag** in analysis metadata:
   ```json
   {
     "table": "EKIP_AFFAIRE",
     "column": "DATE_CREATION",
     "data_type": "NUMBER",
     "is_julian_date": true,
     "requires_conversion": true
   }
   ```

### When Translating SQL (sql-translator)

1. **Read** `config/tables_columns_info.csv`
2. **Auto-detect** Julian date columns
3. **Apply conversion formula** automatically:
   ```sql
   CASE
       WHEN {column} = 0 THEN NULL
       ELSE DATEADD(DAY, {column} - 2440588, '1970-01-01'::DATE)
   END as {column}
   ```
4. **Preserve Julian values** if:
   - Column used in JOIN conditions
   - Column compared with other Julian dates
   - Create separate `{column}_julian` and `{column}_converted` columns

### When Generating DBT Models (dbt-model-generator)

1. **Read** `config/tables_columns_info.csv`
2. **Verify** all Julian dates are converted
3. **Add comments** for Julian date conversions:
   ```sql
   -- Julian date conversion: DATE_CREATION (NUMBER) → DATE
   dateadd(day, date_creation - 2440588, '1970-01-01'::date) as date_creation
   ```
4. **Test** date columns have proper types

---

## Validation Checklist

Before deploying DBT models with EKIP data:

- [ ] Read `config/tables_columns_info.csv` for column metadata
- [ ] Identify all columns with "DATE" in name and DATA_TYPE = "NUMBER"
- [ ] Apply Julian date conversion to all identified columns
- [ ] Handle zero values (convert to NULL)
- [ ] Preserve Julian values for joins if needed
- [ ] Add comments documenting Julian conversions
- [ ] Test date filtering works correctly
- [ ] Validate date ranges are reasonable (not in year 1970 or 5000+)

---

## Common Mistakes

1. ❌ **Not converting Julian dates**
   ```sql
   select date_creation from {{ source('ekip', 'EKIP_AFFAIRE') }}
   -- Result: 2459580 (Julian number, not a date)
   ```

2. ❌ **Using wrong formula**
   ```sql
   to_date(date_creation)  -- Wrong! Julian dates need special conversion
   ```

3. ❌ **Ignoring zero values**
   ```sql
   dateadd(day, date_statut - 2440588, '1970-01-01'::date)
   -- Result: 1969-01-03 (when date_statut = 0, should be NULL)
   ```

4. ❌ **Converting non-Julian dates**
   ```sql
   -- Check tables_columns_info.csv first!
   -- s3_ingestion_timestamp is TIMESTAMP_NTZ, not Julian
   dateadd(day, s3_ingestion_timestamp - 2440588, '1970-01-01'::date)  -- Wrong!
   ```

---

## Testing Julian Date Conversions

### Sample Test Queries

```sql
-- Test 1: Verify conversion produces reasonable dates
select
    date_creation as julian_value,
    dateadd(day, date_creation - 2440588, '1970-01-01'::date) as converted_date,
    year(converted_date) as year_value
from {{ source('ekip', 'EKIP_AFFAIRE') }}
where date_creation is not null
limit 10;

-- Expected: year_value between 1990-2025

-- Test 2: Check for zero dates
select
    count(*) as zero_date_count
from {{ source('ekip', 'EKIP_HISTOSTAT') }}
where date_statut = 0;

-- Test 3: Validate date range
select
    min(dateadd(day, date_creation - 2440588, '1970-01-01'::date)) as min_date,
    max(dateadd(day, date_creation - 2440588, '1970-01-01'::date)) as max_date
from {{ source('ekip', 'EKIP_AFFAIRE') }}
where date_creation > 0;

-- Expected: min_date around 1990-2000, max_date around current year
```

---

## Reference

- **Column metadata:** `config/tables_columns_info.csv`
- **Julian day calculation:** https://en.wikipedia.org/wiki/Julian_day
- **Unix epoch:** 1970-01-01 = Julian day 2440588

**CRITICAL:** Always check `tables_columns_info.csv` to determine if a date column is Julian (NUMBER) or standard (DATE/TIMESTAMP).
