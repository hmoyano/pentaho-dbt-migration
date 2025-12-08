# Julian Date Handling (Consolidated)

**CRITICAL**: 99% of date fields in EKIP tables are Julian dates (NUMBER type).

---

## Detection Rule

A column is Julian date if:
1. Column name contains "DATE"
2. DATA_TYPE = "NUMBER" in `config/tables_columns_info.csv`
3. Table is from EKIP schema

**Total: 159+ Julian date columns**

---

## Conversion Formula

```sql
CASE
    WHEN julian_value = 0 THEN NULL
    ELSE DATEADD(DAY, julian_value - 2440588, '1970-01-01'::DATE)
END as converted_date
```

**Key constant**: `2440588` = Julian day for Unix epoch (1970-01-01)

---

## Common Julian Columns

- `DATE_CREATION` (NUMBER)
- `DATE_MODIFICATION` (NUMBER)
- `DATE_STATUT` (NUMBER)
- `DATE_ARRETE` (NUMBER)
- `DATE_FIN` (NUMBER)
- `DATE_DEBUT` (NUMBER)

---

## DBT Model Examples

### Basic Conversion
```sql
select
    id_affaire,
    dateadd(day, date_creation - 2440588, '1970-01-01'::date) as date_creation
from {{ source('ekip', 'EKIP_AFFAIRE') }}
```

### With NULL Handling (zero = NULL)
```sql
select
    case
        when date_statut = 0 then null
        else dateadd(day, date_statut - 2440588, '1970-01-01'::date)
    end as date_statut
from {{ source('ekip', 'EKIP_HISTOSTAT') }}
```

### Preserve Julian for Joins
```sql
with source_data as (
    select
        id_affaire,
        date_arrete,  -- Keep Julian for join
        dateadd(day, date_arrete - 2440588, '1970-01-01'::date) as date_arrete_converted
    from {{ source('ekip', 'EKIP_ARRAFF') }}
)
```

---

## Common Mistakes

```sql
-- WRONG: Not converting Julian date
select date_creation from source  -- Returns 2459580 (number)

-- WRONG: Using wrong formula
to_date(date_creation)  -- Fails

-- WRONG: Ignoring zero values
dateadd(day, date_statut - 2440588, '1970-01-01'::date)
-- Returns 1969-01-03 when date_statut = 0 (should be NULL)
```

---

## Validation

```sql
-- Test conversion produces reasonable dates
select
    date_creation as julian_value,
    dateadd(day, date_creation - 2440588, '1970-01-01'::date) as converted,
    year(converted) as year_value  -- Should be 1990-2025
from source
where date_creation > 0
limit 10;
```

---

## Reference

- **Column metadata**: `config/tables_columns_info.csv`
- **Formula**: `DATEADD(DAY, julian - 2440588, '1970-01-01'::DATE)`
- **Zero handling**: Convert to NULL

See full details in:
- `JULIAN_DATE_HANDLING.md` - Complete guide
- `JULIAN_DATE_FIX.md` - Fix documentation
