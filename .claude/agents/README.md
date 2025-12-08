# Agents Catalog

13 AI-powered agents for Pentaho-to-DBT migration.

## Main Pipeline (6)

| Agent | Step | Purpose |
|-------|------|---------|
| `repo-analyzer` | 0.5 | Analyze existing DBT repo |
| `pentaho-analyzer` | 2 | Analyze Pentaho, resolve variables |
| `dependency-graph-builder` | 3 | Build execution order |
| `sql-translator` | 4 | Oracle to Snowflake SQL |
| `dbt-model-generator` | 5 | Generate DBT models |
| `quality-validator` | 6 | Validate with dbt commands |

## Helpers (5)

| Agent | When Called |
|-------|-------------|
| `pentaho-deep-analyzer` | When analyzer needs detail |
| `pentaho-cross-reference` | When unknown vars found |
| `dependency-resolver` | When cycles detected |
| `sql-function-lookup` | When unknown functions |
| `dbt-validator-fixer` | When validation fails |

## Utilities (2)

| Agent | Purpose |
|-------|---------|
| `migration-docs-generator` | Generate REFERENCE.md, CHANGELOG.md |
| `learning-logger` | Log lessons for future migrations |

## Flow

```
repo-analyzer → pentaho-analyzer → dependency-graph-builder
    → sql-translator → dbt-model-generator → quality-validator
        → migration-docs-generator
```

All agents follow `_COMMON_PRACTICES.md`.
