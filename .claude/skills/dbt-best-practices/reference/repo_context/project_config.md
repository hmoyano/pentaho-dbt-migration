# Project Configuration

Generated: 2025-10-27
Repository: {dbt_repository} (from project.config.json)

## Project Metadata

**Project Name**: tfses_3030
**Version**: 1.0.0
**Config Version**: 2
**Profile**: default
**DBT Cloud Project ID**: 12141

## Directory Structure

### Model Paths
- **models**: `models/`
- **analyses**: `analyses/`
- **tests**: `tests/`
- **seeds**: `seeds/`
- **macros**: `macros/`
- **snapshots**: `snapshots/`

### Output Paths
- **target**: `target/` (compiled SQL and artifacts)
- **clean-targets**: `target/`, `dbt_packages/`

## Model Configurations

### Silver Layer (silver/)
```yaml
models:
  tfses_3030:
    silver:
      +materialized: table
      +schema: silver
```

**Configuration Details**:
- **Default Materialization**: table
- **Schema Override**: silver (will create SILVER schema in Snowflake)
- **Applies to**:
  - models/silver/silver_adq/ (16 models)
  - models/silver/silver_mas/ (16 models)

**Overrides in Models**:
- stg_contracts: incremental (merge on contract_id_ekip)
- stg_status_history: incremental (merge strategy)
- stg_early_terminations: incremental
- mas_contracts: incremental (merge on CONTRACT_ID_EKIP)

### Gold Layer (gold/)
```yaml
models:
  tfses_3030:
    gold:
      +materialized: table
      +schema: gold
```

**Configuration Details**:
- **Default Materialization**: table
- **Schema Override**: gold (will create GOLD schema in Snowflake)
- **Applies to**:
  - models/gold/ (3 dimension models)

**Overrides in Models**:
- d_approval_level: incremental (merge on APPROVAL_LEVEL_NK)
- d_customer: incremental (merge on CUSTOMER_NK)
- d_dealer: incremental (merge on DEALER_ID)

### Bronze Layer (bronze/)

**No explicit configuration** (uses DBT defaults)
- **Default Materialization**: view (DBT default)
- **Schema**: Same as target schema
- **Models**: source_date.sql (overrides to table in model config)

## Seed Configurations

### mas_provinces
```yaml
seeds:
  tfses_3030:
    mas_provinces:
      schema: silver
      +quote_columns: true
      +column_types:
        PROVINCE_ID: VARCHAR(2)
        PROVINCE_DESCRIPTION: VARCHAR(25)
```

**Configuration Details**:
- **Schema**: silver (stored in SILVER schema)
- **Quote Columns**: true (preserves case sensitivity)
- **Column Types**: Explicit typing for PROVINCE_ID and PROVINCE_DESCRIPTION
- **Purpose**: Spanish province reference data

## Project Variables

### Configured Variables
```yaml
vars:
  EKIP_HISTORY_INITIAL_DATE: '20200101'
  INC_ID_CONTRACT_DEALERS: 0
```

**Variable Usage**:

1. **EKIP_HISTORY_INITIAL_DATE**: '20200101'
   - Purpose: Initial date for incremental history loads
   - Used in: Status history models, incremental contract loads
   - Format: String 'YYYYMMDD'

2. **INC_ID_CONTRACT_DEALERS**: 0
   - Purpose: Incremental ID threshold for contract_dealers
   - Used in: mas_contract_dealers incremental logic
   - Type: Integer

**Additional Variables Referenced in Models** (not in dbt_project.yml):
- `process_id`: Used in mas_contracts PROCESS_ID field (default 'dbt_run')
- `inc_date_status_history`: Used in stg_contracts incremental filter

**Accessing Variables in Models**:
```sql
{{ var('EKIP_HISTORY_INITIAL_DATE') }}
{{ var('process_id', "'dbt_run'") }}  -- with default
```

## Materialization Strategy by Layer

### Bronze Layer
- **source_date**: table (infrastructure model, rarely changes)
- **Philosophy**: Single date dimension model, no sources defined here

### Silver ADQ Layer
- **Default**: table (set in dbt_project.yml)
- **Overrides for incremental**:
  - stg_contracts (large, frequently updated)
  - stg_status_history (event log)
  - stg_early_terminations (event log)
  - stg_contract_month_end (time-series data)
- **Philosophy**: Raw staging, table for performance, incremental for large/append-only

### Silver MAS Layer
- **Default**: table (set in dbt_project.yml)
- **Overrides for incremental**:
  - mas_contracts (core business logic, large dataset)
- **Philosophy**: Business logic layer, mostly full refresh tables

### Gold Layer
- **Default**: table (set in dbt_project.yml)
- **Overrides for incremental**:
  - All dimensions use incremental (d_approval_level, d_customer, d_dealer)
- **Philosophy**: SCD Type 2 dimensions, incremental merge strategy

## Incremental Strategy Patterns

### Merge Strategy (Most Common)
```sql
{{ config(
    materialized='incremental',
    unique_key='CONTRACT_ID_EKIP',
    incremental_strategy='merge'
) }}
```

**Used in**:
- stg_contracts
- mas_contracts
- d_approval_level
- d_customer
- d_dealer

**Behavior**: Updates existing rows, inserts new rows (upsert pattern)

### SCD Type 2 Pattern
```sql
{{ config(
    materialized='incremental',
    unique_key='CUSTOMER_NK',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns'
) }}
```

**Used in**:
- d_customer
- d_dealer

**Features**:
- Tracks history with DATE_FROM, DATE_TO
- VERSION and LAST_VERSION flags
- Handles schema evolution with sync_all_columns

## Schema Organization

### Snowflake Schema Structure
```
TFSES_ANALYTICS (database)
├── TFS_BRONZE (sources)
│   ├── EKIP_* tables
│   ├── MILES_* tables
│   ├── TES_* tables
│   ├── TFSLINE_* tables
│   └── PROFINANCE_* tables
├── SILVER (silver layer models)
│   ├── stg_* models (ADQ)
│   └── mas_* models (MAS)
└── GOLD (gold layer models)
    ├── d_* dimensions
    └── f_* facts (none yet)
```

## Tag Conventions

### Layer Tags
- 'bronze', 'silver', 'gold', 'adq', 'mas'

### System Tags
- 'ekip', 'miles', 'tes', 'profinance', 'tfsadmin'

### Entity Tags
- 'contracts', 'customers', 'dealer', 'catalog', 'status'

### Type Tags
- 'incremental', 'dimension', 'dimensional', 'reference_data'

**Tag Usage**:
- Selection: `dbt run --select tag:silver`
- Exclusion: `dbt run --exclude tag:disabled`
- Documentation: Group models by business domain

## Important Settings

### Config Version 2
- Uses modern DBT config syntax
- Supports model-level configurations
- Enables schema and alias customization

### DBT Cloud Integration
- Project ID: 12141
- Enables DBT Cloud features
- Cloud IDE and scheduling support

### Quote Columns Strategy
- **Seeds**: +quote_columns: true (preserves case)
- **Models**: Not quoted by default
- **Snowflake**: Case-insensitive by default

### On Schema Change
- **Most models**: Default (no sync)
- **SCD Type 2 models**: sync_all_columns (d_customer, d_dealer)
- **Philosophy**: Explicit schema evolution for dimensions

## Package Dependencies

**Status**: No packages.yml file found in repository

**Recommended Packages**:
```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
  - package: calogica/dbt_expectations
    version: 0.10.0
```

**Usage in Models**:
- Models may reference dbt_utils macros (surrogate_key, etc.)
- Verify package installation before running models

## Performance Optimizations

### Table Materialization
- **When**: Default for silver and gold layers
- **Why**: Faster query performance, full control over logic
- **Trade-off**: Longer build times, more storage

### Incremental Materialization
- **When**: Large datasets (contracts, status history)
- **Why**: Faster incremental builds, handles large data volumes
- **Trade-off**: More complex logic, requires careful testing

### View Materialization
- **When**: Not used (except default for unmaterialized models)
- **Why**: N/A - project prefers table/incremental for performance

## Development Workflow Settings

### Target Path
- Compiled SQL: `target/compiled/`
- Run results: `target/run/`
- Manifest: `target/manifest.json`

### Clean Targets
- Removes: target/, dbt_packages/
- Command: `dbt clean`

## Configuration Best Practices Applied

1. **Layer Separation**: Clear bronze/silver/gold schema structure
2. **Materialization Strategy**: Appropriate for each layer (incremental for large data)
3. **Schema Organization**: Separate schemas for each layer
4. **Variable Usage**: Centralized configuration for dates and IDs
5. **Seed Management**: Explicit typing and quoting for reference data

## Configuration Gaps/Recommendations

### Missing Configurations

1. **No packages.yml**: Should define dbt_utils if used
2. **No docs configuration**: Could specify docs paths
3. **No test configuration**: Could set test severity levels
4. **No snapshot configuration**: If SCD snapshots needed
5. **No source freshness**: Should add for critical sources

### Recommended Additions

```yaml
# Add to dbt_project.yml

on-run-start:
  - "{{ log('Starting dbt run', info=True) }}"

on-run-end:
  - "{{ log('Completed dbt run', info=True) }}"

tests:
  tfses_3030:
    +severity: error  # All tests fail the build

sources:
  tfses_3030:
    bronze:
      +freshness:
        warn_after: {count: 24, period: hour}
        error_after: {count: 48, period: hour}
```

## Migration Considerations

When migrating new dimensions:

1. **Follow layer conventions**: Use silver (table/incremental) and gold (incremental)
2. **Use existing variables**: Leverage EKIP_HISTORY_INITIAL_DATE for incremental loads
3. **Apply tags**: Add layer, system, and entity tags
4. **Schema placement**: Place models in appropriate silver_adq, silver_mas, or gold folders
5. **Incremental strategy**: Use merge for upserts, append for event logs
6. **On schema change**: Use sync_all_columns for SCD Type 2 dimensions

## Configuration Stability

**Current State**: Stable, production-ready configuration
**Versioning**: Config version 2 (modern DBT)
**Changes Frequency**: Low (core configuration rarely changes)
**Risk Level**: Low (well-structured, follows best practices)
