# Learnings Summary - Relevant to Current Migration

**Generated**: 2025-11-20
**Source**: lessons_learned.md
**Total Learnings**: 8 accumulated from dim_contract, dim_proposal, dim_status migrations
**Last Knowledge Base Update**: 2025-11-19

---

## High-Impact Learnings

### Learning L-20251029-001: GETENUMML UDF Produces Incorrect Results

- **Category**: UDF_HANDLING
- **Impact**: HIGH
- **Affects**: sql-translator, dbt-model-generator, quality-validator
- **Pattern**: GETENUMML() UDF exists in Snowflake (TFSES_ANALYTICS.TFS_SILVER.GETENUMML) but returns incorrect/NULL results (silent failure)
- **Root Cause**: UDF deployed with faulty logic - compiles successfully but produces wrong data at runtime

**Prevention**:
- **sql-translator**: Maintain "broken UDFs" list, auto-replace GETENUMML with explicit JOIN pattern
- **dbt-model-generator**: Never generate models using GETENUMML(), replace if found in translated SQL
- **quality-validator**: Grep for GETENUMML and flag as HIGH SEVERITY error

**Solution Pattern**:
```sql
-- NEVER use: GETENUMML(enumeration_column, language_id)

-- ALWAYS use this pattern instead:
WITH enum_translations AS (
    SELECT
        s.sysenumeration_id,
        COALESCE(
            t1.translation,           -- Direct translation for language_id=4
            t2.translation,           -- Parent language fallback
            s.description             -- Final fallback to base description
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

**Reference Implementations**:
- `{dbt_repository}/models/silver/silver_adq/stg_miles_product.sql` (lines 53-73)
- `{dbt_repository}/models/silver/silver_adq/stg_miles_contract.sql` (lines 126-348)

---

### Learning L-20251105-003: Julian Date Incremental Filters Fail Without Conversion

- **Category**: SQL_TRANSLATION
- **Impact**: HIGH
- **Affects**: sql-translator, dbt-model-generator
- **Pattern**: Incremental WHERE clause comparing Julian NUMBER column to DATE literal causes type mismatch error
- **Root Cause**: EKIP stores dates as Julian numeric values (e.g., 2459580 = 2021-12-15), cannot compare directly with DATE literals

**Prevention**:
- Always wrap Julian date columns with `{{ convert_from_julian() }}` macro in WHERE clauses
- Never compare Julian NUMBER columns directly with DATE literals
- Identify Julian columns during translation (NUMBER type with DATE/TIME in column name)

**Solution**:
```sql
-- WRONG (type mismatch):
{% if is_incremental() %}
    WHERE date_creation > '2020-01-01'
{% endif %}

-- CORRECT (with macro):
{% if is_incremental() %}
    WHERE {{ convert_from_julian('date_creation') }} > '2020-01-01'::date
{% endif %}
```

**Affected Tables**: EKIP_AFFAIRE, EKIP_MATIMMA, EKIP_HISTOSTAT, EKIP_DETTIERS (all EKIP date fields)

---

### Learning L-20251029-002: Lowercase Column Names Require Quoted Identifiers

- **Category**: CASE_SENSITIVITY
- **Impact**: MEDIUM
- **Affects**: sql-translator, dbt-model-generator
- **Pattern**: Source tables with lowercase column names fail unless double-quoted
- **Root Cause**: Snowflake defaults to uppercase, lowercase columns must be explicitly quoted

**Prevention**:
- **sql-translator**: Query INFORMATION_SCHEMA.COLUMNS before translation to detect mixed-case columns
- **dbt-model-generator**: Use double-quoted identifiers for all lowercase or mixed-case columns

**Solution**:
```sql
-- WRONG (fails on C3X_USERS):
SELECT iduser, firstname, lastname FROM {{ source('bronze', 'C3X_USERS') }}

-- CORRECT (quoted identifiers):
SELECT
    "iduser" as iduser,
    "firstname" as firstname,
    "lastname" as lastname
FROM {{ source('bronze', 'C3X_USERS') }}
```

**Affected Tables**: C3X_USERS, potentially other non-EKIP/MILES tables

---

## Medium-Impact Learnings

### Learning L-20251105-005: Incremental Strategy Mismatch

- **Category**: INCREMENTAL_STRATEGY
- **Impact**: MEDIUM
- **Pattern**: Using wrong incremental strategy causes duplicates or missing data
- **Solution**:
  - `merge` strategy for tables with updates (use `unique_key`)
  - `append` strategy for append-only tables (no unique_key)
  - `delete+insert` for partitioned tables

**Examples**:
```sql
-- For contract updates (merge):
{{ config(
    materialized='incremental',
    unique_key='contract_id_ekip',
    incremental_strategy='merge'
) }}

-- For history tables (append):
{{ config(
    materialized='incremental',
    incremental_strategy='append'
) }}
```

---

### Learning L-20251105-006: Missing Default Values in Dimensions

- **Category**: DATA_QUALITY
- **Impact**: MEDIUM
- **Pattern**: Dimension tables missing default values (UNKNOWN=-1, N/A=0) cause NULL FK issues
- **Solution**: Always include default rows in dimension initial load

**Pattern**:
```sql
-- Add to all dimension models:
UNION ALL
SELECT -1 as id, 'UNKNOWN' as nk, 'Unknown' as description, ...
UNION ALL
SELECT 0 as id, 'N/A' as nk, 'N/A' as description, ...
```

---

### Learning L-20251105-007: Hard-Coded Schema Names in SQL

- **Category**: DBT_SYNTAX
- **Impact**: MEDIUM
- **Pattern**: Hardcoded table names (TFSES_ANALYTICS.TFS_BRONZE.TABLE) break DBT lineage
- **Solution**: Always use `{{ source() }}` or `{{ ref() }}`

**Correct Usage**:
```sql
-- WRONG:
FROM TFSES_ANALYTICS.TFS_BRONZE.EKIP_AFFAIRE

-- CORRECT:
FROM {{ source('bronze', 'EKIP_AFFAIRE') }}

-- For model references:
FROM {{ ref('stg_contracts') }}
```

---

### Learning L-20251105-004: Schema Prefix Stripping in Model Names

- **Category**: NAMING_CONVENTION
- **Impact**: LOW
- **Pattern**: Removing Pentaho prefixes (adq_, mas_) causes naming confusion
- **Solution**: Keep semantic meaning, transform prefixes appropriately

**Correct Naming**:
- `adq_ekip_contracts.ktr` → `silver/silver_adq/stg_ekip_contracts.sql`
- `mas_contracts.kjb` → `silver/silver_mas/mas_contracts.sql`
- `d_contract.ktr` → `gold/d_contract.sql`

---

## Agent-Specific Guidance

### For sql-translator

**Pre-Translation Checks**:
1. Query INFORMATION_SCHEMA.COLUMNS for case-sensitive columns
2. Identify Julian date columns (NUMBER type, DATE/TIME in name)
3. Scan for GETENUMML() function calls
4. Check for hardcoded schema names

**Auto-Replacements**:
```python
# Broken UDFs to replace:
broken_udfs = {
    'GETENUMML': 'enum_translations_cte_pattern'
}

# Add to translation_metadata.json:
{
  "broken_udfs_replaced": ["GETENUMML"],
  "case_sensitive_tables": ["C3X_USERS"],
  "julian_date_columns": ["DATE_CREATION", "DATE_MODIFICATION", "DATE_IMMATRICULATION"],
  "requires_convert_from_julian": true
}
```

---

### For dbt-model-generator

**Mandatory Checks**:
1. **GETENUMML Detection**: Replace with enum_translations CTE if found in translated SQL
2. **Julian Date WHERE Clauses**: Wrap in `{{ convert_from_julian() }}` for incremental models
3. **Case-Sensitive Columns**: Use double-quoted identifiers
4. **Source References**: Verify all `{{ source() }}` and `{{ ref() }}` used
5. **Default Values**: Include UNKNOWN=-1 and N/A=0 in all dimensions

**Code Comments to Add**:
```sql
-- GETENUMML UDF replaced with explicit JOIN (broken UDF - see L-20251029-001)
-- Julian date conversion required for incremental (see L-20251105-003)
-- Case-sensitive columns quoted (see L-20251029-002)
```

---

### For quality-validator

**Validation Checklist**:

**HIGH SEVERITY Checks**:
- [ ] No GETENUMML() calls present (grep all models)
- [ ] Julian dates wrapped in convert_from_julian() in WHERE clauses (for incremental models)
- [ ] All source references use `{{ source() }}` (no hardcoded TFSES_ANALYTICS.TFS_BRONZE.*)

**MEDIUM SEVERITY Checks**:
- [ ] Lowercase columns properly quoted (check C3X_USERS and other non-EKIP tables)
- [ ] Incremental strategy matches table type (merge vs append)
- [ ] Dimension tables include default values (UNKNOWN=-1, N/A=0)
- [ ] All refs use `{{ ref() }}` (no hardcoded model names)

**Validation SQL**:
```bash
# Check for broken UDF:
grep -r "GETENUMML" models/

# Check for hardcoded schemas:
grep -r "TFSES_ANALYTICS\\.TFS_BRONZE\\." models/

# Check for unquoted lowercase columns in C3X_USERS models:
grep -r "C3X_USERS" models/ | grep -v '"iduser"'
```

---

## Common Pitfalls to Avoid

1. **Silent UDF Failures**: GETENUMML compiles but returns wrong data → Always replace with explicit JOINs
2. **Type Mismatches**: Julian NUMBER vs DATE literal → Always use convert_from_julian() macro
3. **Case Issues**: Lowercase columns fail without quotes → Query INFORMATION_SCHEMA proactively
4. **Incremental Logic**: Missing Julian conversion breaks incremental loads → Always wrap in macro
5. **Missing Lineage**: Hardcoded table names break DBT lineage graph → Always use source()/ref()
6. **NULL Foreign Keys**: Missing default dimension values → Always include UNKNOWN=-1 and N/A=0

---

## Quick Reference

**Total learnings in knowledge base**: 8
**Last knowledge base update**: 2025-11-19
**Dimensions contributing**: dim_contract, dim_proposal, dim_status
**Categories covered**: SQL_TRANSLATION, UDF_HANDLING, CASE_SENSITIVITY, INCREMENTAL_STRATEGY, NAMING_CONVENTION, DATA_QUALITY, DBT_SYNTAX

**Full knowledge base**: `.claude/skills/dbt-best-practices/reference/repo_context/lessons_learned.md`

---

## Learning Statistics by Category

- **UDF_HANDLING**: 1 learning (HIGH impact)
- **SQL_TRANSLATION**: 1 learning (HIGH impact)
- **CASE_SENSITIVITY**: 1 learning (MEDIUM impact)
- **INCREMENTAL_STRATEGY**: 1 learning (MEDIUM impact)
- **DATA_QUALITY**: 1 learning (MEDIUM impact)
- **DBT_SYNTAX**: 1 learning (MEDIUM impact)
- **NAMING_CONVENTION**: 1 learning (LOW impact)

**High-Impact Learnings (3)**: Must be proactively applied by all agents
**Medium-Impact Learnings (4)**: Should be checked during validation
**Low-Impact Learnings (1)**: Follow established conventions

---

**Note**: This summary is auto-generated from lessons_learned.md. The knowledge base accumulates automatically from each migration. The system learns and improves over time.
