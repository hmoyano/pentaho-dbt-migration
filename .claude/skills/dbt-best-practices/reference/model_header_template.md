# DBT Model Header Template

Production-style header format for all DBT models based on team conventions.

## Standard Header Format

Every DBT model must start with this header structure:

```sql
{{ config(
    materialized='incremental',
    unique_key='<primary_key>',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['<layer>', '<business_entity>', '<source_system>']
) }}

-- ============================================================
-- MODEL_NAME
-- ------------------------------------------------------------
-- Source Pentaho: <pentaho_filename>.ktr/.kjb
-- Layer: <layer_name> (<layer_purpose>)
-- Purpose:
--   <Detailed multi-line description of what this model does>
--   <Include business logic, transformations, and key details>
-- ============================================================
```

---

## Template by Layer

### Silver ADQ Template (stg_*)

```sql
{{ config(
    materialized='incremental',
    unique_key='<primary_key>',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['silver', 'adq', '<business_entity>', '<source_system>']
) }}

-- ============================================================
-- STG_<TABLE_NAME>
-- ------------------------------------------------------------
-- Source Pentaho: adq_<source>_<table>.ktr
-- Layer: Silver (staging)
-- Purpose:
--   Extract and normalize <entity> data from <SOURCE_SYSTEM>.
--   Applies standard column naming and adds audit timestamps.
-- ============================================================
```

**Example:**
```sql
{{ config(
    materialized='incremental',
    unique_key='contract_id',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['silver', 'adq', 'contracts', 'ekip']
) }}

-- ============================================================
-- STG_EKIP_CONTRACTS
-- ------------------------------------------------------------
-- Source Pentaho: adq_ekip_contracts.ktr
-- Layer: Silver (staging)
-- Purpose:
--   Extract contract data from EKIP source system.
--   Standardizes column names, converts Julian dates, and
--   adds dbt_loaded_at/dbt_updated_at timestamps.
-- ============================================================
```

---

### Silver MAS Template (mas_*)

```sql
{{ config(
    materialized='incremental',
    unique_key='<PRIMARY_KEY>',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['ods', '<business_entity>']
) }}

-- ============================================================
-- MAS_<TABLE_NAME>
-- ------------------------------------------------------------
-- Source Pentaho: mas_<table>.kjb
-- Layer: Silver (ODS/business logic)
-- Purpose:
--   Apply business logic to <entity> data from staging layer.
--   <Describe specific transformations and business rules>
-- ============================================================
```

**Example:**
```sql
{{ config(
    materialized='incremental',
    unique_key='CONTRACT_ID',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['ods', 'contracts']
) }}

-- ============================================================
-- MAS_CONTRACTS
-- ------------------------------------------------------------
-- Source Pentaho: mas_contracts.kjb
-- Layer: Silver (ODS/business logic)
-- Purpose:
--   Consolidate contract data from staging with business rules.
--   Applies status decoding, date standardization, and enrichment
--   with related entities (customers, products).
-- ============================================================
```

---

### Gold Template (d_*, f_*)

```sql
{{ config(
    materialized='incremental',
    unique_key='<SURROGATE_KEY>',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['<dimensional|fact>', '<business_entity>']
) }}

-- ============================================================
-- D_<DIMENSION_NAME> / F_<FACT_NAME>
-- ------------------------------------------------------------
-- Source Pentaho: d_<dimension>.ktr / f_<fact>.ktr
-- Layer: Gold (dimensional/fact)
-- Purpose:
--   <Describe dimensional model purpose>
--   <Include SCD type, grain, and key business logic>
-- ============================================================
```

**Example (Dimension):**
```sql
{{ config(
    materialized='incremental',
    unique_key='CUSTOMER_NK',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['dimensional', 'customer']
) }}

-- ============================================================
-- D_CUSTOMER
-- ------------------------------------------------------------
-- Source Pentaho: d_customer.ktr
-- Layer: Gold (dimensional)
-- Purpose:
--   Customer dimension built from ODS (MAS) layer.
--   Implements SCD Type 2 with version tracking and
--   customer group relationships.
-- ============================================================
```

**Example (Fact):**
```sql
{{ config(
    materialized='incremental',
    unique_key='TRANSACTION_ID',
    incremental_strategy='append',
    tags=['fact', 'sales']
) }}

-- ============================================================
-- F_SALES
-- ------------------------------------------------------------
-- Source Pentaho: f_sales.ktr
-- Layer: Gold (fact)
-- Purpose:
--   Sales transaction fact table at transaction line level.
--   Contains measures and foreign keys to customer, product,
--   date, and dealer dimensions.
-- ============================================================
```

---

## Section Headers Within Model

After the main header, use numbered emoji sections for CTEs:

```sql
-- ============================================================
-- 0️⃣ Sources
-- ============================================================
with
src_table1 as (select * from {{ source('bronze', 'TABLE1') }}),
src_table2 as (select * from {{ source('bronze', 'TABLE2') }}),

-- ============================================================
-- 1️⃣ Base Transformation Description
-- ============================================================
base_transformation as (
    select
        -- transformation logic
    from src_table1
),

-- ============================================================
-- 2️⃣ Join with Related Entities
-- ============================================================
joined_data as (
    select
        -- join logic
    from base_transformation
    left join src_table2 on ...
),

-- ============================================================
-- 3️⃣ Apply Business Rules
-- ============================================================
business_logic as (
    select
        -- business rules
    from joined_data
),

-- ============================================================
-- 4️⃣ Final Output
-- ============================================================
final as (
    select
        -- explicit column list
    from business_logic
)

select * from final
```

---

## Header Content Guidelines

### Model Name
- UPPERCASE for the model name in header
- Matches the file name (without .sql)
- Examples: `STG_CONTRACTS`, `MAS_CUSTOMERS`, `D_CUSTOMER`

### Source Pentaho
- Exact filename from `pentaho-sources/<dimension>/` folder
- Include file extension (.ktr or .kjb)
- Examples: `adq_ekip_contracts.ktr`, `mas_contracts.kjb`, `d_customer.ktr`

### Layer Description
- **Silver (staging)** - For stg_ models (ADQ layer)
- **Silver (ODS/business logic)** - For mas_ models (MAS layer)
- **Gold (dimensional)** - For d_ models
- **Gold (fact)** - For f_ models

### Purpose Section
- **2-4 sentences** describing:
  1. What data source(s) this model uses
  2. What transformations/business logic it applies
  3. What the output represents
  4. Any special handling (SCD, incremental strategy, etc.)

---

## Configuration Guidelines

### Tags
- **Always include layer tag**: `silver`, `gold`, `dimensional`, `fact`, `ods`
- **Include business entity**: `contracts`, `customers`, `dealers`, etc.
- **Include source system for ADQ**: `ekip`, `miles`, `tes`, etc.
- **Multiple tags OK**: `tags=['silver', 'adq', 'contracts', 'ekip']`

### Unique Key
- **Silver ADQ**: Natural key from source (lowercase)
- **Silver MAS**: Natural key (UPPERCASE)
- **Gold**: Surrogate key or natural key (UPPERCASE)
- **Always specify** for incremental models

### Incremental Strategy
- **merge**: For most models (allows updates)
- **append**: For append-only facts (rare)
- **delete+insert**: For partition-based updates (rare)

### on_schema_change
- **Always use**: `on_schema_change='sync_all_columns'`
- Allows schema evolution without model rebuild

---

## Special Cases

### Reference/Lookup Tables

```sql
{{ config(
    materialized='table',  -- Not incremental
    tags=['silver', 'adq', 'status', 'reference_data']
) }}

-- ============================================================
-- STG_STATUS
-- ------------------------------------------------------------
-- Source Pentaho: adq_status.ktr
-- Layer: Silver (staging)
-- Purpose:
--   Unified status reference data from EKIP and Miles systems.
--   Provides status codes and descriptions for contract statuses.
-- ============================================================
```

### Date Dimension

```sql
{{ config(
    materialized='table',  -- Not incremental
    tags=['bronze', 'date', 'dimension']
) }}

-- ============================================================
-- SOURCE_DATE
-- ------------------------------------------------------------
-- Source Pentaho: d_date.ktr
-- Layer: Bronze (dimension)
-- Purpose:
--   Date dimension with calendar attributes.
--   Generates dates from 1900-01-01 to 2119-12-31 with
--   fiscal year, quarter, month, and week attributes.
-- ============================================================
```

---

## Complete Example

```sql
{{ config(
    materialized='incremental',
    unique_key='contract_id',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    tags=['silver', 'adq', 'contracts', 'ekip']
) }}

-- ============================================================
-- STG_EKIP_CONTRACTS
-- ------------------------------------------------------------
-- Source Pentaho: adq_ekip_contracts.ktr
-- Layer: Silver (staging)
-- Purpose:
--   Extract contract data from EKIP source system.
--   Standardizes column names, converts Julian dates to
--   Gregorian, and adds audit timestamps for tracking.
-- ============================================================

-- ============================================================
-- 0️⃣ Sources
-- ============================================================
with
src_affaire as (select * from {{ source('bronze', 'EKIP_AFFAIRE') }}),
src_status as (select * from {{ source('bronze', 'EKIP_ACODIFS') }}),

-- ============================================================
-- 1️⃣ Rename and Standardize Columns
-- ============================================================
renamed as (
    select
        a.id_affaire as contract_id,
        a.numero_affaire as contract_number,
        a.code_statut as status_code,
        case when a.date_creation = 0 then null
             else dateadd('day', a.date_creation - 1721426, '0001-01-01') end as created_date
    from src_affaire a
),

-- ============================================================
-- 2️⃣ Add Metadata
-- ============================================================
add_metadata as (
    select
        *,
        current_timestamp() as dbt_loaded_at,
        current_timestamp() as dbt_updated_at
    from renamed
),

-- ============================================================
-- 3️⃣ Final Output
-- ============================================================
final as (
    select
        contract_id,
        contract_number,
        status_code,
        created_date,
        dbt_loaded_at,
        dbt_updated_at
    from add_metadata
)

select * from final

{% if is_incremental() %}
    where dbt_updated_at >= (select max(dbt_updated_at) from {{ this }})
{% endif %}
```

---

## Checklist

Before committing a model, verify:

- [ ] Config block has all required parameters
- [ ] Header block follows standard format
- [ ] Model name in header matches filename
- [ ] Source Pentaho filename is correct and exists
- [ ] Layer description is accurate
- [ ] Purpose section is clear and complete (2-4 sentences)
- [ ] Emoji-numbered section headers (0️⃣, 1️⃣, 2️⃣...)
- [ ] `src_` prefix used for all source CTEs
- [ ] Tags include layer, entity, and source system (if ADQ)
- [ ] Unique key specified for incremental models
- [ ] `on_schema_change='sync_all_columns'` included

---

## References

- Production examples: `{dbt_repository}/models/`
- Naming conventions: `naming_conventions.md`
- Materialization guide: `materialization_guide.md`
- CTE structure: `cte_structure.md`
