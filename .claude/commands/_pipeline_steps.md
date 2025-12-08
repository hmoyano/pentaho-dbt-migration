# Shared Pipeline Steps (Steps 1-6)

This module contains the core migration pipeline logic shared by `/migrate` and `/improve` commands.

**Important**: This file is referenced by commands, not executed directly.

---

## Configuration Loading

Before executing any step, read `project.config.json`:

```bash
cat project.config.json
```

Extract paths:
- `paths.pentaho_sources` - Source Pentaho files
- `paths.dimensions_output` - Dimension output folder
- `paths.facts_output` - Fact output folder
- `paths.dbt_repository` - DBT repo path

Determine entity type and output path:
```python
if entity_name.startswith("d_") or entity_name.startswith("dim_"):
    entity_type = "dimension"
    output_folder = config.paths.dimensions_output
elif entity_name.startswith("f_") or entity_name.startswith("fact_"):
    entity_type = "fact"
    output_folder = config.paths.facts_output
else:
    # Ask user
    entity_type = ask_user("Is this a dimension or fact?")
    output_folder = dimensions_output if entity_type == "dimension" else facts_output

entity_path = f"{output_folder}/{entity_name}"
```

---

## Step 1: Parse Pentaho Files

**Skill**: pentaho-parser

**Command**:
```
/pentaho-parser {{ ENTITY_NAME }}
```

**Expected Output**: `{entity_path}/metadata/pentaho_raw.json`

**Validation**:
- File created successfully
- No parsing errors
- Files listed in output

**If fails**: Stop and report error.

---

## Step 2: Analyze Transformations

**Agent**: pentaho-analyzer

**Task**: Use Task tool to invoke pentaho-analyzer:

```
Task(
    subagent_type="pentaho-analyzer",
    prompt="""
    Analyze Pentaho transformations for {{ ENTITY_NAME }}.

    Read:
    - {entity_path}/metadata/pentaho_raw.json
    - config/schema_registry.json
    - config/TABLE_COUNT.csv (if exists)

    Perform:
    1. Variable resolution
    2. Table classification
    3. Complexity assessment
    4. Business logic analysis
    5. Dependency identification

    Output: {entity_path}/metadata/pentaho_analyzed.json
    """
)
```

**Expected Output**: `{entity_path}/metadata/pentaho_analyzed.json`

### Gate Check (CRITICAL)

After analysis, check for blocking issues:

```python
# Read analysis output
analysis = read_json(f"{entity_path}/metadata/pentaho_analyzed.json")

blocking_issues = [i for i in analysis.issues if i.blocking]
auto_resolved = [i for i in analysis.issues if i.auto_resolved]
warnings = [i for i in analysis.issues if i.severity == "WARNING"]

# Display auto-fix results
if auto_resolved:
    print(f"✅ {len(auto_resolved)} issues auto-resolved")
    for issue in auto_resolved:
        print(f"  - {issue.description}: {issue.resolution}")

# Check blocking issues
if blocking_issues:
    # STOP PIPELINE
    print("❌ PIPELINE BLOCKED")
    for issue in blocking_issues:
        print(f"  🔴 {issue.description}")
        print(f"     Action: {issue.action_needed}")
    print("\nFix issues and re-run migration.")
    exit(1)

# Non-blocking warnings
if warnings:
    print(f"⚠️ {len(warnings)} warnings (non-blocking)")
    for w in warnings:
        print(f"  - {w.description}")
```

### Step 2 Review (Safe Mode)

Display summary and confirm:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ STEP 2 COMPLETE: Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESOLVED VARIABLES:
✅ ${VAR} → VALUE (from schema_registry.json)

FILES ANALYZED: X
COMPLEXITY: X low, Y medium, Z high
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Use AskUserQuestion to confirm:
- ✅ Yes, continue to Step 3
- ❌ No, let me fix something
- 📝 Show detailed analysis

---

## Step 3: Build Dependency Graph

**Agent**: dependency-graph-builder

**Task**: Use Task tool:

```
Task(
    subagent_type="dependency-graph-builder",
    prompt="""
    Build dependency graph for {{ ENTITY_NAME }}.

    Read:
    - {entity_path}/metadata/pentaho_raw.json
    - {entity_path}/metadata/pentaho_analyzed.json

    Perform:
    1. File-level dependencies
    2. Table-level dependencies
    3. Execution order
    4. Circular dependency detection
    5. Parallel execution identification

    Output:
    - {entity_path}/metadata/dependency_graph.json
    - {entity_path}/metadata/dependency_graph.mmd
    """
)
```

**Expected Output**:
- `{entity_path}/metadata/dependency_graph.json`
- `{entity_path}/metadata/dependency_graph.mmd`

### Gate Check (Circular Dependencies)

```python
graph = read_json(f"{entity_path}/metadata/dependency_graph.json")

circular = graph.get("circular_dependencies", [])
unresolved = [c for c in circular if c.status in ["UNRESOLVABLE", "UNKNOWN"]]

if unresolved:
    # STOP PIPELINE
    print("❌ UNRESOLVABLE CIRCULAR DEPENDENCIES")
    for dep in unresolved:
        print(f"  🔄 {dep.description}")
        print(f"     Reason: {dep.reason}")
    exit(1)
```

### Step 3 Review (Safe Mode)

Display and confirm:
- ✅ Yes, continue to Step 4
- 📊 View dependency graph
- ❌ Stop pipeline

---

## Step 4: Translate SQL to Snowflake

**Agent**: sql-translator

**Task**: Use Task tool:

```
Task(
    subagent_type="sql-translator",
    prompt="""
    Translate SQL for {{ ENTITY_NAME }} from Oracle to Snowflake.

    Read:
    - {entity_path}/metadata/pentaho_analyzed.json
    - {entity_path}/metadata/dependency_graph.json
    - config/schema_registry.json
    - .claude/skills/oracle-snowflake-rules/

    Perform:
    1. Oracle → Snowflake function conversion
    2. Syntax translation
    3. Custom function handling (check schema_registry.json)
    4. Variable mapping to DBT
    5. Confidence scoring

    Output:
    - {entity_path}/sql/*_translated.sql
    - {entity_path}/metadata/translation_metadata.json
    """
)
```

**Expected Output**:
- Translated SQL files in `{entity_path}/sql/`
- `{entity_path}/metadata/translation_metadata.json`

### Step 4 Review (Safe Mode)

Display translation summary:
- Files translated
- Confidence breakdown
- Custom functions preserved

Confirm:
- ✅ Yes, continue to Step 5
- 📄 Review translated SQL
- ❌ Stop for manual review

---

## Step 5: Generate DBT Models

**Agent**: dbt-model-generator

**Task**: Use Task tool:

```
Task(
    subagent_type="dbt-model-generator",
    prompt="""
    Generate DBT models for {{ ENTITY_NAME }}.

    IMPORTANT:
    - output_path = "{dbt_repository}" (from project.config.json)
    - entity_type = "{entity_type}" (dimension or fact)

    Read:
    - {entity_path}/metadata/translation_metadata.json
    - {entity_path}/metadata/dependency_graph.json
    - {entity_path}/metadata/pentaho_analyzed.json
    - config/schema_registry.json
    - .claude/skills/dbt-best-practices/
    - .claude/skills/dbt-best-practices/reference/repo_context/

    Perform:
    1. Model file creation with CTE structure
    2. source() and ref() conversion
    3. Config blocks with materialization
    4. Documentation (_models.yml)
    5. Data quality tests
    6. _sources.yml updates (APPEND mode)

    Output (relative to dbt_repository):
    - models/bronze/_sources.yml
    - models/silver/silver_adq/*
    - models/silver/silver_mas/*
    - models/gold/*
    - {entity_path}/metadata/dbt_generation_report.json
    """
)
```

**Expected Output**:
- DBT model files
- _models.yml and _sources.yml files
- `{entity_path}/metadata/dbt_generation_report.json`

### Step 5 Review (Safe Mode)

Display generation summary:
- Models created per layer
- Files generated
- Materialization strategy

Confirm:
- ✅ Yes, validate models
- 📂 Review generated models
- ❌ Skip validation

---

## Step 6: Validate Quality

**Agent**: quality-validator

**Task**: Use Task tool:

```
Task(
    subagent_type="quality-validator",
    prompt="""
    Validate DBT models for {{ ENTITY_NAME }} by running dbt commands LOCALLY.

    Parameters:
    - dimension: {{ ENTITY_NAME }}
    - output_path: "{dbt_repository}" (from project.config.json)
    - enable_git_ops: {true for /migrate, false for /improve}
    - git_platform: {detected platform}
    - cli_tool: {gh or glab}

    Read:
    - {entity_path}/metadata/dbt_generation_report.json

    Perform:
    1. dbt parse (syntax validation)
    2. dbt compile (template validation)
    3. dbt run --select tag:{{ ENTITY_NAME }}
    4. dbt test --select tag:{{ ENTITY_NAME }}
    5. Auto-fix errors (max 2 attempts)
    6. Git commit + push (if enable_git_ops=true)

    Output: {entity_path}/metadata/validation_report.json
    """
)
```

**Expected Output**: `{entity_path}/metadata/validation_report.json`

---

## Migration State Management

After each step, update migration state:

```python
migration_state = {
    "entity_name": entity_name,
    "entity_type": entity_type,
    "last_run": timestamp,
    "last_successful_step": step_number,
    "status": "IN_PROGRESS" if step < 6 else "COMPLETED",
    "steps_completed": [...]
}

write_json(f"{entity_path}/metadata/migration_state.json", migration_state)
```

---

## Error Handling

If any step fails:
1. **Stop pipeline** - Don't proceed
2. **Report error** - Which step, what error
3. **Provide remediation** - How to fix
4. **Save state** - Previous steps don't need re-running

---

## Progress Tracking

Use TodoWrite to track:
1. Parse Pentaho files
2. Analyze transformations
3. Build dependency graph
4. Translate SQL
5. Generate DBT models
6. Validate with dbt

Mark each as `in_progress` when starting, `completed` when done.
