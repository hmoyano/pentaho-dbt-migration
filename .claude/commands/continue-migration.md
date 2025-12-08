---
description: Modify an existing migrated entity with full context from reference docs
---

# Continue Migration

You are helping the user modify an already-migrated entity (dimension or fact) with full context.

## User Request

The user wants to modify: **{{ ENTITY_NAME }}**

(If entity name not provided, ask the user which entity to modify)

---

## Step 1: Read Configuration

First, read `project.config.json` to get paths:

```bash
cat project.config.json
```

This gives you:
- `paths.dimensions_output` - Where dimensions are (e.g., `./dimensions`)
- `paths.facts_output` - Where facts are (e.g., `./facts`)
- `paths.dbt_repository` - DBT repo path

---

## Step 2: Locate Entity and Load Context

Determine if entity is a dimension or fact:

```bash
# Check if it's a dimension
if [ -d "dimensions/{{ ENTITY_NAME }}" ]; then
    entity_type="dimension"
    entity_path="dimensions/{{ ENTITY_NAME }}"
# Check if it's a fact
elif [ -d "facts/{{ ENTITY_NAME }}" ]; then
    entity_type="fact"
    entity_path="facts/{{ ENTITY_NAME }}"
else
    echo "Entity not found. Available entities:"
    echo "Dimensions:" && ls dimensions/ 2>/dev/null
    echo "Facts:" && ls facts/ 2>/dev/null
    exit 1
fi
```

Read the reference documentation:

```bash
# Read REFERENCE.md (primary context)
cat ${entity_path}/REFERENCE.md

# Read CHANGELOG.md (modification history)
cat ${entity_path}/CHANGELOG.md
```

---

## Step 3: Display Summary

Show the user a concise summary of the migrated entity:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENTITY: {{ ENTITY_NAME }} ({entity_type})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Migration Date: {from REFERENCE.md}
Status: {validated/needs_review}

Source Tables:
- {list from REFERENCE.md}

DBT Models:
- Silver ADQ: {list}
- Silver MAS: {list}
- Gold: {list}

Recent Changes:
- {latest entries from CHANGELOG.md}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Step 4: Ask What User Wants to Modify

Present options to the user:

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

---

## Step 5: Execute Changes with Context

Based on user choice, proceed with full context:

### If Adding Columns:

1. Read source table definitions from metadata:
   ```bash
   cat ${entity_path}/metadata/pentaho_analyzed.json | jq '.files[].source_tables'
   ```

2. Ask which columns to add

3. Update the appropriate model(s) in DBT repo:
   - Silver ADQ: Add to SELECT and source mapping
   - Silver MAS: Add to transformations if needed
   - Gold: Add to final output

4. Update `_models.yml` with column documentation

### If Fixing a Bug:

1. Ask user to describe the bug

2. Read relevant model(s):
   ```bash
   cat {dbt_repo}/models/{layer}/{model}.sql
   ```

3. Identify and fix the issue

4. Run validation:
   ```bash
   cd {dbt_repo}
   dbt compile --select {model}
   dbt run --select {model}
   ```

### If Updating Translation Logic:

1. Ask what translation needs updating

2. Read current SQL:
   ```bash
   cat ${entity_path}/sql/*_translated.sql
   ```

3. Modify the DBT model with new logic

4. Validate changes

### If Adding/Modifying Tests:

1. Show current tests from `_models.yml`

2. Ask what tests to add (unique, not_null, relationships, etc.)

3. Update `_models.yml` with new tests

4. Run tests:
   ```bash
   cd {dbt_repo}
   dbt test --select {model}
   ```

### If Updating Documentation:

1. Show current column descriptions

2. Ask for updates

3. Modify `_models.yml` with improved descriptions

### If Changing Materialization:

1. Show current materialization strategy

2. Ask for new strategy (view, table, incremental)

3. Update model config block

4. Validate:
   ```bash
   dbt run --select {model} --full-refresh
   ```

---

## Step 6: Update CHANGELOG.md

After making changes, append to CHANGELOG.md:

```markdown
## [{current_date}] Modification

**Type:** {type of change}

**Changes:**
- {description of changes}

**Models Modified:**
- {list of models}

**Validated:** {yes/no}

---
```

---

## Step 7: Summary

Provide summary of changes made:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHANGES COMPLETE: {{ ENTITY_NAME }}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Changes Made:
- {list of changes}

Files Modified:
- {list of files}

Validation:
- dbt compile: {pass/fail}
- dbt run: {pass/fail}
- dbt test: {pass/fail}

CHANGELOG updated: {entity_path}/CHANGELOG.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next Steps:
1. Review changes in DBT models
2. Commit and push: git add . && git commit -m "..."
3. Create PR for review
```

---

## Important Notes

- **Always read REFERENCE.md first** - It contains all context about the migration
- **Update CHANGELOG.md** - Every modification should be logged
- **Validate after changes** - Run dbt compile/run/test
- **Don't break existing functionality** - Test thoroughly before committing
- **Use config paths** - Read from project.config.json, don't hardcode
