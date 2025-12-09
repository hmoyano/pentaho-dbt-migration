---
description: Pause a dimension migration and save progress state
---

# Pause Model Migration

You are pausing a dimension migration that has incomplete models due to missing dependencies or other blockers.

## User Request

The user wants to pause migration for: **{{ DIMENSION_NAME }}**

(If dimension name not provided, ask the user which dimension to pause)

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

## Step 0.5: Git Sync

**Use `git-workflow` skill - operation: `sync-current`**

Read and execute the script from `.claude/skills/git-workflow/SKILL.md` (section 2).

Parameters:
- `{dbt_repository}` - from config

This will:
1. Fetch latest from remote
2. Pull current branch if exists on remote
3. Warn about uncommitted changes

---

## Purpose

This command is used when:
- Some models depend on outputs from OTHER dimensions (cross-dimension dependencies)
- Models are incomplete due to missing source tables
- You need to migrate other dimensions first before completing this one
- You want to save progress and come back later

---

## Pause Process

### Step 1: Verify Current State

Check that the dimension has been migrated (at least partially):

```bash
# Check if metadata exists
ls -la dimensions/{{ DIMENSION_NAME }}/metadata/

# Check if models exist
find {dbt_repository}/models/ -name "*.sql" | grep -i "{{ DIMENSION_NAME }}" | head -20
```

If no metadata or models exist, inform user that there's nothing to pause.

---

### Step 2: Run DBT Parse to Identify Issues

Run `dbt parse` to identify which models have dependency issues:

```bash
cd {dbt_repository}
./dbt.exe parse 2>&1 | tee /tmp/dbt_parse_output.txt
```

**Analyze output for**:
- Missing source errors: `depends on a source named 'X' which was not found`
- Missing model errors: `depends on a node named 'X' which was not found`
- Syntax errors (should be fixed before pausing)

---

### Step 3: Extract Models with Tag

Get list of all models associated with this dimension:

```bash
# Find all models with dimension tag
grep -rl "tags=.*'{{ DIMENSION_NAME }}'" {dbt_repository}/models/ --include="*.sql" | sort
```

---

### Step 4: Categorize Models

For each model identified:

1. **Complete models**: Parse successfully, no dependency issues
2. **Incomplete models**: Have missing dependencies (from parse output)

Create two lists:
- `COMPLETE_MODELS` - Working models
- `INCOMPLETE_MODELS` - Models with missing dependencies

---

### Step 5: Identify Missing Dependencies

For each incomplete model, extract the missing dependencies from parse errors:

```bash
# Example: Parse d_user.sql to find what it references
grep -oh "{{ ref('[^']*') }}" models/gold/d_user.sql
grep -oh "{{ source('[^']*', '[^']*') }}" models/gold/d_user.sql
```

Cross-reference with:
1. **Existing models** in repository
2. **Expected outputs** from translation_metadata.json
3. **Known external dependencies** from other dimensions

---

### Step 6: Rename Incomplete Models to .skip

For each incomplete model:

```bash
cd {dbt_repository}/models/

# Rename to .skip
mv gold/d_user.sql gold/d_user.sql.skip
mv gold/tmp_f_early_terminations.sql gold/tmp_f_early_terminations.sql.skip
```

---

### Step 7: Verify Parse Succeeds

After skipping incomplete models:

```bash
cd {dbt_repository}
./dbt.exe parse
```

**Expected**: Parse should succeed for all complete models.

If parse still fails:
- Investigate remaining errors
- May need to skip additional models
- Check for syntax errors (fix before pausing)

---

### Step 8: Generate Migration State Document

Create comprehensive state document: `dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md`

**Required sections**:

```markdown
# {{ dimension_name }} Migration State

**Migration ID**: {{ dimension_name }}_{{ YYYYMMDD }}
**Status**: PAUSED - Awaiting Dependencies
**Date**: {{ current_date }}
**Branch**: {{ git_branch }}
**System Version**: {{ migration_system_version }}

---

## Migration Progress: X% Complete

### ✅ Completed (X/Y models)

**Silver ADQ (N models)**:
- stg_model_1.sql
- stg_model_2.sql
[List all complete silver_adq models]

**Silver MAS (N models)**:
- mas_model_1.sql
- mas_model_2.sql
[List all complete silver_mas models]

**Gold (N models)**:
- d_dimension_1.sql
- f_fact_1.sql
[List all complete gold models]

---

## ⏸️ Paused Models (N/Y)

### 1. model_name.sql → model_name.sql.skip
**Status**: INCOMPLETE - Missing N dependencies
**Location**: `{dbt_repository}/models/{{ layer }}/model_name.sql.skip`

**Missing Dependencies**:
- ❌ **dependency_1** (from another dimension OR needs generation)
- ❌ **dependency_2** (from another dimension OR needs generation)

**Has Dependencies** (N/Total):
- ✅ existing_dep_1
- ✅ existing_dep_2

**Resume Action**:
```bash
# After dependencies are available:
cd {dbt_repository}/models/{{ layer }}
mv model_name.sql.skip model_name.sql
dbt run --select model_name
```

[Repeat for each paused model]

---

## ⚠️ Known Issues

### Issue 1: [Description]
**Model**: model_name.sql
**Issue**: [Detailed description]
**Impact**: [HIGH/MEDIUM/LOW]
**Resolution**: [Steps to resolve]

[List all known issues]

---

## 📊 Metadata Files

**Translation Metadata**: `dimensions/{{ dimension_name }}/metadata/translation_metadata.json` (vX.X)
**Generation Report**: `dimensions/{{ dimension_name }}/metadata/dbt_generation_report.json`
**Translated SQL**: `dimensions/{{ dimension_name }}/sql/*.sql` (N files)
**Backup**: `dimensions/{{ dimension_name }}/backup_vX.X/*.json` (if exists)

---

## 🔄 Source Definitions Added (N sources)

**Bronze Sources File**: `{dbt_repository}/models/bronze/sources.yml`

**Added Systems**:
- **SYSTEM1**: N new sources (TABLE1, TABLE2, ...)
- **SYSTEM2**: N new sources (TABLE1, TABLE2, ...)

[List all source systems and tables added]

---

## 🎯 Resume Instructions

### To Complete {{ dimension_name }} Migration:

1. **Generate Missing Internal Models** (if applicable):
   ```bash
   # If any models need generation within this dimension
   ```

2. **Wait for Cross-Dimension Dependencies**:
   - Migrate dimension providing: [list dependencies]
   - Migrate dimension providing: [list dependencies]

3. **Resume Paused Models**:
   ```bash
   cd {dbt_repository}/models/{{ layer }}
   mv model_name.sql.skip model_name.sql
   # [Repeat for all paused models]
   ```

4. **Test**:
   ```bash
   cd {dbt_repository}
   dbt parse
   dbt compile --select {{ dimension_name }}
   dbt run --select {{ dimension_name }}
   dbt test --select {{ dimension_name }}
   ```

5. **Commit** (if not already committed):
   ```bash
   git add .
   git commit -m "Complete {{ dimension_name }} migration"
   git push origin migrate/{{ dimension_name }}
   ```

---

## 📈 Test Results

### DBT Parse: [✅ PASSED / ❌ FAILED]
**Date**: {{ test_date }}
**Models Tested**: N complete models
**Result**: [Description]
**Warnings**: [Count and description]

**Command Used**:
```bash
cd {dbt_repository}
./dbt.exe parse
```

---

## 🔍 Dependencies Map

```
Bronze (sources)
  ↓
Silver ADQ (N staging models)
  ↓
Silver MAS (N master models)
  ↓
Gold (N dimensions/facts)
  ↓
Gold (N PAUSED - awaiting dependencies)
```

**Complete Chain Example**:
```
[Show example dependency chain]
```

---

## 💾 Git State

**Branch**: {{ git_branch }}
**Status**: [Clean / Uncommitted changes]
**Stash**: [Description if stash exists]
**Modified Files**:
[List key modified files]

---

## 📝 Notes

- System {{ version }} successfully implemented [key features]
- All N Pentaho files (.ktr/.kjb) parsed and translated
- X% of {{ dimension_name }} models complete and working
- Remaining Y% blocked by [reasons] (EXPECTED/UNEXPECTED)

---

**Generated by**: Pentaho → DBT Migration System {{ version }}
**Last Updated**: {{ timestamp }}
```

---

### Step 9: Generate Summary

Create a concise summary for the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏸️  MIGRATION PAUSED: {{ DIMENSION_NAME }}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: X/Y models complete (Z%)

✅ Complete Models (X):
   - Silver ADQ: N models
   - Silver MAS: N models
   - Gold: N models

⏸️  Paused Models (Y):
   - model_1.sql.skip (missing N dependencies)
   - model_2.sql.skip (missing N dependencies)

Missing Dependencies (Total: N):
   From other dimensions:
   - dependency_1 (from dim_X)
   - dependency_2 (from dim_Y)

   To be generated:
   - dependency_3 (needs investigation)

State Document: dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Commit current progress (if not committed):
   git add .
   git commit -m "pause: {{ dimension_name }} migration (X/Y models)"
   git push origin migrate/{{ dimension_name }}

2. Migrate other dimensions to provide dependencies:
   /migrate dim_X  # Provides: dependency_1
   /migrate dim_Y  # Provides: dependency_2

3. Resume this migration:
   /restart-model-migration {{ dimension_name }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Step 10: Commit Changes (Optional)

Ask user if they want to commit the paused state:

```bash
cd {dbt_repository}

# Check status
git status

# Stage changes
git add models/
git add -f dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md

# Commit
git commit -m "$(cat <<'EOF'
pause: {{ dimension_name }} migration (X/Y models complete)

Complete models (X):
- [List by layer]

Paused models (Y):
- [List with reasons]

Missing dependencies:
- [List]

State saved to: dimensions/{{ DIMENSION_NAME }}/{{ DIMENSION_NAME_UPPER }}_MIGRATION_STATE.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push
git push origin migrate/{{ dimension_name }}
```

---

## Important Notes

- **Pause is normal**: Cross-dimension dependencies are expected in complex migrations
- **State document is critical**: Contains all info needed to resume
- **.skip files are intentional**: Prevents dbt parse errors for incomplete models
- **Complete models are safe**: Can be deployed and used immediately
- **Resume anytime**: Use `/restart-model-migration {{ dimension_name }}` when ready

---

## Validation

Before finishing pause:

✅ dbt parse succeeds with complete models
✅ Incomplete models renamed to .skip
✅ State document created and comprehensive
✅ Missing dependencies clearly identified
✅ Resume instructions are clear
✅ Git branch is clean (or changes committed)

---

## Error Handling

### If parse still fails after skipping:
- Review parse errors for syntax issues
- Check if additional models need skipping
- Verify source definitions are correct

### If unable to identify dependencies:
- Review model SQL manually
- Check translation_metadata.json for clues
- Use dependency_graph.json to understand relationships

### If too many models are incomplete:
- Consider if dimension should be migrated later
- Check if missing dependencies are within this dimension (can be generated)
- Review pentaho files for missing transformations

---

Be thorough, clear, and helpful. The pause state should give complete visibility and confidence for resumption.
