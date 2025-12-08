---
name: oracle-snowflake-rules
description: Comprehensive Oracle to Snowflake SQL translation rules and function mappings
---

# Oracle to Snowflake Translation Rules

## Purpose

This skill provides authoritative reference documentation for translating Oracle SQL to Snowflake SQL. It serves as a knowledge base for the sql-translator subagent and other tools that need to convert Pentaho Oracle queries to Snowflake-compatible DBT models.

## What This Skill Provides

- **Function Mappings**: Complete Oracle → Snowflake function conversion table
- **Syntax Rules**: Oracle-specific syntax patterns and their Snowflake equivalents
- **Custom Functions**: Project-specific UDFs that must be preserved
- **Best Practices**: Guidelines for idiomatic Snowflake SQL

## Structure

```
oracle-snowflake-rules/
├── SKILL.md (this file)
└── reference/
    ├── function_mappings.md    (Function conversion reference)
    ├── syntax_rules.md          (Syntax pattern translations)
    └── custom_functions.md      (Project-specific functions)
```

## When to Use This Skill

Use this skill when:
- Translating Oracle SQL queries to Snowflake
- Reviewing translated queries for correctness
- Understanding function equivalencies
- Handling Oracle-specific syntax patterns
- Identifying custom functions that should NOT be translated

**Don't use this skill for:**
- Actual SQL translation (use sql-translator subagent)
- Performance optimization (use separate optimization tools)
- Schema design decisions

## Key Translation Principles

### 1. Function Equivalency
Oracle and Snowflake share many similar functions, but with different names or syntax. Always consult `reference/function_mappings.md` for the correct mapping.

### 2. Syntax Modernization
Oracle supports legacy syntax (like `(+)` for outer joins). Snowflake requires modern ANSI SQL. See `reference/syntax_rules.md` for patterns.

### 3. Custom Function Preservation
Project-specific UDFs must NEVER be translated. They are already defined in Snowflake and should be used as-is. See `reference/custom_functions.md`.

### 4. Case Sensitivity
- Oracle: Case-insensitive by default
- Snowflake: Case-insensitive by default, but uppercase is convention
- **Best Practice**: Use UPPERCASE for SQL keywords and identifiers

### 5. Schema Qualification
Always qualify table names with schema, especially when using variables:
```sql
-- Oracle
FROM ${EKIP_SCHEMA}.CONTRACTS

-- Snowflake (same, but ensure schema variable is resolved)
FROM {{ var('ekip_schema') }}.CONTRACTS
```

## Translation Workflow

1. **Parse** the Oracle query to identify functions and syntax patterns
2. **Map** Oracle functions to Snowflake equivalents using function_mappings.md
3. **Transform** syntax patterns using syntax_rules.md
4. **Preserve** custom functions listed in custom_functions.md
5. **Validate** the translated query for correctness

## Important Caveats

### Variables
Oracle Pentaho variables like `${VARIABLE_NAME}` need to be converted to DBT variables:
```sql
-- Oracle/Pentaho
WHERE date >= to_date('${START_DATE}', 'YYYYMMDD')

-- Snowflake/DBT
WHERE date >= to_date('{{ var("start_date") }}', 'YYYYMMDD')
```

### ROWNUM
Oracle's `ROWNUM` pseudo-column must be replaced with window functions:
```sql
-- Oracle
WHERE ROWNUM <= 10

-- Snowflake
QUALIFY ROW_NUMBER() OVER (ORDER BY column) <= 10
```

### CONNECT BY
Oracle's hierarchical queries require recursive CTEs in Snowflake:
```sql
-- Oracle
START WITH parent_id IS NULL
CONNECT BY PRIOR id = parent_id

-- Snowflake
WITH RECURSIVE hierarchy AS (
  SELECT id, parent_id, 1 as level
  FROM table
  WHERE parent_id IS NULL
  UNION ALL
  SELECT t.id, t.parent_id, h.level + 1
  FROM table t
  JOIN hierarchy h ON t.parent_id = h.id
)
```

## Reference Files

### function_mappings.md
Complete listing of Oracle functions and their Snowflake equivalents, organized by category:
- String functions
- Date/time functions
- Numeric functions
- Conversion functions
- Aggregate functions
- Analytical functions

### syntax_rules.md
Oracle syntax patterns that need transformation:
- Outer join operators (`(+)`)
- DUAL table references
- Date arithmetic
- Sequence usage
- Hierarchical queries (CONNECT BY)

### custom_functions.md
Project-specific Snowflake UDFs that must be preserved:
- GETENNUML
- Other custom functions from your schema registry

## Usage Example

When the sql-translator subagent encounters:
```sql
SELECT
  NVL(contract_id, -1) as id,
  TO_CHAR(created_date, 'YYYY-MM-DD') as created,
  MONTHS_BETWEEN(end_date, start_date) as duration
FROM ${EKIP_SCHEMA}.CONTRACTS
WHERE created_date >= ADD_MONTHS(SYSDATE, -12)
  AND ROWNUM <= 100
```

It references this skill to translate to:
```sql
SELECT
  COALESCE(contract_id, -1) as id,
  TO_CHAR(created_date, 'YYYY-MM-DD') as created,
  DATEDIFF(MONTH, start_date, end_date) as duration
FROM {{ var('ekip_schema') }}.CONTRACTS
WHERE created_date >= DATEADD(MONTH, -12, CURRENT_TIMESTAMP())
QUALIFY ROW_NUMBER() OVER (ORDER BY created_date DESC) <= 100
```

## Version Compatibility

- **Oracle**: Tested with Oracle 11g, 12c, 19c syntax
- **Snowflake**: Compatible with current Snowflake SQL syntax
- **DBT**: Assumes DBT 1.x variable syntax

## Related Resources

- [Snowflake Oracle to Snowflake Migration Guide](https://docs.snowflake.com/en/user-guide/migrating-from-oracle)
- [DBT Jinja Templating](https://docs.getdbt.com/reference/dbt-jinja-functions)
- Project schema_registry.json for variable mappings
