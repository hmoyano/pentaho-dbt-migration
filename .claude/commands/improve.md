---
description: Test Pentaho to DBT improvements locally without git operations
---

# Pentaho to DBT Improvement Tester (Local)

You are testing Pentaho to DBT improvements for a dimension LOCALLY (no git operations).

## User Request

The user wants to test improvements for: **{{ DIMENSION_NAME }}**

(If name not provided, ask the user which entity to test)

---

## Step 0: Configuration & Test Setup

### 0.1 Read Configuration

**First**: Read `project.config.json` to get paths:

```bash
cat project.config.json
```

Extract:
- `dbt_repository` = `paths.dbt_repository`
- `dimensions_output` = `paths.dimensions_output`
- `facts_output` = `paths.facts_output`

Create test output path:
```python
test_repo = f"{dbt_repository}-ai"  # e.g., ./tfses-dbt-snowflake-3030-ai
```

### 0.2 Copy Repository for Testing

```bash
# Remove old test folder if exists
if [ -d "{test_repo}" ]; then
    rm -rf "{test_repo}"
fi

# Copy repo to test folder
cp -r {dbt_repository} {test_repo}

# Remove git to prevent accidental commits
rm -rf {test_repo}/.git

echo "Test environment ready: {test_repo}/"
```

### 0.3 Determine Entity Type

```python
entity_name = "{{ DIMENSION_NAME }}"

if entity_name.startswith("d_") or entity_name.startswith("dim_"):
    entity_type = "dimension"
    entity_path = f"{dimensions_output}/{entity_name}"
elif entity_name.startswith("f_") or entity_name.startswith("fact_"):
    entity_type = "fact"
    entity_path = f"{facts_output}/{entity_name}"
```

### 0.4 Repository Analysis

```
Task(
    subagent_type="repo-analyzer",
    prompt="Analyze DBT repository at {test_repo}/ and extract context.
    Write to: .claude/skills/dbt-best-practices/reference/repo_context/"
)
```

Display:
```
LOCAL TEST ENVIRONMENT READY
Test Folder: {test_repo}/
Git: Disabled (safe testing)
Original: {dbt_repository}/ (untouched)
```

---

## Steps 1-6: Migration Pipeline

**Execute the shared pipeline from `.claude/commands/_pipeline_steps.md`**

Parameters:
- `entity_name`: {{ DIMENSION_NAME }}
- `entity_type`: {entity_type}
- `entity_path`: {entity_path}
- `dbt_repository`: {test_repo}  (TEST folder, not production!)
- `enable_git_ops`: **false**    (no git operations!)

**Pipeline Steps:**
1. Parse Pentaho Files (pentaho-parser)
2. Analyze Transformations (pentaho-analyzer) + Gate
3. Build Dependency Graph (dependency-graph-builder) + Gate
4. Translate SQL (sql-translator)
5. Generate DBT Models (dbt-model-generator)
6. Validate Quality (quality-validator with enable_git_ops=false)

**Key Difference**: All output goes to `{test_repo}/`, not the production repo.

---

## Final Report & Comparison

```
IMPROVEMENT TEST COMPLETE: {{ DIMENSION_NAME }}

Generated in: {test_repo}/
Original in: {dbt_repository}/

COMPARISON GUIDE:

1. Visual diff (VSCode):
   code --diff {dbt_repository} {test_repo}

2. Command line:
   diff -r {dbt_repository}/models {test_repo}/models

3. Specific model:
   diff {dbt_repository}/models/gold/{{ DIMENSION_NAME }}.sql \
        {test_repo}/models/gold/{{ DIMENSION_NAME }}.sql

Key improvements to look for:
- Better documentation
- More tests
- Improved CTE structure
- Proper materialization
- UDF expansions

NEXT STEPS:
1. Review differences
2. If satisfied, run: /migrate {{ DIMENSION_NAME }}
```

---

## Key Differences from /migrate

| Aspect | /migrate | /improve |
|--------|----------|----------|
| Output folder | {dbt_repository}/ | {dbt_repository}-ai/ |
| Git operations | Yes | No |
| Purpose | Production | Testing |
| Risk | Updates repo | Safe sandbox |

---

## Key Points

- **All paths from `project.config.json`** - no hardcoded paths
- **NO git operations** - safe testing
- **Output to test folder** - original repo untouched
- **Compare before migrating** - review changes first
