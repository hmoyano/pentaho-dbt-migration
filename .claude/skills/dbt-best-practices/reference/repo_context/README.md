# Repository Context Analysis Summary

Generated: 2025-10-27
Repository: {dbt_repository} (from project.config.json)

## Analysis Overview

This directory contains comprehensive context files extracted from the existing DBT repository. These files guide downstream agents during model generation to:
- Avoid regenerating shared infrastructure
- Reuse existing models via `{{ ref() }}`
- Follow established patterns and conventions
- Append to sources (not overwrite)

## Summary Statistics

### Models
- **Total models**: 36
  - Bronze: 1 (source_date - infrastructure)
  - Silver ADQ: 16 (staging layer)
  - Silver MAS: 16 (business logic layer)
  - Gold: 3 (dimensions)

### Macros
- **Total macros**: 2
  - convert_from_julian (Julian to Gregorian date)
  - convert_to_julian (Gregorian to Julian date)

### Sources
- **Total source tables**: 73
  - EKIP: 41 tables
  - MILES: 12 tables
  - TES: 11 tables
  - TFSLINE: 4 tables
  - PROFINANCE: 5 tables

### Tests
- **Current tests**: 0 (none defined yet)
- **Recommendation**: HIGH PRIORITY - Add basic tests

## Context Files

### 1. macros.md
**Purpose**: Documents available custom macros

**Key Content**:
- Julian date conversion macros (convert_from_julian, convert_to_julian)
- Usage examples and parameters
- Performance notes
- DBT utils package recommendations

**Use Case**: When generating SQL, use these macros instead of inline date conversion logic

### 2. models_inventory.md
**Purpose**: Complete inventory of existing models with tags and relationships

**Key Content**:
- 36 models categorized by layer
- Shared vs dimension-specific identification
- Tag analysis and patterns
- "DO NOT REGENERATE" list (12 critical shared models)
- Model naming conventions

**Use Case**: Check this BEFORE generating any model to avoid duplication

### 3. sources_inventory.md
**Purpose**: Complete list of 73 source tables already defined

**Key Content**:
- All EKIP, MILES, TES, TFSLINE, PROFINANCE tables
- Source system descriptions
- Usage patterns in existing models
- DO NOT OVERWRITE warning for sources.yml

**Use Case**: Check this BEFORE adding any source definitions

### 4. test_patterns.md
**Purpose**: Test strategy and recommended patterns

**Key Content**:
- Current test status (0 tests)
- Recommended test patterns by type
- Test coverage by layer
- Custom test patterns for this project
- Phase-based implementation plan

**Use Case**: Guide test generation for new models

### 5. project_config.md
**Purpose**: DBT project configuration analysis

**Key Content**:
- Materialization strategy by layer
- Variables defined (EKIP_HISTORY_INITIAL_DATE, INC_ID_CONTRACT_DEALERS)
- Schema organization (BRONZE, SILVER, GOLD)
- Tag conventions
- Incremental strategy patterns

**Use Case**: Ensure new models follow project-wide configurations

## Critical Findings

### Shared Infrastructure Models (DO NOT REGENERATE)

These 12 models are shared by multiple dimensions and must NEVER be regenerated:

1. source_date.sql - Date dimension
2. stg_contracts.sql - Core contract staging (incremental)
3. stg_customers.sql - Core customer staging
4. stg_customers_groups.sql - Customer grouping
5. stg_status.sql - Status reference data
6. stg_status_history.sql - Status history (incremental)
7. stg_miles_businesspartner.sql - Miles staging
8. mas_contracts.sql - Core business logic (incremental)
9. mas_status.sql - Status reference
10. mas_status_history.sql - Status history
11. mas_customers.sql - Customer ODS
12. mas_customers_groups.sql - Customer groups

### Key Patterns Identified

**Materialization Strategy**:
- Bronze: table (infrastructure)
- Silver ADQ: table (default) / incremental (large datasets)
- Silver MAS: table (default) / incremental (core models)
- Gold: incremental (dimensions with SCD Type 2)

**Tag Patterns**:
- Layer: 'silver', 'gold', 'adq', 'mas'
- System: 'ekip', 'miles', 'tes', 'profinance'
- Entity: 'contracts', 'customers', 'dealer', 'catalog'
- Type: 'incremental', 'dimension', 'reference_data'

**Incremental Strategy**:
- Merge on unique_key for upserts
- on_schema_change='sync_all_columns' for SCD Type 2

**Variable Usage**:
- EKIP_HISTORY_INITIAL_DATE for incremental loads
- INC_ID_CONTRACT_DEALERS for ID thresholds

## Usage Guidelines for Agents

### dbt-model-generator Agent

**BEFORE generating any model**:
1. Check models_inventory.md - Does model already exist?
2. If exists and in "DO NOT REGENERATE" list → Use `{{ ref() }}` instead
3. If exists but dimension-specific → Review and potentially reuse
4. If new model → Follow patterns from similar existing models

**BEFORE adding source definitions**:
1. Check sources_inventory.md - Is table already defined?
2. If yes → Use existing `{{ source('bronze', 'TABLE_NAME') }}`
3. If no → Append to existing sources.yml (don't overwrite)

**WHEN generating SQL**:
1. Check macros.md - Use convert_from_julian for EKIP dates
2. Follow materialization strategy from project_config.md
3. Apply appropriate tags based on tag patterns
4. Use variables from project_config.md

### quality-validator Agent

**Test validation**:
1. Use test_patterns.md as reference for expected test coverage
2. Priority: Validate primary key uniqueness and not_null tests
3. Check relationship tests between layers
4. Verify date logic validation for models with DATE_FROM/DATE_TO

### sql-translator Agent

**Translation guidance**:
1. Use convert_from_julian macro for EKIP Julian dates
2. Preserve custom UDFs (GETENUMML, etc.)
3. Follow Snowflake SQL patterns from existing models
4. Use `{{ source() }}` references, not hardcoded table names

## Model Dependency Patterns

### Common Dependency Chains

**Contract Flow**:
```
EKIP_AFFAIRE (source)
  ↓
stg_contracts (silver ADQ)
  ↓
mas_contracts (silver MAS)
  ↓
d_approval_level (gold)
```

**Customer Flow**:
```
EKIP_TIERS (source)
  ↓
stg_customers (silver ADQ)
  ↓
mas_customers (silver MAS)
  ↓
d_customer (gold)
```

**Dealer Flow**:
```
Multiple sources (EKIP, TES, PROFINANCE)
  ↓
Multiple stg_* models
  ↓
Multiple mas_* models
  ↓
d_dealer (gold)
```

### Shared Dependencies

Almost all models depend on:
- source_date (date dimension)
- mas_contracts (contract core)
- mas_customers (customer core)
- mas_status (status reference)

## Priority Recommendations

### Immediate Actions

1. **Add basic tests** (PRIMARY KEY uniqueness/not_null on all gold dimensions)
2. **Install dbt_utils package** (if not already installed)
3. **Document test strategy** in team documentation

### Short-term Improvements

1. **Add relationship tests** between layers
2. **Implement source freshness checks** for critical tables
3. **Add accepted_values tests** for enumerated fields

### Long-term Enhancements

1. **Comprehensive test coverage** (all recommended patterns)
2. **Documentation improvements** (especially TES table descriptions)
3. **Performance optimization** (materialization strategy review)

## Files in This Directory

- **README.md** (this file) - Summary and usage guide
- **macros.md** - Custom macro documentation
- **models_inventory.md** - Complete model inventory
- **sources_inventory.md** - Source table definitions
- **test_patterns.md** - Testing recommendations
- **project_config.md** - Project configuration analysis

## Maintenance

These context files should be regenerated when:
- New models are added to the repository
- Source tables are added or modified
- Project configuration changes
- New macros are created

**Regeneration command**: Run repo-analyzer agent again

## Version History

- **v1.0** (2025-10-27): Initial analysis
  - 36 models inventoried
  - 73 source tables documented
  - 2 macros documented
  - Test strategy defined
  - Project config analyzed
