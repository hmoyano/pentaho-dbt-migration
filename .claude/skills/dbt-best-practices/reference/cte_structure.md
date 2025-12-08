# CTE Structure and Best Practices

Complete guide for structuring Common Table Expressions (CTEs) in DBT models.

## Why CTEs?

CTEs (Common Table Expressions) improve code:
- **Readability**: Break complex queries into logical steps
- **Maintainability**: Easy to modify individual steps
- **Debuggability**: Can test each CTE independently
- **Reusability**: Clear separation of concerns

---

## Standard CTE Pattern

Every DBT model follows this structure:

```sql
{{ config(...) }}

-- ============================================================
-- MODEL_NAME
-- ------------------------------------------------------------
-- Source Pentaho: filename.ktr
-- Layer: Silver (staging) / Gold (dimensional)
-- Purpose:
--   Detailed description of what this model does
-- ============================================================

-- ============================================================
-- 0️⃣ Sources
-- ============================================================
with
src_<source_1> as (select * from {{ source('bronze', 'TABLE_1') }}),
src_<source_2> as (select * from {{ source('bronze', 'TABLE_2') }}),

-- ============================================================
-- 1️⃣ First Transformation Description
-- ============================================================
<transformation_cte_1> as (
    -- First transformation logic
),

-- ============================================================
-- 2️⃣ Second Transformation Description
-- ============================================================
<transformation_cte_2> as (
    -- Second transformation logic
),

-- ============================================================
-- 3️⃣ Final Output
-- ============================================================
final as (
    -- Final SELECT with explicit columns
)

select * from final
```

**Key Elements:**
- Header comment block with model metadata
- Numbered emoji sections (0️⃣, 1️⃣, 2️⃣, etc.)
- `src_` prefix for source CTEs
- Clear section headers between CTEs
- Descriptive transformation names

---

## CTE Naming Conventions

### 1. Import CTEs (0️⃣ Sources Section)

**Purpose:** Bring in data from sources or upstream models

**Names:** Use `src_` prefix for source tables, descriptive names for refs

```sql
-- ============================================================
-- 0️⃣ Sources
-- ============================================================
with
src_contracts as (select * from {{ source('bronze', 'EKIP_AFFAIRE') }}),
src_customers as (select * from {{ source('bronze', 'EKIP_TIERS') }}),
src_status as (select * from {{ source('bronze', 'EKIP_ACODIFS') }}),

-- For refs (staging/intermediate models)
stg_contracts as (select * from {{ ref('stg_ekip_contracts') }}),
stg_customers as (select * from {{ ref('stg_ekip_customers') }}),
```

**Naming patterns:**
- `src_<entity>` - When importing from source (use src_ prefix!)
- `stg_<entity>` - When importing from staging layer
- `mas_<entity>` - When importing from MAS layer
- `<entity>` - When importing from gold layer

**Rules:**
- First CTEs in the query under 0️⃣ Sources section
- Use `src_` prefix for ALL source() calls
- One CTE per import
- Can be on single lines for brevity: `src_table as (select * from ...),`
- Use descriptive names (not `cte1`, `import`, `t1`)

### 2. Transformation CTEs

**Purpose:** Apply business logic, joins, calculations

**Names:** Verb or action describing the transformation

```sql
renamed as (
    -- Rename columns to standard
),

filtered as (
    -- Filter data
),

joined as (
    -- Join multiple sources
),

add_calculations as (
    -- Add calculated fields
),

deduplicated as (
    -- Remove duplicates
),

apply_business_rules as (
    -- Complex business logic
),
```

**Common transformation CTE names:**
- `renamed` - Column renaming
- `filtered` - Filtering rows
- `joined` - Joining tables
- `deduplicated` - Removing duplicates
- `add_<field>` - Adding specific fields
- `apply_<logic>` - Applying business rules
- `aggregated` - Aggregating data
- `pivoted` / `unpivoted` - Pivoting operations
- `add_calculations` - Adding calculated columns
- `add_metadata` - Adding metadata columns
- `data_quality` - Data quality filters

**Rules:**
- Use verb forms (action-oriented)
- One logical step per CTE
- Order matters (dependencies flow down)
- Descriptive, not generic

### 3. Final CTE

**Purpose:** Select final columns in desired order

**Name:** Always `final`

```sql
final as (
    select
        -- List columns in desired order
        customer_id,
        customer_name,
        created_date
    from <last_transformation_cte>
)

select * from final
```

**Rules:**
- Always named `final`
- Last CTE before final SELECT
- Lists columns explicitly (no `SELECT *` in production)
- Orders columns logically (PKs, FKs, attributes, dates, metadata)

---

## CTE Patterns by Model Type

### Pattern 1: Staging Model

**Purpose:** Import and standardize source data

```sql
{{ config(
    materialized='table',
    tags=['bronze', 'ekip']
) }}

with source_data as (

    select * from {{ source('ekip', 'contracts') }}

),

renamed as (

    select
        -- Rename to standard naming
        id_contract as contract_id,
        contract_number,
        code_status as status_code,
        to_date(date_creation, 'J') as created_date

    from source_data

),

add_metadata as (

    select
        *,
        current_timestamp() as _loaded_at,
        'EKIP' as _source_system

    from renamed

),

final as (

    select * from add_metadata

)

select * from final
```

**CTEs used:**
1. `source_data` - Import from source
2. `renamed` - Standardize column names
3. `add_metadata` - Add audit columns
4. `final` - Final output

### Pattern 2: Intermediate Model (Simple)

**Purpose:** Apply business logic to single source

```sql
{{ config(
    materialized='table',
    tags=['silver', 'contracts']
) }}

with staging_contracts as (

    select * from {{ ref('staging__ekip_contracts') }}

),

apply_business_rules as (

    select
        contract_id,
        contract_number,

        -- Decode status
        case
            when status_code = 'A' then 'Active'
            when status_code = 'I' then 'Inactive'
            when status_code = 'C' then 'Closed'
            else 'Unknown'
        end as status_name,

        -- Calculate duration
        datediff(month, start_date, coalesce(end_date, current_date())) as duration_months,

        -- Flags
        status_code = 'A' as is_active,

        created_date,
        _loaded_at

    from staging_contracts

),

filtered as (

    select *
    from apply_business_rules
    where contract_id is not null
        and created_date >= '{{ var("history_start_date") }}'

),

final as (

    select * from filtered

)

select * from final
```

**CTEs used:**
1. `staging_contracts` - Import
2. `apply_business_rules` - Business transformations
3. `filtered` - Data quality
4. `final` - Output

### Pattern 3: Intermediate Model (Join)

**Purpose:** Join multiple sources

```sql
{{ config(
    materialized='table',
    tags=['silver', 'contracts']
) }}

with staging_contracts as (

    select * from {{ ref('staging__ekip_contracts') }}

),

staging_customers as (

    select * from {{ ref('staging__ekip_customers') }}

),

staging_status as (

    select * from {{ ref('staging__status_history') }}

),

joined as (

    select
        c.contract_id,
        c.contract_number,
        c.customer_id,

        -- From customer
        cu.customer_name,
        cu.customer_type,

        -- From status (latest)
        s.status_code,
        s.status_date,

        c.created_date,
        c._loaded_at

    from staging_contracts c
    left join staging_customers cu
        on c.customer_id = cu.customer_id
    left join staging_status s
        on c.contract_id = s.contract_id
        and s.is_latest = true  -- Get latest status only

),

add_calculations as (

    select
        *,
        datediff(day, created_date, status_date) as days_to_status_change
    from joined

),

final as (

    select * from add_calculations

)

select * from final
```

**CTEs used:**
1. `staging_contracts` - Import contracts
2. `staging_customers` - Import customers
3. `staging_status` - Import status
4. `joined` - Join all sources
5. `add_calculations` - Add derived fields
6. `final` - Output

### Pattern 4: Dimension Model (SCD Type 2)

**Purpose:** Create slowly changing dimension

```sql
{{ config(
    materialized='incremental',
    unique_key='surrogate_key',
    tags=['gold', 'dimension']
) }}

with source as (

    select * from {{ ref('intermediate__customers') }}

    {% if is_incremental() %}
        where updated_at > (select max(updated_at) from {{ this }})
    {% endif %}

),

add_scd_columns as (

    select
        customer_id,
        customer_name,
        customer_type,
        address,
        phone,

        -- SCD Type 2: Track changes with effective dates
        updated_at as effective_date,

        coalesce(
            lead(updated_at) over (
                partition by customer_id
                order by updated_at
            ),
            '9999-12-31'::date
        ) as end_date,

        case
            when lead(updated_at) over (
                partition by customer_id
                order by updated_at
            ) is null
            then true
            else false
        end as is_current

    from source

),

add_surrogate_key as (

    select
        {{ dbt_utils.surrogate_key(['customer_id', 'effective_date']) }} as surrogate_key,
        *
    from add_scd_columns

),

final as (

    select
        -- Keys
        surrogate_key,
        customer_id,

        -- Attributes
        customer_name,
        customer_type,
        address,
        phone,

        -- SCD columns
        effective_date,
        end_date,
        is_current

    from add_surrogate_key

)

select * from final
```

**CTEs used:**
1. `source` - Import with incremental filter
2. `add_scd_columns` - Add SCD Type 2 columns
3. `add_surrogate_key` - Generate surrogate key
4. `final` - Final column ordering

### Pattern 5: Fact Model

**Purpose:** Create fact table with measures

```sql
{{ config(
    materialized='incremental',
    unique_key='transaction_id',
    incremental_strategy='append',
    tags=['gold', 'fact']
) }}

with source as (

    select * from {{ ref('intermediate__sales_transactions') }}

    {% if is_incremental() %}
        where transaction_date > (select max(transaction_date) from {{ this }})
    {% endif %}

),

add_foreign_keys as (

    select
        t.transaction_id,

        -- Foreign keys
        c.customer_key,
        p.product_key,
        d.date_key,
        s.store_key,

        -- Degenerate dimensions
        t.transaction_number,
        t.receipt_number,

        -- Measures
        t.quantity,
        t.unit_price,
        t.discount_amount,
        t.tax_amount,

        -- Transaction details
        t.transaction_date,
        t.transaction_timestamp,
        t._loaded_at

    from source t
    left join {{ ref('dim_customer') }} c
        on t.customer_id = c.customer_id
        and c.is_current = true
    left join {{ ref('dim_product') }} p
        on t.product_id = p.product_id
        and p.is_current = true
    left join {{ ref('dim_date') }} d
        on t.transaction_date = d.date_actual
    left join {{ ref('dim_store') }} s
        on t.store_id = s.store_id
        and s.is_current = true

),

add_calculations as (

    select
        *,

        -- Calculated measures
        quantity * unit_price as gross_amount,
        (quantity * unit_price) - discount_amount as net_amount,
        ((quantity * unit_price) - discount_amount) + tax_amount as total_amount,
        quantity * unit_price - discount_amount - tax_amount as revenue

    from add_foreign_keys

),

final as (

    select
        -- Primary key
        transaction_id,

        -- Foreign keys
        customer_key,
        product_key,
        date_key,
        store_key,

        -- Degenerate dimensions
        transaction_number,
        receipt_number,

        -- Measures
        quantity,
        unit_price,
        discount_amount,
        tax_amount,
        gross_amount,
        net_amount,
        total_amount,
        revenue,

        -- Dates
        transaction_date,
        transaction_timestamp,

        -- Metadata
        _loaded_at

    from add_calculations

)

select * from final
```

**CTEs used:**
1. `source` - Import with incremental filter
2. `add_foreign_keys` - Join to dimensions for keys
3. `add_calculations` - Calculate derived measures
4. `final` - Final column ordering

---

## CTE Best Practices

### 1. One Logical Step Per CTE

**✅ Good:**
```sql
with renamed as (
    select
        id_customer as customer_id,
        customer_name
    from source
),

filtered as (
    select *
    from renamed
    where customer_id is not null
)
```

**❌ Bad:**
```sql
with renamed_and_filtered as (
    select
        id_customer as customer_id,
        customer_name
    from source
    where id_customer is not null  -- Too many concerns
)
```

### 2. Use Descriptive Names

**✅ Good:**
```sql
with staging_contracts as (...),
apply_business_rules as (...),
add_calculations as (...)
```

**❌ Bad:**
```sql
with cte1 as (...),
temp as (...),
x as (...)
```

### 3. Column Selection

**In intermediate CTEs:**
- `SELECT *` is OK for passing through

**In final CTE:**
- List columns explicitly
- Order logically (PKs, FKs, attributes, dates, metadata)

**✅ Good:**
```sql
final as (
    select
        customer_id,
        customer_name,
        customer_type,
        created_date,
        _loaded_at
    from add_metadata
)
```

**❌ Bad:**
```sql
final as (
    select * from add_metadata  -- Too implicit for final
)
```

### 4. Comment Complex Logic

```sql
with add_calculations as (

    select
        *,

        {#
            Calculate revenue recognition based on contract type:
            - Monthly contracts: Revenue / months
            - Annual contracts: Revenue / 12
            - One-time: Full revenue immediately
        #}
        case
            when contract_type = 'MONTHLY' then revenue / contract_duration_months
            when contract_type = 'ANNUAL' then revenue / 12
            when contract_type = 'ONETIME' then revenue
            else 0
        end as monthly_revenue

    from contracts

)
```

### 5. Indent Consistently

```sql
with source_data as (

    select * from {{ source('ekip', 'contracts') }}

),

renamed as (

    select
        id as contract_id,
        name as contract_name
    from source_data

),

final as (

    select * from renamed

)

select * from final
```

---

## Common CTE Sequences

### Sequence 1: Simple Transformation
```
source → renamed → filtered → final
```

### Sequence 2: Join Pattern
```
source_1 → ...
source_2 → ...
source_3 → ...
joined → add_calculations → final
```

### Sequence 3: Aggregation Pattern
```
source → filtered → grouped → add_calculations → final
```

### Sequence 4: Deduplication Pattern
```
source → ranked → deduplicated → final
```

Example:
```sql
with source as (
    select * from {{ ref('staging__contracts') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by contract_id
            order by updated_at desc
        ) as row_num
    from source
),

deduplicated as (
    select * from ranked
    where row_num = 1
),

final as (
    select
        contract_id,
        contract_name,
        status
    from deduplicated
)

select * from final
```

---

## Testing CTEs

You can test individual CTEs during development:

```sql
-- Test just the renamed CTE
with source_data as (
    select * from {{ source('ekip', 'contracts') }}
),

renamed as (
    select
        id_contract as contract_id,
        contract_number
    from source_data
)

select * from renamed  -- Instead of final
limit 100
```

---

## Anti-Patterns to Avoid

### ❌ Don't Use Subqueries in FROM

**Bad:**
```sql
select *
from (
    select * from contracts
    where status = 'A'
) active_contracts
```

**Good:**
```sql
with active_contracts as (
    select * from contracts
    where status = 'A'
)

select * from active_contracts
```

### ❌ Don't Nest CTEs

**Bad:**
```sql
with outer_cte as (
    with inner_cte as (  -- Can't do this
        select * from source
    )
    select * from inner_cte
)
```

**Good:**
```sql
with inner_cte as (
    select * from source
),

outer_cte as (
    select * from inner_cte
)
```

### ❌ Don't Repeat Logic

**Bad:**
```sql
with calculations_1 as (
    select
        *,
        amount * 0.1 as tax
    from source
),

calculations_2 as (
    select
        *,
        amount * 0.1 as tax  -- Repeated!
    from source
)
```

**Good:**
```sql
with add_tax as (
    select
        *,
        amount * 0.1 as tax
    from source
),

use_in_multiple_places as (
    select * from add_tax
)
```

---

## Quick Reference

**CTE Ordering:**
1. Import CTEs (source_data, staging_x, etc.)
2. Transformation CTEs (renamed, filtered, joined, etc.)
3. Final CTE (always named `final`)
4. Final SELECT (always `select * from final`)

**Naming:**
- Import: Descriptive of source (`source_data`, `staging_contracts`)
- Transform: Action verb (`renamed`, `filtered`, `add_calculations`)
- Final: Always `final`

**Structure:**
```sql
{{ config(...) }}

with <imports> as (...),
<transforms> as (...),
final as (...)

select * from final
```

**Best Practices:**
- One logical step per CTE
- Descriptive names (not cte1, temp, x)
- Comment complex logic
- Explicit columns in final CTE
- Consistent indentation
