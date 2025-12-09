---
description: Continue or resume work on an entity - auto-detects if paused (incomplete) or completed (modify)
---

# Continue Migration

Smart command that auto-detects what mode to use based on entity state.

## User Request

The user wants to continue work on: **{{ ENTITY_NAME }}**

(If entity name not provided, ask the user which entity to continue)

---

## Step 0: Read Configuration

First, read `project.config.json` to get paths:

```bash
cat project.config.json
```

Extract:
- `dbt_repository` = `paths.dbt_repository`
- `dimensions_output` = `paths.dimensions_output`
- `facts_output` = `paths.facts_output`

---

## Step 0.5: Git Sync

**Use `git-workflow` skill - operation: `sync-current`**

Read and execute the script from `.claude/skills/git-workflow/SKILL.md` (section 2).

This will:
1. Fetch latest from remote
2. Pull current branch if exists on remote
3. Warn about uncommitted changes

---

## Step 1: Locate Entity and Detect Mode

```bash
# Find entity path
if [ -d "dimensions/{{ ENTITY_NAME }}" ]; then
    entity_type="dimension"
    entity_path="dimensions/{{ ENTITY_NAME }}"
elif [ -d "facts/{{ ENTITY_NAME }}" ]; then
    entity_type="fact"
    entity_path="facts/{{ ENTITY_NAME }}"
else
    echo "Entity not found. Available:"
    ls dimensions/ facts/ 2>/dev/null
    exit 1
fi

# Detect mode based on files present
if [ -f "${entity_path}/*MIGRATION_STATE.md" ] || [ -f "${entity_path}/*_STATE.md" ]; then
    MODE="RESTART"  # Paused migration - complete remaining models
elif [ -f "${entity_path}/REFERENCE.md" ]; then
    MODE="MODIFY"   # Completed migration - modify existing
else
    echo "ERROR: No state files found. Use /migrate first."
    exit 1
fi
```

---

## Mode A: RESTART (Complete Paused Migration)

**Triggered when:** `MIGRATION_STATE.md` exists (created by `/pause-model-migration`)

### A1. Load State Document

```bash
STATE_FILE=$(find ${entity_path}/ -name "*MIGRATION_STATE.md" -o -name "*_STATE.md" | head -1)
cat "$STATE_FILE"
```

Extract from state document:
- Paused models (files with `.sql.skip` extension)
- Missing dependencies at time of pause
- Resume instructions

### A2. Check if Dependencies Now Available

For each missing dependency from state document:

```bash
# Check if dependency model now exists
find {dbt_repository}/models/ -name "{dependency_name}.sql"

# Or check if source now exists in _sources.yml
grep -q "name: {dependency_name}" {dbt_repository}/models/bronze/_sources.yml
```

### A3. Resume Skipped Models

For each `.sql.skip` file:

```bash
# Check if dependencies are satisfied
# If yes: rename back to .sql
mv {dbt_repository}/models/{layer}/{model}.sql.skip {dbt_repository}/models/{layer}/{model}.sql

# Run validation
cd {dbt_repository}
./dbt.exe compile --select {model}
./dbt.exe run --select {model}
```

### A4. Update State and Validate

After processing all skipped models:

```bash
cd {dbt_repository}
./dbt.exe run --select tag:{{ ENTITY_NAME }}
./dbt.exe test --select tag:{{ ENTITY_NAME }}
```

If all models pass:
- Delete or archive MIGRATION_STATE.md
- Generate REFERENCE.md (run migration-docs-generator)

---

## Mode B: MODIFY (Change Completed Migration)

**Triggered when:** `REFERENCE.md` exists (migration completed)

### B1. Load Context

```bash
cat ${entity_path}/REFERENCE.md
cat ${entity_path}/CHANGELOG.md 2>/dev/null || echo "No changelog yet"
```

### B2. Display Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENTITY: {{ ENTITY_NAME }} ({entity_type})
Mode: MODIFY (completed migration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Migration Date: {from REFERENCE.md}
Source Tables: {list from REFERENCE.md}

DBT Models:
- Silver ADQ: {list}
- Silver MAS: {list}
- Gold: {list}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### B3. Ask What to Modify

Present options:

```
What would you like to do?

1. Add new columns - Add columns from source tables
2. Fix a bug - Fix issues in existing models
3. Update translation logic - Modify SQL transformations
4. Add/modify tests - Update DBT tests
5. Update documentation - Improve model docs
6. Change materialization - Switch view/table/incremental
7. Other - Describe what you need
```

Wait for user response.

### B4. Execute Changes

Based on user choice, make modifications using context from REFERENCE.md.

**Always validate after changes:**
```bash
cd {dbt_repository}
./dbt.exe compile --select {model}
./dbt.exe run --select {model}
./dbt.exe test --select {model}
```

### B5. Update CHANGELOG.md

Append to CHANGELOG.md:

```markdown
## [{current_date}] Modification

**Type:** {type of change}
**Changes:** {description}
**Models Modified:** {list}
**Validated:** yes/no
```

---

## Step Final: Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTINUE COMPLETE: {{ ENTITY_NAME }}
Mode: {RESTART or MODIFY}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actions Taken:
- {list of actions}

Validation:
- dbt compile: {pass/fail}
- dbt run: {pass/fail}
- dbt test: {pass/fail}

Next Steps:
1. Review changes
2. Commit: git add . && git commit -m "..."
3. Push and create PR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Quick Reference

| State File Found | Mode | Action |
|------------------|------|--------|
| `MIGRATION_STATE.md` | RESTART | Complete skipped models |
| `REFERENCE.md` | MODIFY | Edit completed migration |
| Neither | ERROR | Use `/migrate` first |
