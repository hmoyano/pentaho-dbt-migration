# DBT Naming Conventions (Consolidated)

Complete naming standards for the Pentaho to DBT migration.

---

## CRITICAL: Table Naming in Snowflake

**MANDATORY RULES:**

### External Sources (Bronze)
All table names: `{SCHEMA_PREFIX}_{TABLE_NAME}` (UPPERCASE)

```sql
-- CORRECT
{{ source('ekip', 'EKIP_AFFAIRE') }}
{{ source('miles', 'MILES_DM_CONTRACTSTATE_DIM') }}

-- WRONG
{{ source('ekip', 'affaire') }}  -- lowercase
{{ source('ekip', 'AFFAIRE') }}  -- missing prefix
```

### Verification
Always check `config/TABLE_COUNT.csv` for actual table names.

---

## File Mapping: Pentaho → DBT

| Pentaho File | DBT Model | Layer |
|-------------|-----------|-------|
| `adq_*.ktr` | `stg_*.sql` | Silver ADQ |
| `mas_*.kjb` | `mas_*.sql` | Silver MAS |
| `d_*.ktr` | `d_*.sql` | Gold |
| `f_*.ktr` | `f_*.sql` | Gold |

### Cleanup Steps

1. Remove `adq_` prefix
2. Remove numeric prefixes (`_01_`, `_1_`)
3. Remove `ekip_` for common entities
4. Add `stg_` prefix

**Examples:**
```
adq_ekip_01_status_history.ktr → stg_status_history.sql
adq_ekip_contracts.ktr → stg_contracts.sql
adq_miles_businesspartner.ktr → stg_miles_businesspartner.sql
mas_1_contracts.kjb → mas_contracts.sql
d_customer.ktr → d_customer.sql
```

---

## Column Case by Layer

| Layer | Case | Example |
|-------|------|---------|
| Silver ADQ | lowercase | `contract_id`, `dbt_loaded_at` |
| Silver MAS | UPPERCASE | `CONTRACT_ID`, `PROCESS_DATE` |
| Gold | UPPERCASE | `CUSTOMER_NK`, `DATE_FROM` |

---

## Column Patterns

| Type | Pattern | Example |
|------|---------|---------|
| Primary Key | `<entity>_id` | `customer_id` |
| Surrogate Key | `<entity>_key` | `customer_key` |
| Foreign Key | `<referenced>_id` | `contract_id` |
| Boolean | `is_<state>` | `is_active` |
| Date | `<event>_date` | `created_date` |
| Timestamp | `<event>_at` | `updated_at` |
| Amount | `<measure>_amount` | `total_amount` |

---

## Tags (Atomic)

```sql
-- CORRECT (atomic)
tags=['silver', 'adq', 'dim_approval_level']

-- WRONG (combined)
tags=['silver_adq']
```

---

## Directory Structure

```
models/
├── bronze/_sources.yml
├── silver/
│   ├── silver_adq/stg_*.sql, _models.yml
│   └── silver_mas/mas_*.sql, _models.yml
└── gold/d_*.sql, f_*.sql, _models.yml
```

---

## Quick Reference

**Model Prefixes:**
- `stg_` = Silver ADQ (staging)
- `mas_` = Silver MAS (master)
- `d_` = Gold dimension
- `f_` = Gold fact

**Source Pattern:**
```sql
{{ source('bronze', 'PREFIX_TABLENAME') }}
```

See individual files for detailed rules:
- `naming_conventions.md` - Full column naming guide
- `naming_cleanup_rules.md` - Pentaho filename cleanup
- `CRITICAL_NAMING_CONVENTIONS.md` - Snowflake table names
