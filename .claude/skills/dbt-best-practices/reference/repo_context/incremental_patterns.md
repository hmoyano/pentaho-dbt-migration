# DBT Incremental Materialization Patterns

**Created**: 2025-10-28
**Purpose**: Document how Pentaho incremental load parameters are migrated to DBT
**Applies to**: All dimensions with large transaction tables (contracts, status_history, etc.)

---

## Overview

Pentaho transformations use runtime parameters (e.g., `${INC_DATE_FROM}`, `${MAX_PROCESS_DATE}`) to filter incremental loads. In DBT, we replace this with:

1. **`materialized='incremental'`** config
2. **`{% if is_incremental() %}`** blocks for delta logic
3. **`{{ var('variable_name', 'default') }}`** for optional runtime variables
4. **`{{ this }}`** to reference the current model for delta detection

---

## Pattern 1: Delta by Max ID

**Pentaho pattern:**
```sql
WHERE ID_FIELD > ${MAX_ID_LAST_RUN}
```

**DBT pattern:**
```sql
{% if is_incremental() %}
    where id_field > (select coalesce(max(id_field), 0) from {{ this }})
{% endif %}
```

**Example from stg_contracts.sql (lines 20-31):**
```sql
delta as (
    select id_affaire
    from {{ source('bronze', 'EKIP_AFFAIRE') }} a
    {% if is_incremental() %}
        where
            -- New contracts (greater ID)
            a.id_affaire > (select coalesce(max(contract_id_ekip), 0) from {{ this }})
    {% endif %}
)
```

**Key points:**
- `{{ this }}` references the current model (e.g., `stg_contracts`)
- `coalesce(..., 0)` handles first run when table is empty
- Delta CTE is used to filter all downstream CTEs

---

## Pattern 2: Delta by Date with Variable

**Pentaho pattern:**
```sql
WHERE DATE_FIELD >= ${INC_DATE_FROM}
```

**DBT pattern:**
```sql
{% if is_incremental() %}
    where date_field >= {{ var('inc_date_from', "to_date('2000-01-01')") }}
{% endif %}
```

**Example from stg_contracts.sql (lines 28-29):**
```sql
{% if is_incremental() %}
    where
        ...
        or
        -- Modified contracts since last incremental date
        a.date_creation >= {{ var('inc_date_status_history', "to_date('2000-01-01')") }}
{% endif %}
```

**Key points:**
- `{{ var('name', 'default') }}` provides optional runtime override
- Default value ensures full refresh works without variables
- Can pass variable via CLI: `dbt run --vars "{'inc_date_status_history': '2024-01-01'}"`

---

## Pattern 3: Combined Delta (ID + Date)

**Pentaho pattern:**
```sql
WHERE ID > ${MAX_ID} OR DATE_FIELD >= ${INC_DATE}
```

**DBT pattern:**
```sql
delta as (
    select primary_key
    from source_table
    {% if is_incremental() %}
        where
            id > (select coalesce(max(id), 0) from {{ this }})
            or
            date_field >= {{ var('inc_date', "to_date('2000-01-01')") }}
    {% endif %}
)
```

**Example from stg_contracts.sql (lines 23-30):**
```sql
{% if is_incremental() %}
    where
        -- New contracts (greater ID)
        a.id_affaire > (select coalesce(max(contract_id_ekip), 0) from {{ this }})
        or
        -- Modified contracts since last incremental date
        a.date_creation >= {{ var('inc_date_status_history', "to_date('2000-01-01')") }}
{% endif %}
```

**When to use:**
- Tables where records can be updated after creation (not just inserted)
- Captures both new records (by ID) and updates to old records (by date)

---

## Pattern 4: Simple Incremental (No Explicit Delta)

**Pentaho pattern:**
```sql
-- Full table load, Pentaho handles delta externally
SELECT * FROM SOURCE_TABLE
```

**DBT pattern:**
```sql
{{
    config(
        materialized='incremental',
        unique_key='primary_key_field',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

select * from {{ source('bronze', 'TABLE_NAME') }}
```

**Example from stg_status_history.sql (lines 1-98):**
```sql
{{
    config(
        materialized='incremental',
        unique_key='status_history_key',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

-- No explicit {% if is_incremental() %} block
-- DBT handles incremental logic based on unique_key
select
    concat(id_affaire, '_', no_ordre) as status_history_key,
    ...
from {{ source('bronze', 'EKIP_HISTOSTAT') }}
```

**When to use:**
- Small to medium tables (< 10M rows)
- Full source scan is acceptable
- DBT merge strategy efficiently updates only changed records

---

## Configuration Reference

### Config Block (Required for All Incremental Models)

```sql
{{
    config(
        materialized='incremental',           -- Enable incremental strategy
        unique_key='field_or_expression',     -- For merge strategy (upsert)
        incremental_strategy='merge',         -- Use merge (upsert) vs append
        on_schema_change='sync_all_columns',  -- Auto-add new columns
        tags=['silver', 'adq', 'incremental'] -- For selective runs
    )
}}
```

### Strategy Options

| Strategy | When to Use | Behavior |
|----------|-------------|----------|
| `merge` | Records can be updated | Upsert based on unique_key |
| `append` | Insert-only (e.g., logs) | Append new rows only |
| `delete+insert` | Partition-based loads | Delete partition, insert new data |

**Current standard**: Use `merge` for all transactional tables.

---

## Migration Checklist

When migrating a Pentaho transformation with incremental logic:

- [ ] **Identify unique key**: What field(s) uniquely identify a record?
- [ ] **Determine delta strategy**:
  - By ID only? → Pattern 1
  - By date only? → Pattern 2
  - By ID + date? → Pattern 3
  - No explicit delta? → Pattern 4
- [ ] **Add config block** with `materialized='incremental'`
- [ ] **Create delta CTE** (if needed) with `{% if is_incremental() %}`
- [ ] **Filter base CTEs** by joining to delta CTE
- [ ] **Define unique_key** in config (must be unique!)
- [ ] **Add tags** including 'incremental'
- [ ] **Test**:
  - Full refresh: `dbt run --full-refresh --select model_name`
  - Incremental: `dbt run --select model_name`

---

## Common Pentaho Parameters → DBT Equivalents

| Pentaho Parameter | DBT Equivalent | Notes |
|-------------------|----------------|-------|
| `${INC_DATE_FROM}` | `{{ var('inc_date_from', 'default') }}` | Optional runtime variable |
| `${INC_DATE_TO}` | `{{ var('inc_date_to', 'default') }}` | Optional runtime variable |
| `${MAX_PROCESS_DATE_TABLE}` | `(select max(date) from {{ this }})` | Query current model |
| `${MAX_ID_TABLE}` | `(select max(id) from {{ this }})` | Query current model |
| `${DELTA_CONDITION}` | `{% if is_incremental() %} ... {% endif %}` | Conditional logic |
| `${EKIP_HISTORY_INITIAL_DATE}` | Hardcoded or `var('initial_date', '...')` | Usually fixed date |

---

## Performance Considerations

### When to Use Incremental Materialization

**Use incremental for:**
- Tables > 1M rows
- Tables that change frequently (daily/hourly)
- High query complexity (many joins)
- Examples: contracts, status_history, financial transactions

**Use table materialization for:**
- Tables < 1M rows
- Reference/dimension tables
- Tables that change infrequently
- Examples: status codes, product catalog, dealer list

### Execution Time Comparison

**Example: stg_contracts (7M rows)**
- Full refresh: ~8 minutes
- Incremental (daily delta ~5k rows): ~30 seconds

**Trade-off**: Incremental adds complexity but saves 95%+ execution time.

---

## Testing Incremental Models

### 1. Test Full Refresh

```bash
dbt run --full-refresh --select stg_contracts
```

**Expected**: Model runs without errors, loads all historical data.

### 2. Test Incremental Run

```bash
# First run (full)
dbt run --select stg_contracts

# Second run (incremental)
dbt run --select stg_contracts
```

**Expected**:
- First run loads all data
- Second run processes only delta (should be much faster)

### 3. Test with Variable

```bash
dbt run --select stg_contracts --vars "{'inc_date_status_history': '2024-01-01'}"
```

**Expected**: Only processes records with date >= 2024-01-01.

### 4. Verify Unique Key

```sql
-- Run in Snowflake after dbt run
select
    unique_key_field,
    count(*)
from schema.model_name
group by unique_key_field
having count(*) > 1
```

**Expected**: 0 rows (no duplicates).

---

## Troubleshooting

### "Model has duplicates on unique_key"

**Cause**: unique_key in config doesn't uniquely identify records.

**Fix**:
- Use composite key: `concat(field1, '_', field2)`
- Or array: `unique_key=['field1', 'field2']`

### "Incremental run is slow"

**Cause**: Delta logic is inefficient or scanning too much data.

**Fix**:
- Ensure delta CTE filters early in pipeline
- Use indexed fields in delta condition
- Consider partitioning large tables

### "Variables not working in full refresh"

**Cause**: Variables without defaults fail when not provided.

**Fix**: Always provide default value:
```sql
{{ var('inc_date', "to_date('2000-01-01')") }}
```

---

## Future Enhancements

Potential improvements to consider:

1. **Snapshots for SCD Type 2**: Use `dbt snapshot` for slowly-changing dimensions
2. **Partition-based incremental**: Use `incremental_strategy='delete+insert'` with partitions
3. **Dynamic variables**: Calculate `inc_date` based on last run timestamp
4. **Incremental tests**: Add data quality tests specific to delta logic

---

## References

- **DBT Docs**: https://docs.getdbt.com/docs/build/incremental-models
- **Example Models**:
  - `{dbt_repository}/models/silver/silver_adq/stg_contracts.sql`
  - `{dbt_repository}/models/silver/silver_adq/stg_status_history.sql`
- **Config Reference**: `config/schema_registry.json` → `incremental_parameters`

---

**Last Updated**: 2025-10-28
**Maintained By**: Data Engineering Team
