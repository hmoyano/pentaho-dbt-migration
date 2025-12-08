# CRITICAL: Table Naming Conventions

**THESE RULES ARE MANDATORY AND NON-NEGOTIABLE**

## Snowflake Table Names

All table names in Snowflake follow this pattern from `config/schema_registry.json`:

### External Sources (Bronze Layer)

**Format:** `{SCHEMA_PREFIX}_{TABLE_NAME}` (ALL UPPERCASE)

**Examples:**
- `EKIP_AFFAIRE` (not `affaire` or `ekip_affaire`)
- `EKIP_LIB_ACODIFS` (not `lib_acodifs`)
- `MILES_DM_CONTRACTSTATE_DIM` (not `dm_contractstate_dim`)
- `TFSLINE_POS_FINANCIAL` (not `pos_financial`)
- `EKIP_TFS_CRITOBJ_HIST_0TES` (not `critobj_hist_0tes`)

### Verification Source

**File:** `config/TABLE_COUNT.csv`

This file contains the ACTUAL table names in Snowflake. Always reference this file to verify correct table names.

Example entries:
```csv
TABLE_NAME,ROW_COUNT
EKIP_AFFAIRE,1280795
EKIP_LIB_ACODIFS,633166
MILES_DM_CONTRACTSTATE_DIM,16
TFSLINE_POS_FINANCIAL,5306306
```

## DBT Source References

**CORRECT FORMAT:**
```sql
{{ source('ekip', 'EKIP_AFFAIRE') }}
{{ source('ekip', 'EKIP_LIB_ACODIFS') }}
{{ source('miles', 'MILES_DM_CONTRACTSTATE_DIM') }}
{{ source('tfsline', 'TFSLINE_POS_FINANCIAL') }}
```

**INCORRECT FORMAT (DO NOT USE):**
```sql
{{ source('ekip', 'affaire') }}              -- ❌ WRONG
{{ source('ekip', 'lib_acodifs') }}          -- ❌ WRONG
{{ source('miles', 'dm_contractstate_dim') }} -- ❌ WRONG
```

## Bronze Sources File

**File:** `models/bronze/_sources.yml`

All table names in the sources file MUST be uppercase with prefix:

```yaml
sources:
  - name: ekip
    database: TFSES_ANALYTICS
    schema: TFS_BRONZE
    tables:
      - name: EKIP_AFFAIRE          # ✓ CORRECT
      - name: EKIP_LIB_ACODIFS      # ✓ CORRECT

  - name: miles
    database: TFSES_ANALYTICS
    schema: TFS_BRONZE
    tables:
      - name: MILES_DM_CONTRACTSTATE_DIM  # ✓ CORRECT
```

**NOT like this:**
```yaml
sources:
  - name: ekip
    tables:
      - name: affaire               # ❌ WRONG
      - name: lib_acodifs           # ❌ WRONG
```

## Schema Mapping from schema_registry.json

### External Schemas (Bronze Layer)

| Pentaho Variable | Snowflake Schema | Database | Prefix | Layer |
|-----------------|------------------|----------|---------|-------|
| ${EKIP_SCHEMA} | TFS_BRONZE | TFSES_ANALYTICS | EKIP_ | bronze |
| ${MILES_SCHEMA} | TFS_BRONZE | TFSES_ANALYTICS | MILES_ | bronze |
| ${TFSLINE_SCHEMA} | TFS_BRONZE | TFSES_ANALYTICS | TFSLINE_ | bronze |
| ${EKIP_TFS_SCHEMA} | TFS_BRONZE | TFSES_ANALYTICS | EKIP_TFS_ | bronze |
| ${PROFINANCE_SCHEMA} | TFS_BRONZE | TFSES_ANALYTICS | PROFINANCE_ | bronze |

### Internal Schemas (Silver/Gold Layers)

| Pentaho Variable | Snowflake Schema | Database | Layer |
|-----------------|------------------|----------|-------|
| ${ODS_SCHEMA} | TFS_SILVER | TFSES_ANALYTICS | silver |
| ${DW_SCHEMA} | TFS_GOLD | TFSES_ANALYTICS | gold |

**Internal table names (silver/gold) DO NOT use prefixes:**
- Silver ADQ: `STG_EKIP_CONTRACTS` (not `TFS_SILVER_STG_EKIP_CONTRACTS`)
- Silver MAS: `MAS_CONTRACTS` (not `TFS_SILVER_MAS_CONTRACTS`)
- Gold: `D_APPROVAL_LEVEL` (not `TFS_GOLD_D_APPROVAL_LEVEL`)

## Agent Requirements

### When Generating DBT Models

1. **ALWAYS read `config/TABLE_COUNT.csv`** to verify table names
2. **ALWAYS use UPPERCASE with PREFIX** for external source tables
3. **ALWAYS check schema_registry.json** for schema mappings
4. **ALWAYS update `models/bronze/_sources.yml`** with correct uppercase table names
5. **NEVER use lowercase table names** in source() references

### When Translating SQL

Convert Pentaho table references to DBT source() calls:

**Pentaho SQL:**
```sql
SELECT * FROM ${EKIP_SCHEMA}.AFFAIRE
```

**Translated to DBT:**
```sql
SELECT * FROM {{ source('ekip', 'EKIP_AFFAIRE') }}
```

**NOT:**
```sql
SELECT * FROM {{ source('ekip', 'affaire') }}  -- ❌ WRONG
```

## Common Mistakes to Avoid

1. ❌ Using lowercase table names: `{{ source('ekip', 'affaire') }}`
2. ❌ Omitting the schema prefix: `{{ source('ekip', 'AFFAIRE') }}`
3. ❌ Using mixed case: `{{ source('ekip', 'Ekip_Affaire') }}`
4. ❌ Adding extra prefixes: `{{ source('ekip', 'EKIP_EKIP_AFFAIRE') }}`

## Validation Checklist

Before generating any DBT model:
- [ ] Read `config/TABLE_COUNT.csv` to verify table names
- [ ] Check all source() calls use UPPERCASE with PREFIX
- [ ] Verify table names exist in TABLE_COUNT.csv
- [ ] Confirm schema mappings from schema_registry.json
- [ ] Validate all sources defined in `models/bronze/_sources.yml`

## References

- **Table names:** `config/TABLE_COUNT.csv`
- **Schema mappings:** `config/schema_registry.json`
- **Source definitions:** `models/bronze/_sources.yml`

**CRITICAL:** Failure to follow these conventions will cause DBT compilation errors and runtime failures in Snowflake.
