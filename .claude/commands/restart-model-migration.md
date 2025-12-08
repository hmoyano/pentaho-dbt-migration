---
description: Restart a paused dimension migration and complete remaining models
---

# Restart Model Migration

You are restarting a previously paused dimension migration to complete remaining models.

## User Request

The user wants to restart migration for: **{{ DIMENSION_NAME }}**

(If dimension name not provided, ask the user which dimension to restart)

---

## Step 0: Read Configuration

**First**, read `project.config.json` to get paths:

```bash
cat project.config.json
```

Extract:
- `dbt_repository` = `paths.dbt_repository`
- `dimensions_output` = `paths.dimensions_output`

---

## Purpose

This command is used to:
- Resume a paused migration when dependencies become available
- Complete models that were previously skipped
- Validate and deploy the fully complete dimension

---

## Restart Process

### Step 1: Locate Migration State Document

Find the state document created during pause:

```bash
# Look for state document
find dimensions/{{ DIMENSION_NAME }}/ -name "*MIGRATION_STATE.md" -o -name "*_STATE.md"

# If found, read it
STATE_FILE=$(find dimensions/{{ DIMENSION_NAME }}/ -name "*MIGRATION_STATE.md" -o -name "*_STATE.md" | head -1)

if [ -f "$STATE_FILE" ]; then
  echo "Found state document: $STATE_FILE"
  cat "$STATE_FILE"
else
  echo "ERROR: No migration state document found for {{ DIMENSION_NAME }}"
  echo "Cannot restart migration without state document."
  exit 1
fi
```

**If no state document exists**:
- Inform user that dimension was not properly paused
- Suggest running `/migration-status {{ DIMENSION_NAME }}` to check current state
- Consider running `/migrate {{ DIMENSION_NAME }}` instead for fresh migration

---

### Step 2: Extract Paused Models and Dependencies

From the state document, identify:

1. **Paused models** - Files with .sql.skip extension
2. **Missing dependencies** - Models/tables that were not available
3. **Resume instructions** - Specific steps documented during pause

Parse the state document sections:
- "⏸️ Paused Models" section
- "Missing Dependencies" lists
- "Resume Instructions" section

---

### Step 3: Check Dependency Availability

For each missing dependency identified in pause state:

```bash
# Check if dependency is now a model in repository
find {dbt_repository}/models/ -name "{{ dependency_name }}.sql"

# Check if dependency is a source
grep -q "name: {{ dependency_name }}" {dbt_repository}/models/bronze/sources.yml
```

**Create availability report**:

```
Dependency Availability Check:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ dependency_1 - FOUND in models/silver/silver_mas/
✅ dependency_2 - FOUND in models/gold/
❌ dependency_3 - STILL MISSING
❌ dependency_4 - STILL MISSING

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Available: 2/4 dependencies
Still Missing: 2/4 dependencies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Step 4: Determine Which Models Can Be Resumed

For each paused model, check if ALL its dependencies are now available:

```bash
# Example: Check d_user.sql.skip dependencies
MODEL_FILE="{dbt_repository}/models/gold/d_user.sql.skip"

# Extract all ref() calls
REFS=$(grep -oh "{{ ref('[^']*') }}" "$MODEL_FILE" | sed "s/{{ ref('\([^']*\)') }}/\1/g")

# Extract all source() calls
SOURCES=$(grep -oh "{{ source('[^']*', '[^']*') }}" "$MODEL_FILE")

# Check each ref
for ref in $REFS; do
  if find {dbt_repository}/models/ -name "$ref.sql" | grep -q .; then
    echo "✅ $ref - FOUND"
  else
    echo "❌ $ref - MISSING"
    BLOCKED=true
  fi
done

# Check each source
# [Similar logic for sources]
```

**Categorize paused models**:

1. **Ready to resume** - All dependencies now available
2. **Still blocked** - Some dependencies still missing
3. **Needs investigation** - Unclear dependency status

---

### Step 5: User Decision Point

Present findings to user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESTART READINESS: {{ DIMENSION_NAME }}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Paused Models Analysis:

✅ READY TO RESUME (N models):
   - model_1.sql.skip → All dependencies available
   - model_2.sql.skip → All dependencies available

❌ STILL BLOCKED (N models):
   - model_3.sql.skip → Missing: dependency_X, dependency_Y
   - model_4.sql.skip → Missing: dependency_Z

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Options:

1. Resume N ready models (partial completion)
2. Wait until all dependencies available (full completion)
3. Cancel restart

What would you like to do?
```

**User chooses**:
- **Option 1**: Resume ready models only, keep blocked models paused
- **Option 2**: Wait, exit command
- **Option 3**: Cancel

---

### Step 6: Restore Ready Models

For models ready to resume:

```bash
cd {dbt_repository}/models/

# Restore each ready model
mv gold/d_user.sql.skip gold/d_user.sql
mv gold/model_2.sql.skip gold/model_2.sql

echo "Restored N models from .skip"
```

---

### Step 7: Verify with DBT Parse

Test that restored models parse successfully:

```bash
cd {dbt_repository}
./dbt.exe parse 2>&1 | tee /tmp/dbt_parse_restart.txt
```

**Expected**: Parse should succeed for all active models (previous complete + newly restored)

**If parse fails**:
- Review errors carefully
- May indicate dependency issues not caught in Step 4
- May need to re-skip problematic models
- Check for syntax errors introduced since pause

---

### Step 8: Update Migration State Document

Update the state document to reflect restart:

```bash
STATE_FILE="dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md"

# Update status line
sed -i 's/Status: PAUSED/Status: RESUMED/g' "$STATE_FILE"

# Add restart log section
cat >> "$STATE_FILE" <<EOF

---

## 🔄 Restart Log

**Restart Date**: $(date +%Y-%m-%d)
**Models Resumed**: N models
**Models Still Paused**: N models

### Resumed Models:
- model_1.sql (was .skip)
- model_2.sql (was .skip)

### Still Paused:
- model_3.sql.skip (missing: dependency_X, dependency_Y)
- model_4.sql.skip (missing: dependency_Z)

**Next Action**: [Complete migration / Wait for remaining dependencies]

EOF
```

---

### Step 9: Run DBT Commands

If all models are now available, run full DBT workflow:

```bash
cd {dbt_repository}

# 1. Parse (already done in Step 7)
echo "✅ Parse successful"

# 2. Compile
echo "Running dbt compile..."
./dbt.exe compile --select tag:{{ dimension_name }}

# 3. Run (if user approves)
echo "Ready to run models. Proceed? (This will execute in Snowflake)"
# Wait for user confirmation

./dbt.exe run --select tag:{{ dimension_name }}

# 4. Test
echo "Running tests..."
./dbt.exe test --select tag:{{ dimension_name }}
```

**Ask user before running** - This executes SQL in Snowflake

---

### Step 10: Generate Completion Report

If all models are now complete:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ MIGRATION COMPLETE: {{ DIMENSION_NAME }}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: Y/Y models complete (100%)

✅ All Models Operational:
   - Silver ADQ: N models
   - Silver MAS: N models
   - Gold: N models

🔄 Resumed from Pause:
   - model_1.sql (previously blocked)
   - model_2.sql (previously blocked)

📊 Test Results:
   - Tests passed: X
   - Tests failed: Y
   - Test coverage: Z%

State Updated: dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Commit completion:
   git add .
   git commit -m "complete: {{ dimension_name }} migration (100%)"
   git push origin migrate/{{ dimension_name }}

2. Create merge request to develop

3. Deploy to production (after MR approval):
   dbt run --select tag:{{ dimension_name }}
   dbt test --select tag:{{ dimension_name }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

If some models still blocked:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏸️  MIGRATION PARTIALLY RESUMED: {{ DIMENSION_NAME }}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: X/Y models complete (Z%)

✅ Resumed Models (N):
   - model_1.sql (previously blocked, now complete)
   - model_2.sql (previously blocked, now complete)

⏸️  Still Blocked (N):
   - model_3.sql.skip (missing: dependency_X from dim_A)
   - model_4.sql.skip (missing: dependency_Y from dim_B)

State Updated: dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Commit partial completion:
   git add .
   git commit -m "resume: {{ dimension_name }} (X/Y models)"
   git push origin migrate/{{ dimension_name }}

2. Migrate remaining dependencies:
   /migrate dim_A  # Provides: dependency_X
   /migrate dim_B  # Provides: dependency_Y

3. Restart again when ready:
   /restart-model-migration {{ dimension_name }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Step 11: Commit Changes (Optional)

Ask user if they want to commit the restart progress:

```bash
cd {dbt_repository}

# Check status
git status

# Stage changes
git add models/
git add -f dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md

# Commit
git commit -m "$(cat <<'EOF'
resume: {{ dimension_name }} migration (X/Y models complete)

Resumed models (N):
- [List models restored from .skip]

[If complete]:
✅ Migration 100% complete - all models operational

[If partial]:
Still blocked (N):
- [List models still .skip with reasons]

State updated: dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push
git push origin migrate/{{ dimension_name }}
```

---

## Important Checks

Before declaring completion:

✅ All models restored from .skip (or documented why still blocked)
✅ dbt parse succeeds
✅ dbt compile succeeds (if running full workflow)
✅ State document updated with restart log
✅ User informed of next steps

---

## Edge Cases

### Case 1: State Document Not Found

```
ERROR: Cannot restart migration - no state document found.

The migration may not have been properly paused.

Suggestions:
1. Check if migration was completed: /migration-status {{ dimension_name }}
2. Look for manual .skip files: find models/ -name "*.skip"
3. Consider fresh migration: /migrate {{ dimension_name }}
```

### Case 2: No Dependencies Available Yet

```
Cannot resume migration - dependencies still missing.

Missing dependencies:
- dependency_1 (from dim_X - not migrated yet)
- dependency_2 (from dim_Y - not migrated yet)

Recommendations:
1. Migrate dim_X: /migrate dim_X
2. Migrate dim_Y: /migrate dim_Y
3. Return to restart: /restart-model-migration {{ dimension_name }}

No changes made.
```

### Case 3: Parse Fails After Resume

```
ERROR: dbt parse failed after resuming models.

Models restored:
- model_1.sql (from .skip)
- model_2.sql (from .skip)

Parse errors:
[Show errors]

Actions taken:
- Re-skipped problematic models
- Restored to last working state

Analysis:
[Explain likely causes]

Recommendations:
[Steps to resolve]
```

### Case 4: Git Conflicts

```
WARNING: Uncommitted changes detected.

Current branch: {{ current_branch }}
Status: [Show git status]

Recommendations:
1. Commit or stash changes before restart
2. Ensure you're on correct branch
3. Pull latest changes if needed

Proceed anyway? (Not recommended)
```

---

## Validation Flow

```
┌─────────────────────────────────────────┐
│  1. Locate State Document               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Extract Paused Models & Dependencies│
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Check Dependency Availability       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. Determine Ready vs Blocked Models   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. User Decision                       │
│     (Resume ready / Wait / Cancel)      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  6. Restore Ready Models (.skip → .sql)│
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  7. Verify DBT Parse                    │
└──────────────┬──────────────────────────┘
               │
          ┌────┴─────┐
          │          │
      SUCCESS      FAILURE
          │          │
          ▼          ▼
    ┌─────────┐  ┌──────────┐
    │Complete │  │Rollback  │
    │Migration│  │& Report  │
    └─────────┘  └──────────┘
```

---

## Success Criteria

Migration can be marked complete when:

✅ All paused models restored to .sql
✅ dbt parse succeeds
✅ dbt compile succeeds
✅ dbt run succeeds (in test environment)
✅ dbt test passes (acceptable failure rate)
✅ State document updated
✅ Changes committed to git
✅ User informed and satisfied

---

## Notes

- **Incremental restart**: Can resume partial models, don't need all dependencies
- **Idempotent**: Can run restart multiple times as dependencies become available
- **State preserved**: Original pause state maintained with restart log appended
- **Rollback safe**: Failed restarts re-skip models, return to working state

---

Be thorough, cautious, and clear. Restart is the payoff after migration work - make it smooth and successful.
