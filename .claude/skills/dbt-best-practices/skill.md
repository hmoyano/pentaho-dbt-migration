---
name: dbt-best-practices
description: DBT best practices, templates, and conventions for generating high-quality DBT models
---

# DBT Best Practices

## Purpose

This skill provides comprehensive DBT best practices, model templates, and coding conventions for the Pentaho to DBT migration project. It serves as the authoritative guide for generating consistent, maintainable, and performant DBT models on Snowflake.

## What This Skill Provides

- **Model Templates**: Ready-to-use SQL templates for staging, intermediate, and mart models
- **Schema Templates**: YAML templates for model documentation and testing
- **Best Practices**: Guidelines for materialization, naming, and code structure
- **Reference Docs**: Detailed guides for CTEs, naming conventions, and materialization strategies

## Structure

```
dbt-best-practices/
├── SKILL.md (this file)
├── templates/
│   ├── staging_model_template.sql       (Bronze layer models)
│   ├── intermediate_model_template.sql  (Silver layer models)
│   ├── mart_model_template.sql          (Gold layer models)
│   └── schema_template.yml              (Model documentation)
└── reference/
    ├── materialization_guide.md         (When to use what)
    ├── naming_conventions.md            (File/model naming)
    └── cte_structure.md                 (CTE patterns)
```

## When to Use This Skill

Use this skill when:
- Generating new DBT models from Pentaho transformations
- Creating model documentation (schema.yml)
- Deciding on materialization strategy
- Structuring CTEs and transformations
- Naming models and columns
- Writing tests and documentation

**Don't use this skill for:**
- SQL translation (use oracle-snowflake-rules)
- Pentaho XML parsing (use pentaho-parser)
- Performance optimization (separate concern)

## Core Principles

### 1. Layered Architecture (Team Conventions)

**Bronze Layer**:
- Location: `models/bronze/`
- Purpose: Source definitions only
- File: `_sources.yml` (all sources in one file)

**Silver ADQ Layer**:
- Source: Pentaho `adq_*` files
- DBT: `stg_*` models in `models/silver/silver_adq/`
- Purpose: Raw data extraction with minimal transformation
- Materialization: `view` (default) or `table` (if >10M rows)

**Silver MAS Layer**:
- Source: Pentaho `mas_*` files
- DBT: `mas_*` models in `models/silver/silver_mas/`
- Purpose: Business logic and transformations
- Materialization: `table` (always)

**Gold Layer**:
- Source: Pentaho `d_*` and `f_*` files
- DBT: `d_*` and `f_*` models in `models/gold/`
- Purpose: Final analytical models (dimensions and facts)
- Materialization: `table` (dimensions) or `incremental` (facts)

### 2. Naming Conventions (Team Conventions)

**Pentaho → DBT Mapping:**
```
adq_ekip_contracts.ktr    → silver/silver_adq/stg_ekip_contracts.sql
adq_status.ktr            → silver/silver_adq/stg_status.sql
mas_contracts.kjb         → silver/silver_mas/mas_contracts.sql
d_approval_level.ktr      → gold/d_approval_level.sql
d_date.ktr                → gold/d_date.sql
f_sales.ktr               → gold/f_sales.sql
```

**Rules:**
- All lowercase
- Underscores for word separation
- Prefix indicates layer (stg_, mas_, d_, f_)
- Remove `adq_` prefix, add `stg_` prefix for silver_adq
- Keep `mas_` prefix for silver_mas
- Keep `d_` and `f_` prefixes for gold
- Descriptive names (no abbreviations unless standard)

### 3. CTE Structure

Every model follows this pattern:
```sql
with source_data as (
    -- Get data from source or ref
),

transformation_step as (
    -- Apply business logic
),

final as (
    -- Final SELECT with all logic applied
)

select * from final
```

**Rules:**
- Always use CTEs (no subqueries in FROM)
- One CTE per logical transformation step
- Final CTE always named "final"
- Descriptive CTE names (not cte1, cte2, temp)
- Import CTEs at top, transformation CTEs in middle, final at end

### 4. Configuration

Every model must have a config block:
```sql
{{ config(
    materialized='table',
    tags=['layer', 'source_system'],
    unique_key='id'  -- for incremental
) }}
```

### 5. Dependencies

**Use macros, never hardcode:**
```sql
-- ✓ GOOD
from {{ source('ekip', 'contracts') }}
from {{ ref('staging__ekip_contracts') }}

-- ✗ BAD
from EKIP_SCHEMA.CONTRACTS
from ODS.STAGING__EKIP_CONTRACTS
```

## Templates Overview

### staging_model_template.sql
For bronze layer models that ingest raw data with minimal transformation:
- Use `{{ source() }}` for source tables
- Rename columns to standard format
- Cast data types if needed
- Add source system metadata
- Tag with source system

### intermediate_model_template.sql
For silver layer models with business logic:
- Use `{{ ref() }}` for dependencies
- Multiple CTEs for complex transformations
- Business rules and calculations
- Data quality filters
- Document each transformation step

### mart_model_template.sql
For gold layer dimensional and fact models:
- Incremental materialization for large tables
- `unique_key` configuration
- Comprehensive documentation
- Data quality tests
- Performance optimizations

### schema_template.yml
For model documentation and testing:
- Model description
- Column descriptions
- Data tests (not_null, unique, relationships)
- Meta tags for governance

## Best Practices

### Code Style

1. **SQL Keywords**: UPPERCASE
2. **Column Names**: lowercase_with_underscores
3. **Indentation**: 4 spaces (or 2 spaces consistently)
4. **Line Length**: < 100 characters when possible
5. **Commas**: Leading commas for column lists

```sql
select
    , customer_id
    , customer_name
    , created_date
from customers
```

### Jinja Usage

1. **Variables**: Use `{{ var('variable_name') }}`
2. **Macros**: Reference with `{{ macro_name() }}`
3. **Whitespace**: Use `{{- -}}` to trim whitespace
4. **Comments**: `{# This is a Jinja comment #}`

### Performance

1. **Incremental Models**: Use for tables > 1M rows
2. **Clustering**: Add clustering keys for large tables
3. **Column Selection**: Only select needed columns (no `SELECT *` in production)
4. **Early Filtering**: Filter data as early as possible in CTEs

### Documentation

1. **Every Model**: Must have description in schema.yml
2. **Key Columns**: Document business meaning
3. **Calculations**: Explain complex logic
4. **Sources**: Document source system and refresh frequency

### Testing

1. **Primary Keys**: `unique` and `not_null` tests
2. **Foreign Keys**: `relationships` test to parent tables
3. **Business Rules**: Custom tests for data quality
4. **Freshness**: Source freshness checks on staging models

## Common Patterns

### Pattern 1: Staging Model
```sql
{{ config(materialized='table', tags=['bronze', 'ekip']) }}

with source_data as (
    select * from {{ source('ekip', 'contracts') }}
),

renamed as (
    select
        id_contract as contract_id,
        contract_number,
        status_code as status,
        created_date
    from source_data
)

select * from renamed
```

### Pattern 2: Incremental Model
```sql
{{ config(
    materialized='incremental',
    unique_key='contract_id',
    tags=['gold', 'fact']
) }}

with source_data as (
    select * from {{ ref('intermediate__contracts') }}
)

select * from source_data

{% if is_incremental() %}
    where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

### Pattern 3: Dimension with SCD Type 2
```sql
{{ config(
    materialized='incremental',
    unique_key='surrogate_key',
    tags=['gold', 'dimension']
) }}

with source as (
    select * from {{ ref('intermediate__customers') }}
),

add_metadata as (
    select
        {{ dbt_utils.surrogate_key(['customer_id', 'effective_date']) }} as surrogate_key,
        customer_id,
        customer_name,
        effective_date,
        end_date,
        is_current
    from source
)

select * from add_metadata
```

## Migration Workflow

When converting a Pentaho transformation to DBT:

1. **Identify Layer**: Check filename prefix (adq_, mas_, d_, f_)
2. **Choose Template**: Select appropriate template based on layer
3. **Extract SQL**: Get SQL from pentaho_raw.json
4. **Translate SQL**: Use oracle-snowflake-rules skill
5. **Structure CTEs**: Break down into logical steps
6. **Add Config**: Set materialization and tags
7. **Document**: Create schema.yml entry
8. **Test**: Add data quality tests

## Quality Checklist

Before completing a model, verify:

- [ ] Config block present with correct materialization
- [ ] Uses `{{ ref() }}` or `{{ source() }}` (no hardcoded schemas)
- [ ] CTEs follow naming convention (descriptive, ends with "final")
- [ ] No subqueries in FROM clause (use CTEs instead)
- [ ] Column names are lowercase with underscores
- [ ] SQL keywords are UPPERCASE
- [ ] Model documented in schema.yml
- [ ] Key columns documented
- [ ] Appropriate tests added (unique, not_null, relationships)
- [ ] Tagged correctly (layer + source system)
- [ ] Incremental models have unique_key
- [ ] No `SELECT *` in final model (list columns explicitly)

## Variable Mapping

Pentaho variables → DBT variables:

```sql
-- Pentaho
WHERE date >= to_date('${EKIP_HISTORY_INITIAL_DATE}', 'YYYYMMDD')
FROM ${EKIP_SCHEMA}.CONTRACTS

-- DBT
WHERE date >= to_date('{{ var("ekip_history_initial_date") }}', 'YYYYMMDD')
FROM {{ source('ekip', 'contracts') }}
```

**Variable Naming:**
- Pentaho: `UPPER_CASE_WITH_UNDERSCORES`
- DBT: `lower_case_with_underscores`

## Common Pitfalls to Avoid

1. **Hardcoding Schema Names**: Always use `{{ source() }}` or `{{ ref() }}`
2. **Missing Config**: Every model needs a config block
3. **Poor CTE Names**: Use descriptive names, not temp1, temp2
4. **Subqueries**: Use CTEs instead
5. **Undocumented Models**: Every model needs description
6. **Missing Tests**: At minimum, test primary keys
7. **SELECT * Everywhere**: Be explicit about columns in production
8. **Inconsistent Naming**: Follow the conventions strictly

## Materialization Decision Tree

```
Is this a staging model (bronze)?
├─ YES → materialized='table'
└─ NO → Is this intermediate (silver)?
    ├─ YES → materialized='table'
    └─ NO → Is this a dimension/fact (gold)?
        └─ YES → How many rows?
            ├─ < 1M rows → materialized='table'
            └─ > 1M rows → materialized='incremental'
                          + unique_key required
                          + Add incremental logic
```

## Folder Structure (Team Conventions)

Organize models by layer:
```
models/
├── bronze/
│   └── _sources.yml                    # All source definitions
├── silver/
│   ├── silver_adq/                     # From adq_*.ktr files
│   │   ├── stg_ekip_contracts.sql
│   │   ├── stg_ekip_customers.sql
│   │   ├── stg_status.sql
│   │   └── _models.yml
│   └── silver_mas/                     # From mas_*.kjb files
│       ├── mas_contracts.sql
│       ├── mas_customers.sql
│       ├── mas_status.sql
│       └── _models.yml
└── gold/                               # From d_*.ktr and f_*.ktr files
    ├── d_approval_level.sql
    ├── d_customer.sql
    ├── d_date.sql
    ├── f_sales.sql
    └── _models.yml
```

**Key points:**
- Flat structure (no subfolders by source)
- One `_models.yml` per folder
- All sources in `bronze/_sources.yml`

## Related Skills

- **oracle-snowflake-rules**: For SQL translation rules
- **pentaho-parser**: For extracting metadata from Pentaho files
- **dbt-model-generator** (subagent): Uses this skill to generate models

## Version Compatibility

- **DBT**: 1.x (uses `source()` and `ref()` macros)
- **Snowflake**: Current syntax
- **Jinja2**: 2.x templating

## Additional Resources

- [DBT Best Practices](https://docs.getdbt.com/guides/best-practices)
- [DBT Style Guide](https://github.com/dbt-labs/corp/blob/main/dbt_style_guide.md)
- [DBT Discourse](https://discourse.getdbt.com/)
