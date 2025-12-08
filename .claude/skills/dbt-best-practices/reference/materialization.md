# DBT Materialization Guide

Complete guide for choosing and detecting materialization strategies for DBT models.

---

## Quick Reference

### Team Convention (Simple Rule)

**Use `incremental` for everything EXCEPT reference/lookup tables.**

| Model Type | Materialization | Why |
|------------|----------------|-----|
| **Reference tables** (status, catalog, lookups) | `table` | Small, full refresh is fast |
| **Everything else** (transactions, dimensions, facts) | `incremental` | Efficient updates |

### By Layer

| Layer | Materialization | Notes |
|-------|----------------|-------|
| **Silver ADQ** (`stg_*`) | `incremental` | Lowercase columns, `merge` strategy |
| **Silver MAS** (`mas_*`) | `incremental` | UPPERCASE columns, `merge` strategy |
| **Gold Dimensions** (`d_*`) | `incremental` / `table` | Use `table` if < 1M rows |
| **Gold Facts** (`f_*`) | `incremental` | Usually `append` strategy |

---

## Intelligent Detection (Automatic)

**The system automatically detects materialization from Pentaho operations!**

Instead of guessing, we read what Pentaho actually does and map it to DBT.

### Detection Pipeline

```
Step 1: pentaho-parser     → Extracts operations from XML
Step 2: pentaho-analyzer   → Analyzes and recommends materialization
Step 3: dbt-model-generator → Uses recommendation to generate config
```

### Detection Rules

| Pentaho Operation | Detected As | DBT Materialization | Strategy |
|-------------------|-------------|---------------------|----------|
| TableOutput + `truncate=Y` | TRUNCATE_INSERT | `table` | N/A |
| TableOutput + `truncate=N` | APPEND | `incremental` | append |
| InsertUpdate step | MERGE | `incremental` | merge |
| Update step | UPDATE | `incremental` | merge |
| No operation found | NONE | `incremental` (fallback) | merge |

### Confidence Levels

- **HIGH**: Clear operation detected (truncate flag, InsertUpdate step)
- **MEDIUM**: Inferred from job patterns
- **LOW**: No operation detected, using safe fallback

### Reference Table Override

Filenames containing "status", "catalog", "lookup", "reference" → Always use `table` regardless of detected operation.

---

## Materialization Types

### 1. Table Materialization

**What it does:** Drops and recreates table on every run.

**When to use:**
- Reference/lookup tables (< 1000 rows)
- Small dimensions (< 1M rows)
- When Pentaho uses TRUNCATE_INSERT

**Configuration:**
```sql
{{ config(
    materialized='table',
    tags=['silver', 'adq', 'reference_data']
) }}
```

**Pros:** Simple, predictable, no data drift risk
**Cons:** Slow for large tables (> 10M rows)

---

### 2. Incremental Materialization

**What it does:** First run builds complete table; subsequent runs process only new/changed records.

**When to use:**
- Large tables (> 1M rows)
- Facts (typically append-only)
- Large dimensions with updates

**Strategies:**

#### Merge Strategy (Default)
```sql
{{ config(
    materialized='incremental',
    unique_key='contract_id',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns'
) }}

select * from source_data

{% if is_incremental() %}
    where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

Use when: Records can be updated, need to handle late-arriving data

#### Append Strategy
```sql
{{ config(
    materialized='incremental',
    incremental_strategy='append'
) }}

select * from source_data

{% if is_incremental() %}
    where transaction_date > (select max(transaction_date) from {{ this }})
{% endif %}
```

Use when: Append-only data (events, logs, transactions)

#### Delete+Insert Strategy
```sql
{{ config(
    materialized='incremental',
    unique_key='date_key',
    incremental_strategy='delete+insert'
) }}
```

Use when: Reprocessing entire partitions

**Pros:** Fast for large tables, lower compute costs
**Cons:** More complex, requires good filter logic

---

### 3. View Materialization

**What it does:** Creates database view, query runs on read.

**When to use:** **RARELY** - Prefer `table` for better Snowflake performance.

**Configuration:**
```sql
{{ config(materialized='view') }}
```

**Cons:** Slow queries, compute cost on every read

---

### 4. Ephemeral Materialization

**What it does:** Creates CTE in dependent models, no database object.

**When to use:** **Sparingly** - Prefer `table` for visibility.

**Configuration:**
```sql
{{ config(materialized='ephemeral') }}
```

---

## Layer-Specific Patterns

### Silver ADQ (stg_*)

```sql
{{ config(
    materialized='incremental',
    unique_key='contract_id',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['silver', 'adq', 'contracts', 'ekip']
) }}

with source_data as (
    select * from {{ source('bronze', 'EKIP_AFFAIRE') }}
),

renamed as (
    select
        id_affaire as contract_id,        -- lowercase columns
        numero_affaire as contract_number,
        current_timestamp() as dbt_loaded_at,
        current_timestamp() as dbt_updated_at
    from source_data
)

select * from renamed

{% if is_incremental() %}
    where dbt_updated_at >= (select max(dbt_updated_at) from {{ this }})
{% endif %}
```

**Key:** Lowercase columns, `dbt_loaded_at`/`dbt_updated_at` timestamps

---

### Silver MAS (mas_*)

```sql
{{ config(
    materialized='incremental',
    unique_key='CONTRACT_ID',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['ods', 'contracts']
) }}

with stg_contracts as (
    select * from {{ ref('stg_ekip_contracts') }}
),

transformed as (
    select
        CONTRACT_ID,                      -- UPPERCASE columns
        STATUS_NAME,
        CREATED_DATE
    from stg_contracts
)

select
    *,
    current_timestamp() as PROCESS_DATE,
    'dbt_run' as PROCESS_ID
from transformed

{% if is_incremental() %}
    where CREATED_DATE >= (select max(CREATED_DATE) from {{ this }})
{% endif %}
```

**Key:** UPPERCASE columns, `PROCESS_DATE`/`PROCESS_ID` columns

---

### Gold Dimensions (d_*)

```sql
{{ config(
    materialized='incremental',
    unique_key='APPROVAL_LEVEL_NK',
    incremental_strategy='merge',
    tags=['gold', 'dimension', 'dim_approval_level']
) }}
```

**Key:** Use `table` if < 1M rows for simplicity

---

### Gold Facts (f_*)

```sql
{{ config(
    materialized='incremental',
    unique_key='transaction_id',
    incremental_strategy='append',
    cluster_by=['transaction_date'],
    tags=['gold', 'fact']
) }}
```

**Key:** Usually `append` strategy, add clustering for large tables

---

## Detection Examples

### Example 1: Pentaho Truncate → DBT Table

**Pentaho XML:**
```xml
<step>
  <type>TableOutput</type>
  <truncate>Y</truncate>
</step>
```

**Detection Result:**
```json
{
  "detected_operation": "TRUNCATE_INSERT",
  "recommended_materialization": "table",
  "confidence": "high"
}
```

**Generated DBT:**
```sql
{{ config(materialized='table') }}
-- Detected from: Pentaho TRUNCATE_INSERT (truncate=Y)
-- Confidence: high
```

---

### Example 2: Pentaho InsertUpdate → DBT Incremental Merge

**Pentaho XML:**
```xml
<type>InsertUpdate</type>
<key><name>STATUS_ID</name></key>
```

**Detection Result:**
```json
{
  "detected_operation": "MERGE",
  "recommended_materialization": "incremental",
  "incremental_strategy": "merge",
  "confidence": "high"
}
```

**Generated DBT:**
```sql
{{ config(
    materialized='incremental',
    unique_key='STATUS_ID',
    incremental_strategy='merge'
) }}
-- Detected from: Pentaho MERGE operation
-- Confidence: high
```

---

## Performance Optimization

### Clustering Keys (Large Tables)

```sql
{{ config(
    materialized='incremental',
    unique_key='transaction_id',
    cluster_by=['transaction_date', 'customer_id']
) }}
```

Choose based on: Common filter columns, join columns (dates first)

---

## Testing

```bash
# First run (full refresh)
dbt run --select model_name --full-refresh

# Second run (incremental)
dbt run --select model_name

# Check for duplicates
select unique_key, count(*)
from model_name
group by unique_key
having count(*) > 1;  -- Should return 0 rows
```

---

## Troubleshooting

### "Low confidence detection"
**Cause:** No clear operation in Pentaho XML
**Solution:** Check pentaho_raw.json, review Pentaho manually, or accept safe default

### "Reference table detected as incremental"
**Cause:** Filename doesn't match reference patterns
**Solution:** Rename to include "status"/"catalog" or manually override

---

## Summary

**Detection is automatic:**
1. Parser reads Pentaho operations (truncate, merge, append)
2. Analyzer maps to DBT materialization
3. Generator applies intelligent overrides
4. Result: Production-ready models matching Pentaho behavior

**Simple rule:** `incremental` for most, `table` for reference tables.
