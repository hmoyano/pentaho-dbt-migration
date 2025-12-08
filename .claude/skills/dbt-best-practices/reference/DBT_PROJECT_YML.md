# dbt_project.yml Configuration

## Overview

The `dbt_project.yml` file is **essential** for running DBT models. It configures project settings, model materializations, and layer-specific configurations.

---

## Project Configuration

### Basic Settings

```yaml
name: 'tfses_3030'
version: '1.0.0'
config-version: 2
profile: 'default'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"
```

### Required Variables

```yaml
vars:
  # History tracking variables (used in incremental models)
  ekip_history_initial_date: '2020-01-01'
  dwh_history_initial_date: '2020-01-01'

  # Language ID for translations (4 = default language)
  default_language_id: 4
```

---

## Model Layer Configuration

### Bronze Layer (Sources)

```yaml
models:
  tfses_3030:
    bronze:
      +materialized: view
      +tags: ['bronze', 'source']
```

**Purpose:** Source definitions only (no SQL models)
**Location:** `models/bronze/_sources.yml`

### Silver ADQ Layer (Staging)

```yaml
    silver:
      silver_adq:
        +materialized: view  # Default to view
        +tags: ['silver', 'silver_adq', 'staging']

        # Override materialization for specific high-volume models
        stg_ekip_contracts:
          +materialized: table
          +tags: ['silver', 'silver_adq', 'staging', 'high_volume']

        stg_ekip_status_history:
          +materialized: table
          +tags: ['silver', 'silver_adq', 'staging', 'high_volume']
```

**Purpose:** Raw data extraction with minimal transformation
**Location:** `models/silver/silver_adq/stg_*.sql`
**Materialization:**
- Default: `view`
- High-volume (>10M rows): `table`

### Silver MAS Layer (Business Logic)

```yaml
      silver_mas:
        +materialized: table  # Always table for business logic
        +tags: ['silver', 'silver_mas', 'business_logic']
```

**Purpose:** Business logic and transformations
**Location:** `models/silver/silver_mas/mas_*.sql`
**Materialization:** Always `table`

### Gold Layer (Analytical)

```yaml
    gold:
      +materialized: table  # Default for dimensions
      +tags: ['gold', 'analytical']

      # Dimensions
      d_approval_level:
        +materialized: table
        +tags: ['gold', 'dimension', 'dim_approval_level']

      d_date:
        +materialized: table
        +tags: ['gold', 'dimension', 'dim_date', 'prerequisite']

      # Facts (if any) - use incremental
      # f_sales:
      #   +materialized: incremental
      #   +unique_key: 'surrogate_key'
      #   +on_schema_change: 'fail'
      #   +tags: ['gold', 'fact']
```

**Purpose:** Final analytical models (dimensions and facts)
**Location:** `models/gold/d_*.sql`, `models/gold/f_*.sql`
**Materialization:**
- Dimensions: `table`
- Facts: `incremental` (for large datasets)

---

## Complete Example

```yaml
# Name your project! Project names should contain only lowercase characters
# and underscores. A good package name should reflect your organization's
# name or the intended use of these models
name: 'tfses_3030'
version: '1.0.0'
config-version: 2

# This setting configures which "profile" dbt uses for this project.
profile: 'default'

# These configurations specify where dbt should look for different types of files.
model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

# Configure variables used across models (for Pentaho migration)
vars:
  # History tracking variables (used in incremental models)
  ekip_history_initial_date: '2020-01-01'
  dwh_history_initial_date: '2020-01-01'
  # Language ID for translations (4 = default language)
  default_language_id: 4

# Configuring models
models:
  tfses_3030:
    # Applies to all files under models/example/
    example:
      +materialized: table

    # Bronze layer - source definitions only (no SQL models)
    bronze:
      +materialized: view
      +tags: ['bronze', 'source']

    # Silver ADQ layer - staging models
    silver:
      silver_adq:
        +materialized: view  # Default to view
        +tags: ['silver', 'silver_adq', 'staging']

        # Override materialization for specific high-volume models
        stg_ekip_contracts:
          +materialized: table
          +tags: ['silver', 'silver_adq', 'staging', 'high_volume']

        stg_ekip_status_history:
          +materialized: table
          +tags: ['silver', 'silver_adq', 'staging', 'high_volume']

      # Silver MAS layer - business logic models
      silver_mas:
        +materialized: table  # Always table for business logic
        +tags: ['silver', 'silver_mas', 'business_logic']

    # Gold layer - dimensional and fact models
    gold:
      +materialized: table  # Default for dimensions
      +tags: ['gold', 'analytical']

      # Dimensions
      d_approval_level:
        +materialized: table
        +tags: ['gold', 'dimension', 'dim_approval_level']

      d_date:
        +materialized: table
        +tags: ['gold', 'dimension', 'dim_date', 'prerequisite']
```

---

## Agent Requirements

### When Generating a New Dimension

**The dbt-model-generator agent MUST:**

1. **Check if dbt_project.yml exists**
   ```python
   if Path("dbt_project.yml").exists():
       # Read and update existing file
   else:
       # Create new file
   ```

2. **Add dimension-specific configuration** to the appropriate section:

   For a new dimension like `dim_customer`:
   ```yaml
   gold:
     d_customer:
       +materialized: table
       +tags: ['gold', 'dimension', 'dim_customer']
   ```

3. **Add model-specific overrides** for high-volume silver_adq models:
   ```yaml
   silver_adq:
     stg_ekip_customers:  # If >10M rows
       +materialized: table
       +tags: ['silver', 'silver_adq', 'staging', 'high_volume']
   ```

4. **Update variables** if needed:
   ```yaml
   vars:
     customer_history_initial_date: '2020-01-01'
   ```

### How to Update dbt_project.yml

Use the Edit tool to add new sections:

```python
# Read the file
with open('dbt_project.yml', 'r') as f:
    content = f.read()

# Find the gold section and add new dimension
# ... use Edit tool with proper YAML indentation
```

**Important:**
- Preserve existing configurations
- Maintain proper YAML indentation (2 spaces)
- Keep dimension tags consistent
- Use snake_case for model names

---

## Materialization Decision Tree

### Silver ADQ (stg_* models)

```
Is row count > 10M?
├─ YES → materialized: table
└─ NO  → materialized: view (default)
```

Check row count in `config/TABLE_COUNT.csv`:
```csv
TABLE_NAME,ROW_COUNT
EKIP_AFFAIRE,1280795        → view (< 10M)
EKIP_TABSIMUL,69954478      → table (> 10M)
```

### Silver MAS (mas_* models)

```
Always → materialized: table
```

Business logic layer always uses tables for:
- Performance (pre-computed joins)
- Consistency (stable intermediate results)
- Testing (easier to test materialized tables)

### Gold (d_*, f_* models)

```
Is it a dimension?
├─ YES → materialized: table
└─ NO (fact table) →
    ├─ Large, append-only? → materialized: incremental
    └─ Small, full refresh? → materialized: table
```

---

## Running DBT Commands

### Compile All Models
```bash
dbt compile
```

### Run Specific Dimension
```bash
dbt run --select tag:dim_approval_level
```

### Run Specific Layer
```bash
dbt run --select tag:silver_adq
dbt run --select tag:silver_mas
dbt run --select tag:gold
```

### Run in Execution Order
```bash
dbt run --select d_date                    # Step 1: Prerequisites
dbt run --select tag:silver_adq            # Step 2: Staging
dbt run --select tag:silver_mas            # Step 3: Business logic
dbt run --select tag:gold                  # Step 4: Dimensions
```

---

## Validation Checklist

Before committing dbt_project.yml changes:

- [ ] YAML syntax is valid (proper indentation)
- [ ] Project name matches existing (`tfses_3030`)
- [ ] All required variables are defined
- [ ] Bronze, silver_adq, silver_mas, gold sections exist
- [ ] Each dimension has proper tags
- [ ] High-volume models marked as `table` materialization
- [ ] Model names use snake_case
- [ ] No duplicate model configurations

---

## Common Mistakes

1. ❌ **Wrong indentation** - YAML is indent-sensitive (use 2 spaces)
2. ❌ **Missing tags** - Every model needs layer and dimension tags
3. ❌ **Wrong materialization** - silver_mas must always be `table`
4. ❌ **Duplicate model names** - Each model can only be configured once
5. ❌ **Hardcoded values** - Use variables for dates, IDs, etc.

---

## References

- **Current file:** `dbt_project.yml` (project root)
- **Row counts:** `config/TABLE_COUNT.csv`
- **DBT docs:** https://docs.getdbt.com/reference/dbt_project.yml

**CRITICAL:** The dbt_project.yml file is required for DBT to run. Always ensure it exists and is properly configured before running DBT commands.
