# Migration Knowledge Base - Lessons Learned

**Purpose**: This file accumulates learnings from all migrations to help agents avoid repeating mistakes. All agents should read this file (via repo-analyzer) before starting work.

**Last Updated**: 2025-11-19
**Total Learnings**: 8
**Source Migrations**: dim_contract, dim_proposal, dim_status

---

## How Agents Should Use This File

1. **repo-analyzer** reads this file and creates `learnings_summary.md` with relevant guidance
2. **All agents** receive proactive guidance through the summary
3. **quality-validator** signals new learnings using `📚 LEARNING:` format
4. **learning-logger** processes signals and updates this file

---

## Categories

- **SQL_TRANSLATION**: Oracle to Snowflake SQL conversion issues
- **UDF_HANDLING**: Custom function preservation and replacement
- **CASE_SENSITIVITY**: Identifier case handling in Snowflake
- **PERFORMANCE**: Query performance and optimization
- **DEPENDENCY**: Model dependency and ordering issues
- **SCHEMA_MAPPING**: Variable to schema resolution
- **NAMING_CONVENTION**: Model and column naming issues
- **DATA_QUALITY**: Data validation and quality issues
- **INCREMENTAL_STRATEGY**: Incremental model patterns
- **DBT_SYNTAX**: DBT-specific syntax issues

---

## Learnings

### UDF_HANDLING - GETENUMML UDF Produces Incorrect Results (ID: L-20251029-001)

**Discovered**: 2025-10-29 in dimension dim_contract
**Impact**: HIGH
**Agents Affected**: sql-translator, dbt-model-generator, quality-validator

**Pattern/Issue**:
The GETENUMML() UDF exists in Snowflake (TFSES_ANALYTICS.TFS_SILVER.GETENUMML) but produces incorrect or NULL results when called. This UDF is intended to translate enumeration values to multilingual strings, but the function implementation is broken.

**Root Cause**:
The UDF was deployed to Snowflake but contains faulty logic. When sql-translator preserved the UDF call (as it should for custom functions), the resulting DBT models compiled successfully but returned wrong data at runtime. This is a **silent failure** - no errors, just incorrect data.

**Solution**:
Replace GETENUMML() calls with explicit JOINs to the enum_translations table:

```sql
-- BEFORE (problematic):
GETENUMML(enumeration_column, language_id) as translated_value

-- AFTER (corrected):
WITH enum_translations AS (
    SELECT
        se.ID AS enum_id,
        se.DESCRIPTION AS enum_description,
        ts.LANGUAGEID AS language_id,
        ts.TEXT AS enum_translation
    FROM {{ source('miles', 'sysenumeration') }} se
    LEFT JOIN {{ source('miles', 'translatedstring') }} ts
        ON se.TRANSLATEDSTRINGID = ts.TRANSLATEDSTRINGID
)

SELECT
    et.enum_translation as translated_value
FROM source_table st
LEFT JOIN enum_translations et
    ON st.enumeration_column = et.enum_id
    AND et.language_id = 1  -- Or variable: {{ var('default_language_id') }}
```

**Prevention - How to Detect Proactively**:

**For sql-translator**:
1. Maintain a "broken UDFs" list in `oracle-snowflake-rules/reference/function_mappings.md`
2. When encountering GETENUMML(), auto-replace with the explicit JOIN pattern above
3. Add function to replacement rules:
   ```
   GETENUMML(column, lang_id) → enum_translations CTE + LEFT JOIN pattern
   ```

**For dbt-model-generator**:
1. Never generate models using GETENUMML()
2. If translation_metadata.json contains GETENUMML, replace with JOIN pattern
3. Add comment: `-- GETENUMML UDF replaced with explicit JOIN (broken UDF - see L-20251029-001)`

**For quality-validator**:
1. Grep for GETENUMML in all generated models
2. If found, add HIGH SEVERITY warning to validation report
3. Suggest replacement with enum_translations pattern

**Agents That Should Apply This**:
- **sql-translator**: Auto-replace GETENUMML during Oracle→Snowflake translation
- **dbt-model-generator**: Replace GETENUMML if present in translated SQL
- **quality-validator**: Check for GETENUMML and warn if found

**Reference**:
- Dimension: dim_contract
- Fixed example: `{dbt_repository}/models/silver/silver_mas/stg_miles_product.sql` (lines 53-73)
- Affected models: stg_miles_contract, stg_miles_user, stg_3cx_user
- Validation report: `dimensions/dim_contract/metadata/validation_report.json`

---

### CASE_SENSITIVITY - Lowercase Column Names Require Quoted Identifiers (ID: L-20251029-002)

**Discovered**: 2025-10-29 in dimension dim_contract
**Impact**: MEDIUM
**Agents Affected**: sql-translator, dbt-model-generator

**Pattern/Issue**:
Source table C3X.C3X_USERS contains columns with lowercase names (iduser, firstname, lastname, etc.). When DBT models reference these columns without quotes, Snowflake interprets them as uppercase (IDUSER, FIRSTNAME) and throws "invalid identifier [column_name]" errors during compilation.

**Root Cause**:
Snowflake stores identifiers case-sensitively when created with double quotes, but defaults to uppercase for unquoted identifiers. The C3X_USERS table was created with lowercase column names (likely from a case-sensitive source system), but sql-translator generated unquoted column references assuming case-insensitive behavior.

**Solution**:
Use double-quoted identifiers when referencing lowercase columns:

```sql
-- BEFORE (fails with "invalid identifier IDUSER"):
SELECT
    iduser,
    firstname,
    lastname,
    email
FROM {{ source('c3x', 'c3x_users') }}

-- AFTER (works correctly):
SELECT
    "iduser" as iduser,
    "firstname" as firstname,
    "lastname" as lastname,
    "email" as email
FROM {{ source('c3x', 'c3x_users') }}
```

**Prevention - How to Detect Proactively**:

**For sql-translator** (Step 4.2 - Before Translation):
1. Query Snowflake INFORMATION_SCHEMA to detect case-sensitive columns:
   ```sql
   SELECT
       table_schema,
       table_name,
       column_name,
       CASE
           WHEN column_name != UPPER(column_name) THEN 'lowercase_detected'
           ELSE 'uppercase_only'
       END as case_type
   FROM TFSES_ANALYTICS.INFORMATION_SCHEMA.COLUMNS
   WHERE table_schema IN ('C3X', 'EKIP', 'MILES', ...)  -- From schema_registry.json
       AND column_name != UPPER(column_name);
   ```

2. Create a helper function: `detect_case_sensitive_columns(schema, table)` that returns:
   ```json
   {
     "table": "c3x.c3x_users",
     "case_sensitive_columns": ["iduser", "firstname", "lastname", "email"],
     "requires_quoting": true
   }
   ```

3. During SQL translation, automatically wrap case-sensitive columns in quotes:
   ```python
   if column_name in case_sensitive_columns:
       return f'"{column_name}" as {column_name}'
   else:
       return column_name
   ```

4. Add metadata to translation_metadata.json:
   ```json
   {
     "case_sensitive_tables": [
       {
         "table": "c3x.c3x_users",
         "columns_requiring_quotes": ["iduser", "firstname", "lastname", "email"]
       }
     ]
   }
   ```

**For dbt-model-generator**:
1. Read case_sensitive_tables from translation_metadata.json
2. When generating SELECT statements, check if columns need quotes
3. Add comment in model: `-- Case-sensitive columns quoted (see L-20251029-002)`

**Agents That Should Apply This**:
- **sql-translator**: Query INFORMATION_SCHEMA and auto-quote lowercase columns during translation
- **dbt-model-generator**: Respect case-sensitive column metadata when generating models

**Reference**:
- Dimension: dim_contract
- Affected source: `bronze/_sources.yml` (c3x.c3x_users)
- Fixed model: `{dbt_repository}/models/silver/silver_adq/stg_3cx_user.sql`
- Error message: `SQL compilation error: invalid identifier 'IDUSER'`

---

### SQL_TRANSLATION - Correlated Scalar Subqueries Not Supported in Snowflake (ID: L-20251105-001)

**Discovered**: 2025-11-05 in dimension dim_proposal
**Impact**: HIGH
**Agents Affected**: dbt-model-generator, sql-translator

**Pattern/Issue**:
dbt-model-generator created correlated scalar subqueries in the SELECT clause of stg_financial_proposals. The model had 5 subqueries that referenced the outer query's correlation variables. Snowflake threw "Unsupported subquery type cannot be evaluated" errors, blocking the entire model from running.

Example of problematic pattern:
```sql
SELECT
    fp.id_proposition,
    (SELECT channel_name FROM channels c WHERE c.id_channel = fp.id_channel) as channel_name,
    (SELECT external_ref FROM refs r WHERE r.id_proposition = fp.id_proposition) as external_reference,
    -- 3 more correlated subqueries...
FROM financial_proposals fp
```

**Root Cause**:
Snowflake does not support correlated scalar subqueries in the SELECT clause. This is a fundamental SQL engine limitation. The dbt-model-generator created these patterns to flatten related data, but this approach is incompatible with Snowflake's architecture.

**Solution**:
Convert ALL correlated scalar subqueries to CTEs with LEFT JOINs:

```sql
WITH channel_lookup AS (
    SELECT id_channel, channel_name
    FROM {{ source('bronze', 'channels') }}
),
external_reference AS (
    SELECT id_proposition, external_ref
    FROM {{ source('bronze', 'refs') }}
),
-- Additional CTEs for other lookups...

final AS (
    SELECT
        fp.id_proposition,
        cl.channel_name,
        er.external_ref,
        -- Other fields...
    FROM {{ source('bronze', 'financial_proposals') }} fp
    LEFT JOIN channel_lookup cl ON cl.id_channel = fp.id_channel
    LEFT JOIN external_reference er ON er.id_proposition = fp.id_proposition
    -- Other LEFT JOINs...
)

SELECT * FROM final
```

**Prevention - How to Detect Proactively**:

**For dbt-model-generator**:
1. **NEVER generate correlated scalar subqueries in SELECT clause** - this is a hard rule
2. When translating SQL that needs related data, ALWAYS use CTE + LEFT JOIN pattern
3. Add validation step: Scan generated SQL for pattern `\(SELECT .+ WHERE .+ = [a-z_]+\.[a-z_]+\)` in SELECT clause
4. If detected, automatically refactor to CTE + LEFT JOIN before writing model
5. Add this to model generation rules in `.claude/agents/dbt-model-generator.md`

**For sql-translator**:
1. During Oracle→Snowflake translation, detect correlated subqueries
2. Flag them in translation_metadata.json with `requires_cte_refactor: true`
3. Add note about Snowflake incompatibility

**For quality-validator**:
1. Add SQL pattern check: Search for `\(SELECT .+ FROM .+ WHERE .+ = [a-z_]+\.[a-z_]+\)` in SELECT clause
2. If found, mark as ERROR (not warning) - model will fail in Snowflake
3. Suggest CTE + LEFT JOIN refactoring

**Agents That Should Apply This**:
- **dbt-model-generator**: MUST never generate correlated scalar subqueries - use CTE + LEFT JOIN only
- **sql-translator**: Detect and flag correlated subqueries during translation
- **quality-validator**: Validate no correlated scalar subqueries in generated models

**Reference**:
- Dimension: dim_proposal
- Affected model: `{dbt_repository}/models/silver/silver_adq/stg_financial_proposals.sql`
- Subqueries converted: channel_lookup, external_reference, special_discount, last_status_lookup, last_status_details
- Error message: `Unsupported subquery type cannot be evaluated`

---

### DBT_SYNTAX - Oversimplification of Complex SQL Loses Critical Structure (ID: L-20251105-002)

**Discovered**: 2025-11-05 in dimension dim_proposal
**Impact**: HIGH
**Agents Affected**: dbt-model-generator

**Pattern/Issue**:
dbt-model-generator simplified stg_miles_quotes from 118-line translated SQL to 100-line model, making these critical errors:
1. Dropped the `leaseservice` table entirely (was LEFT JOINed in original)
2. Changed table alias from `pro` to `Q` for products table
3. Result: "invalid identifier 'Q.PRODUCT_ID'" error - should be `pro.PRODUCT_ID`

**Root Cause**:
dbt-model-generator attempted to "clean up" the translated SQL by removing what it perceived as redundant elements. However, this simplification:
- Broke table aliases used throughout the query
- Removed tables that had LEFT JOINs (appeared unused but weren't)
- Changed query semantics by altering join structure

**Solution**:
Regenerate model using EXACT translated SQL structure - preserve:
- All tables and JOINs (even if some columns aren't selected)
- All table aliases exactly as written
- All WHERE clauses and join conditions
- All SQL structure from translated file

**Prevention - How to Detect Proactively**:

**For dbt-model-generator**:
1. **CRITICAL RULE**: Preserve ALL tables, aliases, and SQL structure from `*_translated.sql` files
2. DO NOT simplify, optimize, or remove elements unless explicitly instructed
3. Validation step before writing model:
   - Extract all table aliases from translated SQL: `FROM (\w+) AS (\w+)`
   - Extract all alias references in SELECT/WHERE: `(\w+)\.(\w+)`
   - Verify every alias referenced exists in FROM/JOIN clauses
   - Verify no aliases were changed
4. Add this to generation rules: "Preserve translated SQL structure exactly - no simplification"

**For quality-validator**:
1. Read corresponding `*_translated.sql` file
2. Extract table aliases from translated SQL
3. Extract table aliases from generated model
4. Compare aliases - if ANY mismatch, mark as HIGH SEVERITY error
5. Check for missing tables - if translated SQL has table not in model, mark error

**Code Example**:
```sql
-- TRANSLATED SQL (118 lines):
SELECT
    q.quote_id,
    pro.product_name,           -- Alias: pro
    ls.service_description      -- Table: leaseservice (LEFT JOIN)
FROM miles_quotes q
LEFT JOIN miles_products pro ON pro.product_id = q.product_id
LEFT JOIN miles_leaseservice ls ON ls.quote_id = q.quote_id

-- WRONG (simplified - broke aliases):
SELECT
    q.quote_id,
    Q.product_name,             -- Changed alias to Q (ERROR!)
    -- Missing leaseservice join
FROM miles_quotes q
LEFT JOIN miles_products Q ON Q.product_id = q.product_id

-- CORRECT (preserved structure):
SELECT
    q.quote_id,
    pro.product_name,           -- Kept original alias: pro
    ls.service_description      -- Kept leaseservice join
FROM {{ source('bronze', 'MILES_QUOTES') }} q
LEFT JOIN {{ source('bronze', 'MILES_PRODUCTS') }} pro ON pro.product_id = q.product_id
LEFT JOIN {{ source('bronze', 'MILES_LEASESERVICE') }} ls ON ls.quote_id = q.quote_id
```

**Agents That Should Apply This**:
- **dbt-model-generator**: MUST preserve exact SQL structure from translated files - no simplification
- **quality-validator**: MUST validate aliases match between translated SQL and generated model

**Reference**:
- Dimension: dim_proposal
- Affected model: `{dbt_repository}/models/silver/silver_adq/stg_miles_quotes.sql`
- Translated SQL: `dimensions/dim_proposal/sql/adq_miles_quotes_translated.sql` (118 lines)
- Error: First generation was 100 lines with wrong aliases; second generation preserved structure

---

### SQL_TRANSLATION - Julian Date Type Mismatch in Incremental Logic (ID: L-20251105-003)

**Discovered**: 2025-11-05 in dimension dim_proposal
**Impact**: HIGH
**Agents Affected**: dbt-model-generator, sql-translator

**Pattern/Issue**:
Models with Julian date columns in incremental WHERE clauses fail with type mismatch error:
```sql
-- Incremental filter (WRONG):
WHERE a.date_creation >= to_date('2000-01-01')

-- Error:
"Can not convert parameter CAST('2000-01-01' AS DATE) of type [DATE]
 into expected type [NUMBER(10,0)]"
```

This is a **latent bug** - models work perfectly in full refresh mode but fail when run incrementally.

**Root Cause**:
Julian date columns are stored as NUMBER(10,0) in source systems (e.g., MILES.TFSLINE stores dates as Julian day numbers like 2451545 for 2000-01-01). When dbt-model-generator creates incremental logic, it generates standard date comparisons without checking column data types. Snowflake cannot implicitly convert DATE literals to Julian numbers, causing type mismatch.

**Solution**:
Wrap Julian date columns with convert_from_julian() macro in incremental logic:

```sql
-- BEFORE (fails on incremental run):
{% if is_incremental() %}
    WHERE a.date_creation >= to_date('2000-01-01')
{% endif %}

-- AFTER (works correctly):
{% if is_incremental() %}
    WHERE {{ convert_from_julian('a.date_creation') }} >= to_date('2000-01-01')
{% endif %}
```

**Prevention - How to Detect Proactively**:

**For sql-translator** (Step 4):
1. Query source table metadata to detect Julian date columns:
   ```sql
   SELECT column_name, data_type
   FROM TFSES_ANALYTICS.INFORMATION_SCHEMA.COLUMNS
   WHERE table_schema = 'MILES'
     AND table_name = 'TFSLINE'
     AND data_type = 'NUMBER'
     AND column_name LIKE '%DATE%' OR column_name LIKE '%TIME%';
   ```

2. Add julian_date_columns to translation_metadata.json:
   ```json
   {
     "tables": [
       {
         "table": "MILES.TFSLINE",
         "julian_date_columns": ["date_creation", "date_modified", "date_last_status"],
         "requires_conversion_macro": true
       }
     ]
   }
   ```

3. When translating SQL with Julian date filters, add comment:
   ```sql
   -- JULIAN DATE: date_creation stored as NUMBER - use convert_from_julian() for date operations
   ```

**For dbt-model-generator** (Step 5):
1. Read julian_date_columns from translation_metadata.json
2. When generating incremental logic (is_incremental() blocks), check if filter columns are Julian dates
3. If Julian date detected, automatically wrap with convert_from_julian() macro:
   ```jinja
   {% if is_incremental() %}
       WHERE {{ convert_from_julian('a.date_creation') }} >= to_date('{{ var("incremental_start_date") }}')
   {% endif %}
   ```

4. Add comment in model:
   ```sql
   -- Julian date conversion applied (see L-20251105-003)
   ```

**For quality-validator** (Step 6):
1. Read julian_date_columns from translation_metadata.json
2. Scan is_incremental() blocks for date comparisons
3. If Julian date column used without convert_from_julian(), mark as ERROR
4. Suggest: "Wrap {column} with convert_from_julian() macro"

**Agents That Should Apply This**:
- **sql-translator**: Detect Julian date columns and document in metadata
- **dbt-model-generator**: Auto-apply convert_from_julian() in incremental logic
- **quality-validator**: Validate Julian dates wrapped correctly in incremental blocks

**Reference**:
- Dimension: dim_proposal
- Affected models: stg_miles_quotes, stg_financial_proposals
- Source tables: MILES.TFSLINE (date_creation, date_modified, date_last_status)
- Macro location: `{dbt_repository}/macros/convert_from_julian.sql`
- Error occurs only on incremental runs, not full refresh (latent bug)

---

### DBT_SYNTAX - Column Name Mapping Between Layers Must Be Verified (ID: L-20251105-004)

**Discovered**: 2025-11-05 in dimension dim_proposal
**Impact**: MEDIUM
**Agents Affected**: dbt-model-generator

**Pattern/Issue**:
Gold layer model d_financial_proposal referenced wrong column names from staging models:
```sql
-- d_financial_proposal (WRONG):
SELECT
    financial_proposal_id,     -- Column doesn't exist
    proposal_status_id         -- Column doesn't exist
FROM {{ ref('stg_financial_proposals') }}

-- Error: "invalid identifier 'FINANCIAL_PROPOSAL_ID'"
```

Actual column names in stg_financial_proposals were:
- `ID_PROPOSITION` (not financial_proposal_id)
- `ID_STATUS` (not proposal_status_id)

**Root Cause**:
dbt-model-generator generated gold layer models based on assumptions about staging model schemas without reading the actual staging model files. It used "expected" naming conventions (e.g., table_name_id pattern) rather than verifying actual column names.

**Solution**:
Read staging model files and extract actual column names before generating gold models:

```sql
-- CORRECT (verified from staging model):
SELECT
    ID_PROPOSITION as financial_proposal_id,  -- Map from actual column
    ID_STATUS as proposal_status_id            -- Map from actual column
FROM {{ ref('stg_financial_proposals') }}
```

**Prevention - How to Detect Proactively**:

**For dbt-model-generator** (Step 5):
1. **Before generating gold layer models**, read all referenced staging models
2. Extract column names from SELECT clause of staging models:
   ```python
   def extract_columns_from_staging_model(model_path):
       # Parse SQL, extract all "column_name AS alias" patterns
       # Return: {"alias": "column_name", ...}
   ```

3. When generating gold model SELECT clause, validate column exists:
   ```python
   if column_name not in staging_columns:
       raise ValueError(f"Column {column_name} not found in {staging_model}")
   ```

4. Add metadata to dbt_generation_report.json:
   ```json
   {
     "gold_models": [
       {
         "model": "d_financial_proposal",
         "dependencies": [
           {
             "ref": "stg_financial_proposals",
             "columns_used": ["ID_PROPOSITION", "ID_STATUS", "date_creation"],
             "verified": true
           }
         ]
       }
     ]
   }
   ```

**For quality-validator** (Step 6):
1. Parse gold models and extract all {{ ref('...') }} dependencies
2. Read referenced staging models and extract their column schemas
3. Validate every column reference in gold model exists in staging model
4. If mismatch detected, mark as ERROR with suggestion:
   ```
   ERROR: Column 'financial_proposal_id' not found in stg_financial_proposals
   Available columns: ID_PROPOSITION, ID_STATUS, date_creation, ...
   Did you mean: ID_PROPOSITION?
   ```

**Code Example**:
```sql
-- stg_financial_proposals (staging layer - source of truth):
SELECT
    ID_PROPOSITION,                    -- Actual column name
    ID_STATUS,                         -- Actual column name
    date_creation,
    ...
FROM {{ source('bronze', 'MILES_TFSLINE') }}

-- d_financial_proposal (gold layer - WRONG):
SELECT
    financial_proposal_id,             -- Column doesn't exist!
    proposal_status_id                 -- Column doesn't exist!
FROM {{ ref('stg_financial_proposals') }}

-- d_financial_proposal (gold layer - CORRECT):
SELECT
    ID_PROPOSITION as financial_proposal_id,      -- Map from staging
    ID_STATUS as proposal_status_id               -- Map from staging
FROM {{ ref('stg_financial_proposals') }}
```

**Agents That Should Apply This**:
- **dbt-model-generator**: MUST read and validate staging model schemas before generating gold models
- **quality-validator**: MUST validate column references between layers

**Reference**:
- Dimension: dim_proposal
- Affected model: `{dbt_repository}/models/gold/d_financial_proposal.sql`
- Staging models: stg_financial_proposals, stg_miles_quotes
- Error: "invalid identifier 'FINANCIAL_PROPOSAL_ID'" - easy to fix but blocks gold layer

---

### SCHEMA_MAPPING - Incomplete Source Table Discovery Causes Iterative Failures (ID: L-20251105-005)

**Discovered**: 2025-11-05 in dimension dim_proposal
**Impact**: MEDIUM
**Agents Affected**: pentaho-analyzer, dependency-graph-builder

**Pattern/Issue**:
Migration required 10 source tables but discovered them iteratively through multiple validation failures:
1. Initial run failed → discovered 3 missing tables
2. Loaded 3 tables, run again → discovered 4 more missing
3. Loaded 4 tables, run again → discovered 3 more missing
4. Total: 10 tables across 4 systems (TFSLINE, TFSADMIN, MILES, EKIP)

This iterative discovery slowed migration significantly - each cycle took 10-15 minutes.

**Root Cause**:
pentaho-analyzer extracts table references from SQL queries, but doesn't traverse deep dependencies:
- Extracted direct table references from Pentaho transformations
- Missed tables referenced in JOINs, subqueries, or CTEs
- Missed tables from referenced views or macros
- Didn't analyze cross-dimension dependencies (e.g., d_proposal → mas_contracts → EKIP tables)

**Solution**:
Enhanced table dependency analysis upfront:

1. **Parse all SQL deeply** (not just top-level FROM clauses)
2. **Extract ALL table references**:
   - FROM clauses
   - JOIN clauses (INNER, LEFT, RIGHT, FULL)
   - Subqueries (nested SELECTs)
   - CTEs (WITH clauses)
   - Views (resolve view definitions)

3. **Generate complete table list** in pentaho_analyzed.json:
   ```json
   {
     "required_source_tables": [
       {"schema": "MILES", "table": "TFSLINE", "referenced_in": ["stg_financial_proposals", "stg_miles_quotes"]},
       {"schema": "MILES", "table": "TFSADMIN", "referenced_in": ["stg_miles_quotes"]},
       {"schema": "EKIP", "table": "CONTRACTS", "referenced_in": ["mas_contracts"]},
       // ... complete list
     ],
     "total_tables_required": 10
   }
   ```

4. **Validate table existence** before generating models:
   ```sql
   SELECT table_schema, table_name
   FROM TFSES_ANALYTICS.INFORMATION_SCHEMA.TABLES
   WHERE (table_schema = 'MILES' AND table_name = 'TFSLINE')
      OR (table_schema = 'MILES' AND table_name = 'TFSADMIN')
      -- ... check all required tables
   ```

5. **Report missing tables upfront** (before Step 5):
   ```
   ⚠️ Missing Source Tables (10 required):
   1. MILES.TFSLINE - required by stg_financial_proposals, stg_miles_quotes
   2. MILES.TFSADMIN - required by stg_miles_quotes
   3. EKIP.CONTRACTS - required by mas_contracts
   ... (complete list)

   Action Required:
   - Copy these 10 tables to Snowflake TFSES_ANALYTICS database
   - Add source definitions to bronze/_sources.yml
   - Then re-run migration
   ```

**Prevention - How to Detect Proactively**:

**For pentaho-analyzer** (Step 2):
1. Use comprehensive SQL parser (sqlparse library or similar)
2. Extract ALL table references recursively:
   ```python
   def extract_all_table_references(sql):
       tables = []
       # Parse FROM clauses
       # Parse JOIN clauses
       # Recursively parse subqueries
       # Parse CTEs
       # Resolve view definitions
       return tables
   ```

3. Add source_table_analysis section to pentaho_analyzed.json:
   ```json
   {
     "source_table_analysis": {
       "total_tables_required": 10,
       "by_schema": {
         "MILES": ["TFSLINE", "TFSADMIN", "SYSENUMERATION", ...],
         "EKIP": ["CONTRACTS", "CUSTOMERS"],
         "TFSLINE": ["PROPOSALS"],
         "C3X": ["C3X_USERS"]
       },
       "by_model": {
         "stg_financial_proposals": ["MILES.TFSLINE", "MILES.SYSENUMERATION"],
         "stg_miles_quotes": ["MILES.TFSLINE", "MILES.TFSADMIN", "MILES.LEASESERVICE"],
         ...
       }
     }
   }
   ```

**For dependency-graph-builder** (Step 3):
1. Read source_table_analysis from pentaho_analyzed.json
2. Query INFORMATION_SCHEMA to check which tables exist
3. Generate missing_tables report in dependency_graph.json:
   ```json
   {
     "missing_source_tables": [
       {"schema": "MILES", "table": "TFSLINE", "required_by": ["stg_financial_proposals"]},
       ...
     ]
   }
   ```

**For migrate command**:
1. After Step 3 completes, check for missing_source_tables in dependency_graph.json
2. If missing tables detected, PAUSE migration and report:
   ```
   ⚠️ MIGRATION PAUSED: Missing Source Tables

   10 required tables are not in Snowflake. Options:
   1. Continue anyway (models will fail)
   2. Stop, let me copy tables now
   3. Generate table copy script
   ```

**Agents That Should Apply This**:
- **pentaho-analyzer**: Extract ALL table references from SQL (deep parsing)
- **dependency-graph-builder**: Validate source table existence before Step 5
- **migrate command**: Pause and report missing tables after Step 3

**Reference**:
- Dimension: dim_proposal
- Total tables required: 10
- Systems: TFSLINE (2 tables), TFSADMIN (1 table), MILES (5 tables), EKIP (2 tables)
- Discovery method: Iterative (4 cycles) - should be upfront
- Impact: Added 40-60 minutes to migration time

---

### DATA_QUALITY - Miles DM_*_DIM Views Are Outdated - Use SYSENUMERATION Instead (ID: L-20251119-001)

**Discovered**: 2025-11-19 in dimension dim_status
**Impact**: HIGH
**Agents Affected**: pentaho-analyzer, sql-translator, dbt-model-generator

**Pattern/Issue**:
The initial DBT model for stg_status used `MILES_DM_CONTRACTSTATE_DIM` view as the source for Miles contract statuses. This resulted in MISSING 7 active statuses that exist in the Miles application. When comparing Snowflake output to Vertica (old production system), the row counts didn't match:
- Using DM_CONTRACTSTATE_DIM: 130 rows (missing 7 statuses)
- Using SYSENUMERATION directly: 137 rows (complete data) ✅

**Root Cause**:
Per confirmation from Miles team:
1. **All `DM_*_DIM` views in Miles database are OUTDATED and UNMAINTAINED**
2. **Source of truth is the base tables (SYSENUMERATION, etc.)**
3. **DM views have unclear/undocumented origin and logic**
4. **DM views do NOT reflect what users see in Miles application**

The DBT model was incorrectly created to use the DM view instead of following the original Pentaho transformation, which already used SYSENUMERATION correctly.

**Solution**:
ALWAYS query base tables directly - NEVER use `DM_*_DIM` views:

```sql
-- ❌ WRONG (uses outdated DM view):
FROM {{ source('bronze', 'MILES_DM_CONTRACTSTATE_DIM') }} s

-- ✅ CORRECT (uses source of truth):
FROM {{ source('bronze', 'MILES_SYSENUMERATION') }} status
INNER JOIN {{ source('bronze', 'MILES_SYSENUMERATION') }} groups
    ON groups.SYSENUMERATION_ID = status.GROUP_ENUMID
WHERE status.SYSREPATTRIBUTETYPE_ID = 185  -- Filter for contract states
```

**Key Points**:
1. **SYSENUMERATION** is the source of truth for all Miles enumerations/lookups
2. Use **SYSREPATTRIBUTETYPE_ID** to filter for specific entity types:
   - `185` = Contract states
   - Other IDs exist for different entity types (verify with Miles team)
3. **DM_*_DIM views should be treated as deprecated/legacy**

**Prevention - How to Detect Proactively**:

**For pentaho-analyzer** (Step 2):
1. When analyzing Pentaho transformations, CHECK if they use DM_*_DIM views
2. Add WARNING to pentaho_analyzed.json if DM view detected:
   ```json
   {
     "warnings": [
       {
         "severity": "WARNING",
         "file": "adq_status.ktr",
         "issue": "Uses MILES_DM_CONTRACTSTATE_DIM - verify if base table should be used instead",
         "recommendation": "Miles DM views are outdated - check if SYSENUMERATION should be used (see L-20251119-001)"
       }
     ]
   }
   ```

**For sql-translator** (Step 4):
1. When translating SQL that references `DM_*_DIM` views, add comment:
   ```sql
   -- ⚠️ WARNING: DM_CONTRACTSTATE_DIM may be outdated
   -- Consider using MILES_SYSENUMERATION directly (see L-20251119-001)
   ```

2. Check if Pentaho transformation uses DM view or base table:
   - If Pentaho uses **base table** → translate to base table (preserve original logic)
   - If Pentaho uses **DM view** → flag for review, suggest base table alternative

**For dbt-model-generator** (Step 5):
1. **CRITICAL RULE**: When generating Miles-related models, NEVER use DM_*_DIM views
2. Validation check before writing model:
   ```python
   if 'DM_' in source_table and '_DIM' in source_table and schema == 'MILES':
       raise ValueError(
           f"Miles DM view detected: {source_table}. "
           f"Use base tables instead (see L-20251119-001)"
       )
   ```

3. Always verify against original Pentaho transformation:
   - Read the .ktr file SQL
   - Compare table names
   - Ensure DBT model matches Pentaho exactly

4. Add to dbt_generation_report.json:
   ```json
   {
     "data_source_validation": {
       "miles_tables_used": ["SYSENUMERATION", "TRANSLATEDSTRING"],
       "dm_views_avoided": ["DM_CONTRACTSTATE_DIM"],
       "verified_against_pentaho": true
     }
   }
   ```

**Verification Checklist**:
- [ ] Check original Pentaho .ktr file - what table does IT use?
- [ ] If Pentaho uses base table, DBT must use same base table
- [ ] If Pentaho uses DM view, investigate if base table is better
- [ ] Consult Miles team if unsure about correct source
- [ ] Compare row counts: Vertica vs Snowflake (should match)

**Code Example**:

```sql
-- PENTAHO SOURCE (adq_status.ktr line 680-690):
SELECT
    CAST(status.SYSENUMERATION_ID AS varchar(100)) as STATUS_ID,
    status.NAME as STATUS_DESC,
    groups.NAME as GROUP_ID,
    ${MILES_SCHEMA}.GETENUMML(groups.SYSENUMERATION_ID, 4) as GROUP_DESC,
    'Miles' as source_system
FROM ${MILES_SCHEMA}.SYSENUMERATION status
INNER JOIN ${MILES_SCHEMA}.SYSENUMERATION groups
    ON groups.SYSENUMERATION_ID = status.GROUP_ENUMID
WHERE status.SYSREPATTRIBUTETYPE_ID = 185

-- DBT MODEL (WRONG - used DM view):
FROM {{ source('bronze', 'MILES_DM_CONTRACTSTATE_DIM') }} s

-- DBT MODEL (CORRECT - matches Pentaho):
FROM {{ source('bronze', 'MILES_SYSENUMERATION') }} status
INNER JOIN {{ source('bronze', 'MILES_SYSENUMERATION') }} groups
    ON groups.SYSENUMERATION_ID = status.GROUP_ENUMID
WHERE status.SYSREPATTRIBUTETYPE_ID = 185
```

**Impact of Fix**:
- Before: 130 Miles statuses (7 missing due to outdated DM view)
- After: 137 Miles statuses (complete - matches production Vertica)
- Data Quality: Now reflects actual Miles application data
- Future-proof: No dependency on unmaintained views

**Miles Team Guidance**:
> "The SYSENUMERATION table is the table which reflects what users see in the application. DM_XXXX_DIM tables are outdated and we have no clear understanding where they come from. If you can avoid using them, it will be helpful."

**Agents That Should Apply This**:
- **pentaho-analyzer**: Warn when DM views detected in Pentaho
- **sql-translator**: Flag DM views, suggest base table alternatives
- **dbt-model-generator**: BLOCK DM view usage, enforce base table pattern
- **quality-validator**: Validate no DM views in Miles models

**Reference**:
- Dimension: dim_status
- Affected model: `{dbt_repository}/models/silver/silver_adq/stg_status.sql`
- Original Pentaho: `pentaho-sources/dim_status/adq_status.ktr` (line 680-690)
- Data comparison: D_STATUS_SNOWFLAKE.csv vs D_STATUS_VERTICA.csv
- Miles team confirmation: 2025-11-19 meeting
- Row count impact: +7 previously missing statuses

**Related Learnings**:
- See L-20251029-001 (GETENUMML UDF replacement) - also applies to SYSENUMERATION queries

---

## Statistics

### By Category
- SQL_TRANSLATION: 2 (Correlated subqueries, Julian dates)
- DBT_SYNTAX: 2 (Oversimplification, Column mapping)
- DATA_QUALITY: 1 (Miles DM views outdated)
- SCHEMA_MAPPING: 1 (Incomplete table discovery)
- UDF_HANDLING: 1 (GETENUMML)
- CASE_SENSITIVITY: 1 (Lowercase columns)

### By Impact
- HIGH: 5 (Correlated subqueries, Oversimplification, Julian dates, GETENUMML UDF, Miles DM views)
- MEDIUM: 3 (Column mapping, Incomplete table discovery, Case sensitivity)
- LOW: 0

### By Agent
- dbt-model-generator: 6 learnings (Correlated subqueries, Oversimplification, Julian dates, Column mapping, Case sensitivity, Miles DM views)
- sql-translator: 5 learnings (Correlated subqueries, Julian dates, GETENUMML, Case sensitivity, Miles DM views)
- pentaho-analyzer: 2 learnings (Incomplete table discovery, Miles DM views)
- dependency-graph-builder: 1 learning (Incomplete table discovery)
- quality-validator: 1 learning (GETENUMML)

### By Migration
- dim_contract: 2 learnings (GETENUMML, Case sensitivity)
- dim_proposal: 5 learnings (Correlated subqueries, Oversimplification, Julian dates, Column mapping, Incomplete table discovery)
- dim_status: 1 learning (Miles DM views outdated)

---

## Maintenance Notes

**For learning-logger agent**:
- When adding new learnings, increment learning ID: L-YYYYMMDD-NNN
- Update statistics section after each addition
- Keep learnings sorted by date (newest first within each category)
- Mark deprecated learnings with `[DEPRECATED]` prefix if pattern changes

**For repo-analyzer agent**:
- Extract HIGH IMPACT learnings first
- Create learnings_summary.md with agent-specific guidance
- Include learning IDs in summary for traceability

---

**Next Learning ID**: L-20251119-002
