# DBT Naming Conventions

Comprehensive naming standards for DBT models, columns, and files in the Pentaho to DBT migration.

## Core Principles

1. **Case by layer**:
   - Silver ADQ: `lowercase_with_underscores`
   - Silver MAS: `UPPERCASE_WITH_UNDERSCORES`
   - Gold: `UPPERCASE_WITH_UNDERSCORES`
2. **Descriptive over terse**: `customer_id` not `cust_id`
3. **Consistency**: Same pattern across all models
4. **Layer prefixes**: Indicate layer in model name
5. **Source references**: Use `{{ source('bronze', 'TABLE_NAME') }}` pattern

---

## Pentaho to DBT File Mapping (Team Conventions)

### Transformation Filename → DBT Model Name

| Pentaho File | DBT Model | Layer | Notes |
|-------------|-----------|-------|-------|
| `adq_ekip_contracts.ktr` | `stg_ekip_contracts.sql` | Silver ADQ | Remove adq_ prefix, add stg_ prefix |
| `adq_ekip_01_status_history.ktr` | `stg_ekip_01_status_history.sql` | Silver ADQ | Remove adq_ prefix, add stg_, keep numeric markers |
| `adq_status.ktr` | `stg_status.sql` | Silver ADQ | Remove adq_ prefix, add stg_ |
| `mas_contracts.kjb` | `mas_contracts.sql` | Silver MAS | Keep mas_ prefix |
| `mas_1_status_history.kjb` | `mas_1_status_history.sql` | Silver MAS | Keep mas_ prefix and numeric markers |
| `d_approval_level.ktr` | `d_approval_level.sql` | Gold | Keep d_ prefix |
| `d_customer.ktr` | `d_customer.sql` | Gold | Keep d_ prefix |
| `f_sales.ktr` | `f_sales.sql` | Gold | Keep f_ prefix |
| `d_date.ktr` | `d_date.sql` | Gold | Keep d_ prefix |

### General Mapping Rules

**Silver ADQ (from adq_ files):**
```
adq_<source>_<table>.ktr → silver/silver_adq/stg_<source>_<table>.sql
adq_<table>.ktr          → silver/silver_adq/stg_<table>.sql
```

**Silver MAS (from mas_ files):**
```
mas_<table>.kjb      → silver/silver_mas/mas_<table>.sql
mas_<n>_<table>.kjb  → silver/silver_mas/mas_<n>_<table>.sql
```

**Gold (Dimensions and Facts):**
```
d_<table>.ktr → gold/d_<table>.sql  (keep d_ prefix)
f_<table>.ktr → gold/f_<table>.sql  (keep f_ prefix)
```

---

## Model Naming Standards

### Prefixes (Team Conventions)

| Prefix | Layer | Purpose | Example |
|--------|-------|---------|---------|
| `stg_` | Silver ADQ | Raw data from sources | `stg_ekip_contracts` |
| `mas_` | Silver MAS | Business logic | `mas_contracts` |
| `d_` | Gold | Dimensions | `d_customer`, `d_approval_level` |
| `f_` | Gold | Facts | `f_sales` |

### Source System Inclusion

**Pattern:** `stg_<table>` or `stg_<source>_<table>`

Examples:
- `stg_contracts` (from EKIP system in silver_adq)
- `stg_customers` (from EKIP system in silver_adq)
- `stg_miles_businesspartner` (from MILES system in silver_adq)
- `stg_tes_customer` (from TES system in silver_adq)
- `stg_status` (generic reference table in silver_adq)

**When to include source:**
- When same table name exists in multiple sources
- When source system is important context
- For clarity about data origin

**When to omit source:**
- For generic reference tables (dates, statuses)
- When table name is unique and obvious from context

### Source Reference Pattern

**CRITICAL**: Always use `{{ source('bronze', 'TABLE_NAME') }}` pattern

**Correct:**
```sql
{{ source('bronze', 'EKIP_AFFAIRE') }}
{{ source('bronze', 'MILES_CONTRACT') }}
{{ source('bronze', 'TES_CATALOG') }}
```

**Incorrect:**
```sql
{{ source('ekip', 'EKIP_AFFAIRE') }}  -- ❌ Don't use schema-specific sources
{{ source('bronze', 'affaire') }}      -- ❌ Table name must be UPPERCASE with prefix
```

### Tags Convention (ATOMIC TAGS)

**CRITICAL**: Tags should be atomic and combinable for flexible selectors.

**Correct (Atomic):**
```sql
{{ config(
    materialized='table',
    tags=['silver', 'adq', 'dim_approval_level', 'contracts']
) }}
```

**Incorrect (Combined):**
```sql
{{ config(
    materialized='table',
    tags=['silver_adq', 'dim_approval_level']  -- ❌ Don't combine layer+sublayer
) }}
```

**Why Atomic Tags?**
- Allows flexible DBT selectors: `dbt run --select tag:silver tag:adq`
- Easier filtering and grouping
- Better for partial runs: `dbt run --select tag:adq` (all ADQ models)
- Combined tags limit filtering options

**Tag Categories:**

1. **Layer Tags** (required):
   - `silver`, `gold`, `bronze`

2. **Sublayer Tags** (for silver only):
   - `adq` (acquisition/staging)
   - `mas` (master/business logic)

3. **Dimension Tags** (required for dimension-specific models):
   - `dim_approval_level`, `dim_customer`, `dim_dealer`, etc.
   - Format: `dim_<dimension_name>`

4. **Entity Tags** (optional, for organization):
   - `contracts`, `customers`, `status`, `reference`, etc.

**Examples by Layer:**

**Silver ADQ:**
```sql
tags=['silver', 'adq', 'dim_approval_level', 'contracts']
tags=['silver', 'adq', 'dim_customer', 'customers']
tags=['silver', 'adq', 'reference', 'status']  -- shared model (no dimension tag)
```

**Silver MAS:**
```sql
tags=['silver', 'mas', 'dim_approval_level', 'contracts']
tags=['silver', 'mas', 'dim_customer', 'customers']
```

**Gold:**
```sql
tags=['gold', 'dimensional', 'dim_approval_level']
tags=['gold', 'fact', 'f_sales']
```

**Shared Infrastructure (no dimension tag):**
```sql
tags=['silver', 'adq', 'reference']  -- stg_status.sql (used by multiple dimensions)
tags=['bronze', 'infrastructure']     -- source_date.sql
```

---

## Column Naming Standards

### Column Case by Layer

**CRITICAL RULE**: Column naming case depends on the layer:

| Layer | Case Convention | Example Columns |
|-------|----------------|-----------------|
| Silver ADQ (stg_*) | lowercase_with_underscores | `contract_id`, `customer_name`, `dbt_loaded_at` |
| Silver MAS (mas_*) | UPPERCASE_WITH_UNDERSCORES | `CONTRACT_ID`, `CUSTOMER_NAME`, `PROCESS_DATE` |
| Gold (d_*, f_*) | UPPERCASE_WITH_UNDERSCORES | `CUSTOMER_NK`, `DATE_FROM`, `LAST_VERSION` |

**Examples:**

**Silver ADQ:**
```sql
select
    contract_id,
    contract_number,
    customer_name,
    status_code,
    created_date,
    current_timestamp() as dbt_loaded_at,
    current_timestamp() as dbt_updated_at
from source
```

**Silver MAS:**
```sql
select
    CONTRACT_ID,
    CONTRACT_NUMBER,
    CUSTOMER_NAME,
    STATUS_CODE,
    CREATED_DATE,
    current_timestamp() as PROCESS_DATE,
    {{ var('process_id', "'dbt_run'") }} as PROCESS_ID
from stg
```

**Gold:**
```sql
select
    CUSTOMER_NK,
    CUSTOMER_NAME,
    DATE_FROM,
    DATE_TO,
    VERSION,
    LAST_VERSION
from transformed
```

### Timestamp Columns by Layer

**Different layers use different timestamp patterns:**

| Layer | Timestamp Columns | Purpose |
|-------|------------------|---------|
| Silver ADQ | `dbt_loaded_at`, `dbt_updated_at` (lowercase) | Track when data was loaded/updated in DBT |
| Silver MAS | `PROCESS_DATE`, `PROCESS_ID` (UPPERCASE) | Track processing metadata with run ID |
| Gold | `DATE_FROM`, `DATE_TO` (UPPERCASE) | SCD Type 2 effective dates, no process timestamps |

**Silver ADQ Pattern:**
```sql
select
    *,
    current_timestamp() as dbt_loaded_at,
    current_timestamp() as dbt_updated_at
from renamed
```

**Silver MAS Pattern:**
```sql
select
    *,
    current_timestamp() as PROCESS_DATE,
    {{ var('process_id', "'dbt_run'") }} as PROCESS_ID
from stg
```

**Gold Pattern (SCD Type 2):**
```sql
select
    CUSTOMER_NK,
    DATE_FROM,                    -- When version became effective
    DATE_TO,                      -- When version ended (2199-12-31 for current)
    VERSION,                      -- Version number
    LAST_VERSION                  -- Boolean: is this the current version?
from final
```

### Primary Keys

**Pattern:** `<entity>_id` or `<table>_key`

Examples:
```sql
-- Natural keys
customer_id
contract_id
product_id

-- Surrogate keys (dimensions)
customer_key
product_key

-- Composite keys (use descriptive name)
contract_line_id  -- not contract_id_line_number
```

**Rules:**
- Natural keys: `_id` suffix
- Surrogate keys (SCD): `_key` suffix
- Always singular entity name
- Be specific: `customer_id` not `id`

### Foreign Keys

**Pattern:** `<referenced_entity>_<id|key>`

Examples:
```sql
-- Reference to dim_customer
customer_key

-- Reference to staging__contracts
contract_id

-- Multiple FKs to same table (qualify)
bill_to_customer_id
ship_to_customer_id
```

**Rules:**
- Match the name in the referenced table
- Add qualifiers for multiple FKs to same table
- Use consistent suffix (_id for natural, _key for surrogate)

### Boolean Columns

**Pattern:** `is_<state>` or `has_<attribute>`

Examples:
```sql
is_active
is_deleted
is_current  -- for SCD Type 2
has_children
has_discount
can_edit
```

**Rules:**
- Prefix with `is_`, `has_`, or `can_`
- Use affirmative form (not `is_not_active`)
- Store as BOOLEAN type (true/false, not 'Y'/'N')

### Date/Timestamp Columns

**Pattern:** `<event>_<date|timestamp|at>`

Examples:
```sql
-- Dates
created_date
start_date
end_date
effective_date
birth_date

-- Timestamps
created_at
updated_at
deleted_at
processed_at

-- Specific formats
transaction_timestamp
order_datetime
```

**Rules:**
- Use `_date` for DATE type
- Use `_at` or `_timestamp` for TIMESTAMP type
- Use past tense for event: `created_at` not `create_at`
- Be specific: `order_date` not `date`

### Amount/Measure Columns

**Pattern:** `<measure>_<unit>` or `<measure>_amount`

Examples:
```sql
-- Amounts
total_amount
tax_amount
discount_amount
subtotal_amount

-- Quantities
order_quantity
shipped_quantity
available_quantity

-- Rates
commission_rate
tax_rate
discount_percentage

-- Counts
line_count
customer_count
```

**Rules:**
- Use `_amount` for monetary values
- Use `_quantity` for countable items
- Use `_rate` or `_percentage` for ratios
- Include unit if ambiguous: `weight_kg`, `height_cm`

### Status/Type Columns

**Pattern:** `<entity>_status` or `<entity>_type`

Examples:
```sql
-- Status
order_status
payment_status
contract_status

-- Type
customer_type
product_type
transaction_type

-- Code (when raw code value)
status_code
type_code

-- Name/Description (when decoded)
status_name
type_description
```

**Rules:**
- Use `_status` for state values
- Use `_type` for classification
- Use `_code` for system codes
- Use `_name` or `_description` for human-readable

### Calculated/Derived Columns

**Pattern:** Descriptive name indicating calculation

Examples:
```sql
-- Derived facts
profit_margin
total_revenue
average_order_value

-- Calculations
duration_days
duration_months
age_years

-- Ratios
revenue_per_customer
items_per_order
```

**Rules:**
- Make the calculation obvious from name
- Document formula in schema.yml
- Avoid generic names like `calc1`, `value`

### Metadata Columns

**Pattern:** `_<metadata_type>`

Examples:
```sql
-- Audit columns
_loaded_at
_created_at
_updated_at

-- Source tracking
_source_system
_source_file
_source_record_id

-- Data quality
_is_valid
_validation_status
_error_message

-- Lineage
_dbt_updated_at  -- DBT automatically adds
_row_hash
```

**Rules:**
- Prefix with underscore to distinguish from business columns
- Use present tense: `_loaded_at` not `_load_time`
- Keep at end of column list

### Slowly Changing Dimension Columns

**Pattern:** Standard SCD names

Examples:
```sql
-- SCD Type 2 columns
effective_date      -- When version became effective
end_date           -- When version ceased (9999-12-31 for current)
is_current         -- Boolean flag for current record
surrogate_key      -- Hash of natural key + effective_date
version_number     -- Optional: incremental version

-- Natural key (original business key)
customer_id        -- The actual business identifier
```

**Rules:**
- Always use these exact names for SCD Type 2
- `effective_date` and `end_date` are standard
- `is_current` is boolean (true/false)
- `surrogate_key` is the primary key

---

## Abbreviations

### Allowed Standard Abbreviations

Only use these common, industry-standard abbreviations:

| Abbreviation | Full Word | Example Usage |
|-------------|-----------|---------------|
| `id` | identifier | `customer_id` |
| `qty` | quantity | `order_qty` (only if space-constrained) |
| `num` | number | `invoice_num` (only if space-constrained) |
| `amt` | amount | `total_amt` (avoid if possible) |
| `pct` | percent | `tax_pct` (avoid if possible) |

### Avoid These Abbreviations

Write out these words in full:

| ❌ Avoid | ✅ Use Instead |
|---------|---------------|
| `cust` | `customer` |
| `ord` | `order` |
| `prod` | `product` |
| `addr` | `address` |
| `desc` | `description` |
| `trans` | `transaction` |
| `dept` | `department` |
| `mgr` | `manager` |

**Exception:** Domain-specific abbreviations that are standard in your business (e.g., `sku`, `upc`, `vin`)

---

## File Organization (Team Conventions)

### Directory Structure

```
models/
├── bronze/                      # Source definitions only
│   └── _sources.yml            # All source definitions (ekip, miles, tfsline, etc.)
│
├── silver/                      # Silver layer
│   ├── silver_adq/             # Raw data extraction (from adq_*.ktr)
│   │   ├── stg_ekip_contracts.sql
│   │   ├── stg_ekip_customers.sql
│   │   ├── stg_status.sql
│   │   └── _models.yml         # Documentation for all stg_ models
│   └── silver_mas/             # Business logic (from mas_*.kjb)
│       ├── mas_contracts.sql
│       ├── mas_customers.sql
│       ├── mas_status.sql
│       └── _models.yml         # Documentation for all mas_ models
│
└── gold/                        # Gold layer
    ├── d_approval_level.sql    # Dimension models
    ├── d_customer.sql
    ├── d_date.sql
    ├── f_sales.sql             # Fact models (if any)
    └── _models.yml             # Documentation for all gold models
```

**Key differences from standard DBT:**
- No `staging/` folder - use `silver/silver_adq/` instead
- No `intermediate/` folder - use `silver/silver_mas/` instead
- No `marts/` folder - use `gold/` instead
- All source definitions in one `bronze/_sources.yml` file
- No subfolders by source system - flat structure in each layer

### Schema.yml File Naming (Team Conventions)

**Pattern:** `_models.yml` or `_sources.yml`

Examples:
```
bronze/_sources.yml            # All source definitions
silver/silver_adq/_models.yml  # All stg_ models documentation
silver/silver_mas/_models.yml  # All mas_ models documentation
gold/_models.yml               # All gold models documentation
```

**Prefix with underscore** so they sort to top of directory listings.
**One file per folder** - keep it simple and consolidated.

---

## Consistency Examples

### ✅ Good Naming

```sql
-- Model: dim_customer.sql
select
    customer_key,                          -- Surrogate key
    customer_id,                           -- Natural key
    customer_name,
    customer_type,
    is_active,
    created_date,
    updated_at,
    effective_date,
    end_date,
    is_current,
    _loaded_at,
    _source_system
from source
```

### ❌ Bad Naming

```sql
-- Model: customers.sql (missing dim_ prefix)
select
    id,                    -- Too generic
    cust_name,             -- Avoid abbreviations
    Type,                  -- Wrong case
    active,                -- Missing is_ prefix for boolean
    create_dt,             -- Inconsistent date naming
    UpdatedTS,             -- Wrong case
    eff_dt,               -- Abbreviation
    IsCurrent,            -- Wrong case
    LoadTime,             -- Wrong case, missing underscore prefix
    src                   -- Too terse
from source
```

---

## Special Cases

### Reference/Lookup Tables

**Pattern:** Same as dimensions but often simpler

Examples:
```sql
dim_date          -- Standard date dimension
dim_status        -- Status lookup
dim_country       -- Country codes
dim_product_type  -- Product type lookup
```

### Bridge Tables

**Pattern:** `bridge_<entity1>_<entity2>`

Examples:
```sql
bridge_customer_product    -- Many-to-many customer/product
bridge_account_owner       -- Many-to-many account/owner
```

### Aggregate Tables

**Pattern:** `<entity>_<aggregation>`

Examples:
```sql
fact_sales_daily          -- Daily aggregation
fact_revenue_monthly      -- Monthly aggregation
intermediate__customer_summary  -- Customer-level aggregates
```

---

## Migration Checklist

When converting Pentaho model names to DBT:

- [ ] Identify layer (adq→bronze, mas→silver, d/f→gold)
- [ ] Apply correct prefix (staging__, intermediate__, dim_, fact_)
- [ ] Remove Pentaho numeric prefixes (adq_01, mas_1)
- [ ] Convert to lowercase_with_underscores
- [ ] Simplify overly complex names
- [ ] Add source system if needed (staging only)
- [ ] Verify no abbreviations (except standard ones)
- [ ] Check name is descriptive and clear
- [ ] Ensure consistency with related models

---

## Quick Reference

**Model Prefixes:**
- Bronze: `staging__<source>_<table>`
- Silver: `intermediate__<table>`
- Gold Dimension: `dim_<entity>`
- Gold Fact: `fact_<subject>`

**Column Patterns:**
- PK: `<entity>_id` or `<entity>_key`
- FK: `<referenced_entity>_id`
- Boolean: `is_<state>`, `has_<attribute>`
- Date: `<event>_date`
- Timestamp: `<event>_at`
- Amount: `<measure>_amount`
- Status: `<entity>_status`
- Type: `<entity>_type`
- Metadata: `_<metadata_type>`

**Case:**
- Files: lowercase_with_underscores
- SQL keywords: UPPERCASE
- Column names: lowercase_with_underscores
- Table names: lowercase_with_underscores
