# Gold Dimension Template

Simple template for all gold dimensions based on production patterns.

## Standard Pattern

**Every gold dimension needs:**
1. Default values (-1 'UNK', 0 'N/A')
2. Surrogate ID (DIMENSION_ID)
3. Natural key (DIMENSION_NK)
4. SCD columns (DATE_FROM, DATE_TO, VERSION, LAST_VERSION)
5. NO process timestamps (no dbt_loaded_at, no PROCESS_DATE)

---

## Complete Template

```sql
{{ config(
    materialized='incremental',
    unique_key='<DIMENSION>_NK',
    incremental_strategy='merge',
    tags=['dimensional', '<business_entity>']
) }}

-- ============================================================
-- D_<DIMENSION>
-- <Description>
-- ============================================================

with
-- ============================================================
-- 1️⃣ Default values (always included)
-- ============================================================
default_values as (
    select
        -1 as <DIMENSION>_ID,
        'UNK' as <DIMENSION>_NK,
        'UNKNOWN' as <DIMENSION>_DESC,
        to_date('1900-01-01') as DATE_FROM,
        to_date('2199-12-31') as DATE_TO,
        1 as VERSION,
        true as LAST_VERSION
    union all
    select
        0 as <DIMENSION>_ID,
        'N/A' as <DIMENSION>_NK,
        'N/A' as <DIMENSION>_DESC,
        to_date('1900-01-01') as DATE_FROM,
        to_date('2199-12-31') as DATE_TO,
        1 as VERSION,
        true as LAST_VERSION
),

-- ============================================================
-- 2️⃣ Extract dimension values from source
-- ============================================================
dimension_values as (
    select distinct
        trim(<field>) as <DIMENSION>_NK,
        trim(<field>) as <DIMENSION>_DESC
    from {{ ref('<source_model>') }}
    where <field> is not null
),

-- ============================================================
-- 3️⃣ Combine defaults and values
-- ============================================================
combined as (
    select
        row_number() over (order by <DIMENSION>_NK) as <DIMENSION>_ID,
        <DIMENSION>_NK,
        <DIMENSION>_DESC,
        to_date('1900-01-01') as DATE_FROM,
        to_date('2199-12-31') as DATE_TO,
        1 as VERSION,
        true as LAST_VERSION
    from dimension_values
    union all
    select * from default_values
)

-- ============================================================
-- 4️⃣ Final output
-- ============================================================
select distinct
    <DIMENSION>_ID,
    <DIMENSION>_NK,
    <DIMENSION>_DESC,
    DATE_FROM,
    DATE_TO,
    VERSION,
    LAST_VERSION
from combined
```

---

## Real Example: d_approval_level

```sql
{{ config(
    materialized='incremental',
    unique_key='APPROVAL_LEVEL_NK',
    incremental_strategy='merge',
    tags=['dimensional', 'approval_level']
) }}

-- ============================================================
-- D_APPROVAL_LEVEL
-- Approval Level dimension from MAS_CONTRACTS
-- ============================================================

with
-- ============================================================
-- 1️⃣ Default values (always included)
-- ============================================================
default_values as (
    select
        -1 as APPROVAL_LEVEL_ID,
        'UNK' as APPROVAL_LEVEL_NK,
        'UNKNOWN' as APPROVAL_LEVEL_DESC,
        to_date('1900-01-01') as DATE_FROM,
        to_date('2199-12-31') as DATE_TO,
        1 as VERSION,
        true as LAST_VERSION
    union all
    select
        0 as APPROVAL_LEVEL_ID,
        'N/A' as APPROVAL_LEVEL_NK,
        'N/A' as APPROVAL_LEVEL_DESC,
        to_date('1900-01-01') as DATE_FROM,
        to_date('2199-12-31') as DATE_TO,
        1 as VERSION,
        true as LAST_VERSION
),

-- ============================================================
-- 2️⃣ Distinct approval levels from MAS_CONTRACTS
-- ============================================================
approval_levels as (
    select distinct
        trim(approval_level) as APPROVAL_LEVEL_NK,
        trim(approval_level) as APPROVAL_LEVEL_DESC
    from {{ ref('mas_contracts') }}
    where approval_level is not null
),

-- ============================================================
-- 3️⃣ Combine defaults and detected levels
-- ============================================================
combined as (
    select
        row_number() over (order by APPROVAL_LEVEL_NK) as APPROVAL_LEVEL_ID,
        APPROVAL_LEVEL_NK,
        APPROVAL_LEVEL_DESC,
        to_date('1900-01-01') as DATE_FROM,
        to_date('2199-12-31') as DATE_TO,
        1 as VERSION,
        true as LAST_VERSION
    from approval_levels
    union all
    select * from default_values
)

-- ============================================================
-- 4️⃣ Final output
-- ============================================================
select distinct
    APPROVAL_LEVEL_ID,
    APPROVAL_LEVEL_NK,
    APPROVAL_LEVEL_DESC,
    DATE_FROM,
    DATE_TO,
    VERSION,
    LAST_VERSION
from combined
```

---

## Key Points

**Always Include:**
- ✅ Default values CTE with -1 and 0 rows
- ✅ DIMENSION_ID (use row_number)
- ✅ DIMENSION_NK (natural key)
- ✅ DIMENSION_DESC (description)
- ✅ DATE_FROM, DATE_TO (always '1900-01-01' to '2199-12-31' for Type 1)
- ✅ VERSION (always 1 for Type 1)
- ✅ LAST_VERSION (always true for Type 1)

**Never Include:**
- ❌ dbt_loaded_at
- ❌ dbt_updated_at
- ❌ PROCESS_DATE
- ❌ PROCESS_ID

**Why This Structure:**
- Default values (-1, 0) handle NULL foreign keys
- DIMENSION_ID provides sequential numbering
- DATE_FROM/DATE_TO support future SCD Type 2 conversion
- VERSION/LAST_VERSION support SCD Type 2 pattern
- Simple Type 1 for now (all records have same dates)
