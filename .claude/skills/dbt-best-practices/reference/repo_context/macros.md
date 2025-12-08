# Custom Macros Available

**Generated**: 2025-11-18
**Repository**: {dbt_repository}/

This document catalogs all custom macros available in the DBT repository. Use these macros in new models to maintain consistency with existing patterns.

---

## Date Conversion Macros

### convert_from_julian(julian_field, output_type='date')

**Location**: `macros/convert_from_julian.sql`

**Purpose**: Converts Julian numeric date values (used in EKIP system) to Gregorian dates.

**Parameters**:
- `julian_field` (required): Column or expression containing Julian date number
- `output_type` (optional): Output format - 'date' (default) or 'timestamp'

**Usage Examples**:
```sql
-- Convert to DATE
{{ convert_from_julian('a.date_creation') }}

-- Convert to TIMESTAMP
{{ convert_from_julian('h.date_statut', 'timestamp') }}
```

**Implementation**:
```sql
case
    when {{ julian_field }} is null or {{ julian_field }} = 0 then null
    else
        {% if output_type == 'timestamp' %}
            dateadd(day, {{ julian_field }} - 1721426, '0001-01-01')::timestamp_ntz
        {% else %}
            dateadd(day, {{ julian_field }} - 1721426, '0001-01-01')::date
        {% endif %}
end
```

**Used in models**:
- `bronze/source_date.sql` - Converting EKIP_MATIMMA.DATE_IMMATRICULATION
- All models with EKIP date fields stored as Julian numbers

**Important Notes**:
- EKIP stores dates as Julian day numbers (e.g., 2451545 = 2000-01-01)
- Handles NULL and 0 values correctly
- Essential for incremental models with Julian date filters (see L-20251105-003)

---

### convert_to_julian(date_field)

**Location**: `macros/convert_to_julian.sql`

**Purpose**: Converts Gregorian dates to Julian numeric values (for EKIP compatibility).

**Parameters**:
- `date_field` (required): Column or expression containing date to convert

**Usage Examples**:
```sql
-- Convert date to Julian
{{ convert_to_julian('current_date') }}

-- Convert date literal
{{ convert_to_julian("to_date('2020-01-01')") }}
```

**Implementation**:
```sql
case
    when {{ date_field }} is null then null
    else datediff(day, '0001-01-01', {{ date_field }}) + 1721426
end
```

**Used in models**:
- Any model that needs to write back Julian dates to EKIP-compatible format
- Comparative analysis with EKIP source data

---

## SCD Type 2 Macro

### scd_type2(...)

**Location**: `macros/scd_type2.sql`

**Purpose**: Generic SCD Type 2 implementation with automatic version management, date tracking, and change detection.

**Parameters (Required)**:
- `source_cte` (string): Name of CTE containing prepared source data
- `natural_key` (string): SQL expression for natural key (can be column or formula)
- `tracked_columns` (list): List of columns that trigger new version when changed
- `effective_date_column` (string): Column with effective date of change

**Parameters (Optional)**:
- `surrogate_key` (string): SK column name (default: 'id')
- `natural_key_column` (string): NK column name (default: 'nk')
- `version_column` (string): Version column name (default: 'version')
- `date_from_column` (string): Start date column (default: 'date_from')
- `date_to_column` (string): End date column (default: 'date_to')
- `last_version_column` (string): Current version flag (default: 'last_version')
- `min_date` (string): Minimum history date (default: '1900-01-01')
- `max_date` (string): Open-ended date (default: '2199-12-31')

**Usage Example**:
```sql
{{ config(
    materialized='incremental',
    unique_key='id'
) }}

with source_data as (
    select
        customer_id,
        customer_name,
        customer_address,
        customer_status,
        current_date() as check_date
    from {{ ref('stg_customers') }}
)

{{ scd_type2(
    source_cte='source_data',
    natural_key='customer_id',
    tracked_columns=['customer_name', 'customer_address', 'customer_status'],
    effective_date_column='check_date'
) }}
```

**Behavior**:

1. **First Load (Full Refresh)**:
   - All records get VERSION=1
   - DATE_FROM='1900-01-01', DATE_TO='2199-12-31'
   - LAST_VERSION=true

2. **Incremental Load**:
   - **New NK**: INSERT version 1 with open-ended dates
   - **Unchanged NK**: No action
   - **Changed NK**:
     - UPDATE existing record (close DATE_TO, set LAST_VERSION=false)
     - INSERT new version with incremented VERSION number

3. **Surrogate Key Generation**:
   - Always generates new SK for each version
   - SK = MAX(existing_SK) + DENSE_RANK(over natural_key, version)

4. **Date Management**:
   - DATE_FROM = effective_date_column value (for changes)
   - DATE_TO = max_date for current version
   - DATE_TO = effective_date for closed versions

**Used in models**:
- Not currently used in repository (available for future SCD2 dimensions)
- Alternative to manual SCD2 implementation in `d_contract.sql`

**Important Notes**:
- Macro executes UPDATE via `run_query()` - requires incremental materialization
- Compares ALL tracked columns using NULL-safe comparison
- VERSION numbers are sequential per natural key
- LAST_VERSION flag simplifies current state queries

---

## Macro Usage Patterns in Repository

**Date Conversions**:
- Always use `convert_from_julian()` for EKIP date fields in queries
- Always wrap Julian dates with `convert_from_julian()` in incremental WHERE clauses
- Never compare Julian date columns directly with DATE literals (type mismatch - see L-20251105-003)

**SCD Type 2**:
- Manual SCD2 implementation used in `d_contract.sql` (lines 284-537)
- `scd_type2()` macro available but not yet adopted
- Consider using macro for new SCD2 dimensions to reduce code duplication

---

## Standard DBT Macros Also Used

**From dbt_utils package** (installed via packages.yml):
- `dbt_utils.surrogate_key(['col1', 'col2'])` - Generate deterministic hash keys
- `dbt_utils.expression_is_true` - Custom test for business rule validation
- Standard tests: `not_null`, `unique`, `relationships`, `accepted_values`

**From dbt core**:
- `{{ ref('model_name') }}` - Reference other models
- `{{ source('schema', 'table') }}` - Reference source tables
- `{{ var('variable_name') }}` - Access project variables
- `{{ is_incremental() }}` - Conditional logic for incremental models
- `{{ this }}` - Reference current model

---

## Key Findings for Migration Agents

**For sql-translator**:
- Detect Julian date columns during translation (NUMBER type with DATE/TIME in name)
- Add metadata flag: `requires_julian_conversion: true`
- Convert Oracle date operations to use `convert_from_julian()` macro

**For dbt-model-generator**:
- Use `convert_from_julian()` in incremental WHERE clauses for Julian dates
- Consider `scd_type2()` macro for new SCD2 dimensions
- Always use `{{ source() }}` and `{{ ref() }}` - never hardcode table names

**For quality-validator**:
- Check incremental models with Julian dates have `convert_from_julian()` wrapper
- Verify all table references use `{{ source() }}` or `{{ ref() }}`
- Validate SCD2 models have required columns: VERSION, DATE_FROM, DATE_TO, LAST_VERSION

---

## CRITICAL: GETENUMML UDF is BROKEN (See Learning L-20251029-001)

**DO NOT USE**: `TFSES_ANALYTICS.TFS_SILVER.GETENUMML`

**Problem**: The GETENUMML() UDF exists in Snowflake but produces incorrect results (silent failure).

**Replacement Pattern**:
```sql
-- NEVER use this:
GETENUMML(enumeration_column, language_id) as translated_value

-- ALWAYS use this instead:
WITH enum_translations AS (
    SELECT
        s.sysenumeration_id,
        COALESCE(
            t1.translation,           -- Direct translation
            t2.translation,           -- Parent language fallback
            s.description             -- Final fallback
        ) AS description_ml
    FROM {{ source('bronze', 'MILES_SYSENUMERATION') }} s
    LEFT JOIN {{ source('bronze', 'MILES_TRANSLATEDSTRING') }} t1
        ON t1.language_id = 4
        AND t1.multilanguagestring_id = s.description_mlid
    LEFT JOIN {{ source('bronze', 'MILES_LANGUAGE') }} l
        ON l.language_id = 4
    LEFT JOIN {{ source('bronze', 'MILES_TRANSLATEDSTRING') }} t2
        ON l.parentlanguage_id = t2.language_id
        AND t2.multilanguagestring_id = s.description_mlid
)

-- Then in main query:
LEFT JOIN enum_translations et
    ON source.enumeration_column = et.sysenumeration_id
```

**Reference Implementation**: `{dbt_repository}/models/silver/silver_adq/stg_miles_product.sql` (lines 53-73)

**Agents must**:
- **sql-translator**: Auto-replace GETENUMML() with enum_translations CTE pattern
- **dbt-model-generator**: Never generate models using GETENUMML()
- **quality-validator**: Grep for GETENUMML and flag as HIGH SEVERITY error

---

**Last Updated**: 2025-11-18
**Total Macros**: 3 (convert_from_julian, convert_to_julian, scd_type2)
