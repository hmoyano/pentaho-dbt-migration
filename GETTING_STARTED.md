# Getting Started - Pentaho to DBT Migration

Complete guide to set up and run the automated Pentaho to DBT migration system.

---

## 🚨 MEGA-IMPORTANT RULE

**NEVER commit directly to `develop`, `master`, or `main` branches!**

The system has built-in protection to prevent this, but you should always:
- ✅ Work on feature branches (`migrate/dimension_name`)
- ✅ Create Pull/Merge Requests for code review
- ❌ NEVER commit directly to protected branches

**The `/migrate` command automatically creates feature branches for you.**

---

## Quick Start (5 Minutes)

### 1. Prerequisites

✅ **Already installed:**
- Git Bash (MINGW64)
- DBT Cloud CLI (`dbt.exe` in `tfses-dbt-snowflake-3030/`)
- Snowflake connection configured

✅ **Need to install:**
```bash
# GitLab CLI (if using GitLab)
winget install gitlab.glab
glab auth login

# GitHub CLI (if using GitHub)
winget install GitHub.cli
gh auth login
```

### 2. One-Time Setup (PATH Configuration)

Run this script once to make `dbt` command available everywhere:

```bash
cd 3030-pentaho-dbt
bash setup-dbt-path.sh
source ~/.bashrc
```

**Verify it worked:**
```bash
dbt --version
# Should show: dbt Cloud CLI - 0.40.7
```

### 3. Run Your First Migration

```bash
# Test with small dimension (safe, no git)
/improve dim_date

# Production migration (with git push)
/migrate dim_approval_level
```

**The system will guide you through the process** with Safe Mode prompts at each decision point.

**Done!** ✅

---

## 🔒 Safe Mode (NEW - Default Behavior)

**As of v3.1, the migration system runs in SAFE MODE by default.**

This means the system will pause and ask for your confirmation at critical points:

### What Safe Mode Does

✅ **Unknown Variables**
- System finds similar variables and suggests mappings
- You confirm if the suggestion is correct

✅ **Missing Row Counts**
- System asks if you want VIEW or TABLE materialization
- You choose based on expected data volume

✅ **Custom Functions**
- System detects unknown SQL functions
- You confirm if they're custom UDFs or standard Oracle

✅ **Missing Source Tables**
- System detects tables not in Snowflake
- You choose to skip, wait, or stop

✅ **Step Reviews**
- After each pipeline step, system shows results
- You confirm everything looks correct before continuing

### Example Interactions

```
Variable ${UNKNOWN_SCHEMA} not found.
Found similar: ${EKIP_SCHEMA} → EKIP (93% match). Use this?

Options:
1. Yes, use EKIP
2. No, I'll provide correct value
3. Stop, let me fix manually
```

This ensures you're always in control and prevents surprises!

---

## Understanding the System

### What It Does

Automatically converts **Pentaho transformations** (.ktr, .kjb) into **production-ready DBT models** for Snowflake:

```
Pentaho XML → Parse → Analyze → Translate → Generate → Validate → Git Push
```

### Two Commands

| Command | Purpose | Git Operations | Use When |
|---------|---------|----------------|----------|
| `/improve` | Test locally | ❌ No | Testing improvements, safe experimentation |
| `/migrate` | Production | ✅ Yes | Ready to deploy to production |

---

## The Migration Workflow

### Step-by-Step Process

**1. Parse** (`pentaho-parser` skill)
```bash
Input:  pentaho-sources/dim_approval_level/*.ktr, *.kjb
Output: dimensions/dim_approval_level/metadata/pentaho_raw.json
```
Extracts SQL, variables, steps, tables from Pentaho XML.

**2. Analyze** (`pentaho-analyzer` agent)
```bash
Input:  pentaho_raw.json, schema_registry.json
Output: pentaho_analyzed.json
```
Resolves variables, classifies tables (bronze/silver/gold), assesses complexity.

**3. Build Dependencies** (`dependency-graph-builder` agent)
```bash
Input:  pentaho_raw.json, pentaho_analyzed.json
Output: dependency_graph.json, dependency_graph.mmd
```
Determines execution order, detects circular dependencies.

**4. Translate SQL** (`sql-translator` agent)
```bash
Input:  pentaho_analyzed.json, oracle-snowflake-rules
Output: *_translated.sql, translation_metadata.json
```
Converts Oracle SQL to Snowflake, preserves custom UDFs.

**5. Generate DBT Models** (`dbt-model-generator` agent)
```bash
Input:  translation_metadata.json, dbt-best-practices
Output: DBT models in models/silver/, models/gold/
```
Creates production-ready DBT models with docs and tests.

**6. Validate Locally** (`quality-validator` agent) ✨ **NEW!**
```bash
Runs LOCALLY (no CI/CD wait):
  • dbt parse   (syntax validation)
  • dbt compile (template validation)
  • dbt run     (create models in Snowflake)
  • dbt test    (data quality tests)

If errors: Auto-fix and retry (max 2 times)
If passes: Git commit + push
```

**Total Time:** ~3 minutes (was 10-15 min with CI/CD)

### 📋 Review Screens (Safe Mode)

After each step, you'll see a review screen:

```
✅ STEP 2 COMPLETE: Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESOLVED VARIABLES:
✅ ${EKIP_SCHEMA} → EKIP

USER-CONFIRMED:
✅ ${NEW_VAR} → VALUE (you confirmed)

Review complete. Does everything look correct?
1. ✅ Yes, continue to Step 3
2. ❌ No, let me fix something
3. 📝 Show detailed analysis
```

This ensures you can review and confirm results before proceeding.

---

## Platform Support (GitHub & GitLab)

The system **auto-detects** your Git platform from the remote URL:

### GitHub
```bash
Remote: https://github.com/org/repo.git
→ Detected: GitHub
→ Uses: gh CLI
→ Creates: Pull Request
```

### GitLab
```bash
Remote: https://gitlab.com/org/repo.git
→ Detected: GitLab
→ Uses: glab CLI
→ Creates: Merge Request
```

**Same `/migrate` command works for both!**

---

## Configuration Files

### schema_registry.json

Maps Pentaho variables to Snowflake schemas:

```json
{
  "variables": {
    "EKIP_SCHEMA": {
      "snowflake_name": "EKIP",
      "type": "external",
      "layer": "bronze"
    }
  },
  "custom_functions": [
    {
      "name": "GETENNUML",
      "preserve": true,
      "deployment_required": true
    }
  ]
}
```

**When to edit:**
- Adding new Pentaho variable
- Declaring custom UDF (so it's not translated)

### TABLE_COUNT.csv (Optional)

Used for materialization optimization:

```csv
schema,table,row_count
EKIP,CONTRACTS,50234
EKIP,CUSTOMERS,12500
```

**Rules:**
- `> 10M rows` → Materialized as `table`
- `< 10M rows` → Materialized as `view`

---

## Folder Structure

```
3030-pentaho-dbt/
├── CLAUDE.md                    # Context for Claude Code
├── README.md                    # Overview
├── GETTING_STARTED.md          # This file
├── setup-dbt-path.sh           # PATH setup script
│
├── config/
│   ├── schema_registry.json    # Variable mappings
│   └── TABLE_COUNT.csv         # Table sizes (optional)
│
├── pentaho-sources/                    # INPUT: Pentaho source files
│   └── dim_approval_level/
│       ├── d_approval_level.ktr
│       └── *.kjb
│
├── dimensions/                 # OUTPUT: Metadata per dimension
│   └── dim_approval_level/
│       ├── metadata/
│       │   ├── pentaho_raw.json
│       │   ├── pentaho_analyzed.json
│       │   ├── dependency_graph.json
│       │   ├── translation_metadata.json
│       │   ├── dbt_generation_report.json
│       │   └── validation_report.json
│       └── sql/
│           └── *_translated.sql
│
├── tfses-dbt-snowflake-3030/  # DBT repository (git)
│   ├── dbt.exe                 # DBT CLI binary
│   ├── profiles.yml            # Snowflake connection
│   ├── dbt_project.yml
│   └── models/
│       ├── bronze/_sources.yml
│       ├── silver/
│       │   ├── silver_adq/
│       │   └── silver_mas/
│       └── gold/
│
└── .claude/
    ├── skills/                 # Deterministic operations
    │   ├── pentaho-parser/
    │   ├── oracle-snowflake-rules/
    │   └── dbt-best-practices/
    │       └── reference/
    │           └── repo_context/
    │               ├── macros.md
    │               ├── models_inventory.md
    │               ├── sources_inventory.md
    │               ├── test_patterns.md
    │               ├── project_config.md
    │               ├── lessons_learned.md       # 📚 NEW: Knowledge base
    │               └── learnings_summary.md     # 📚 NEW: Current migration guidance
    ├── agents/                 # AI-powered analysis (12 agents)
    │   ├── pentaho-analyzer.md
    │   ├── sql-translator.md
    │   ├── dbt-model-generator.md
    │   ├── quality-validator.md
    │   ├── learning-logger.md          # 📚 NEW: Processes learnings
    │   └── ... (7 more agents)
    └── commands/               # Workflow orchestration
        ├── migrate.md
        ├── improve.md
        └── pause-model-migration.md
```

---

## DBT Naming Conventions

The system follows strict naming rules:

| Pentaho File | DBT Model | Layer |
|--------------|-----------|-------|
| `adq_ekip_contracts.ktr` | `silver/silver_adq/stg_ekip_contracts.sql` | Silver ADQ |
| `mas_contracts.kjb` | `silver/silver_mas/mas_contracts.sql` | Silver MAS |
| `d_approval_level.ktr` | `gold/d_approval_level.sql` | Gold (dimension) |
| `f_sales.ktr` | `gold/f_sales.sql` | Gold (fact) |

**Pattern:**
- Remove `adq_` prefix → Add `stg_` prefix
- Keep `mas_` prefix
- Keep `d_` (dimension) and `f_` (fact) prefixes

---

## Common Tasks

### Migrate a New Dimension

```bash
# 1. Place Pentaho files
mkdir pentaho-sources/dim_customer
cp /path/to/*.ktr pentaho-sources/dim_customer/

# 2. Run migration
/migrate dim_customer

# 3. Review validation report
cat dimensions/dim_customer/metadata/validation_report.json | jq

# 4. Review Merge Request and merge
```

### Test Improvements Before Deploying

```bash
# Make changes to agents/skills
# Test without git operations
/improve dim_customer

# Compare results
diff -r tfses-dbt-snowflake-3030/models tfses-dbt-snowflake-3030-ai/models

# If good, run production
/migrate dim_customer
```

### Add New Variable Mapping

Edit `config/schema_registry.json`:

```json
{
  "variables": {
    "NEW_SCHEMA": {
      "snowflake_name": "ACTUAL_SCHEMA_NAME",
      "type": "external",
      "layer": "bronze"
    }
  }
}
```

Then re-run `/migrate`.

### Declare Custom UDF

Edit `config/schema_registry.json`:

```json
{
  "custom_functions": [
    {
      "name": "MY_CUSTOM_FUNCTION",
      "preserve": true,
      "deployment_required": true,
      "description": "Custom UDF - do not translate"
    }
  ]
}
```

**Remember:** Deploy UDF to Snowflake before running models!

---

## Troubleshooting

### "dbt: command not found"

**Cause:** PATH not set up

**Solution:**
```bash
source ~/.bashrc
# or
bash setup-dbt-path.sh
```

### "Cannot connect to Snowflake"

**Cause:** profiles.yml misconfigured

**Solution:**
```bash
cd tfses-dbt-snowflake-3030
dbt debug  # Test connection
```

Check `profiles.yml` has correct credentials.

### "Variable not found" Error

**Safe Mode Behavior:** System will suggest similar variables and ask for confirmation.

**If you choose "Stop, let me fix manually":**
Add to `config/schema_registry.json`:
```json
{
  "variables": {
    "YOUR_SCHEMA": {
      "snowflake_name": "ACTUAL_NAME",
      "type": "external",
      "layer": "bronze"
    }
  }
}
```

### "Circular dependency detected"

**Cause:** Pentaho transformations depend on each other in a loop

**Solution:**
1. Review `dimensions/{dimension}/metadata/dependency_graph.mmd`
2. Identify the cycle
3. Redesign transformation logic to break the loop
4. See `dependency_graph.json` for suggested break points

### "Source table not found in Snowflake"

**Safe Mode Behavior:** System will ask what you want to do:
- **Skip models** - Continue without models that use this table
- **Wait** - System waits 30s while you load the table
- **Stop** - Stop migration for critical tables

**To load missing tables:**
1. Copy data from Oracle to Snowflake
2. Choose "Wait" option when prompted
3. System will retry and continue

### Migration Fails with Errors

**The system will:**
1. Show you the error and ask what to do (Safe Mode)
2. Attempt auto-fix if you choose to continue (max 2 times)
3. If can't fix: Display clear error message with remediation steps
4. Fix manually
5. Re-run `/migrate {dimension}`

---

## Learning System (NEW in v3.1) 📚

**The system now learns from each migration to prevent repeated mistakes!**

### How It Works

Every time a migration encounters an issue and fixes it, the system can log it as a "learning":

```
quality-validator encounters issue → Signals 📚 LEARNING
    ↓
learning-logger agent → Processes and stores learning
    ↓
repo-analyzer → Reads learnings for next migration
    ↓
All agents → Receive proactive guidance
    ↓
Future migrations → Catch issues earlier!
```

### Example Learning

From dim_contract migration (2025-10-29):

**GETENUMML UDF Issue:**
- ❌ **Problem**: Function exists but returns wrong data
- ✅ **Solution**: Replace with explicit JOINs
- 🔍 **Prevention**: sql-translator now auto-detects and replaces
- 📈 **Impact**: Prevents data corruption in all future migrations

### Knowledge Base Location

`.claude/skills/dbt-best-practices/reference/repo_context/lessons_learned.md`

This file accumulates knowledge from all migrations and is automatically read by repo-analyzer.

### Benefits

- ✅ **Self-improving** - System gets smarter with each migration
- ✅ **Proactive** - Catches known issues before they fail
- ✅ **Faster** - Less manual intervention over time
- ✅ **Shared knowledge** - All agents learn from each other

See **CLAUDE.md** for detailed documentation on the learning system.

---

## Advanced Topics

### Auto-Fix Capabilities

The quality-validator agent can automatically fix:

**✅ Auto-fixable:**
- Missing source definitions → Adds to `_sources.yml`
- Common typos → `FORM` → `FROM`, `SLECT` → `SELECT`

**⚠️ Requires manual fix:**
- Invalid model references
- Complex SQL syntax errors
- Business logic issues

**Circuit breaker:** Max 2 auto-fix attempts, then stops.

### Local vs Remote Validation

| Aspect | Local (Current) | CI/CD (Optional) |
|--------|-----------------|------------------|
| **Speed** | 30 seconds | 2-5 minutes |
| **Setup** | None (dbt already works) | GitLab CI config needed |
| **Where runs** | Your machine | GitLab runner |
| **Snowflake creds** | Your local profile | CI/CD variables |
| **When to use** | Development, single developer | Production gate, team |

**Current workflow uses LOCAL validation** (faster, simpler).

Optional CI/CD setup available in `docs/archive/GITLAB_CICD_SETUP.md`.

### Materialization Strategy

Automatically determined:

| Layer | Default | Exception |
|-------|---------|-----------|
| **silver_adq** | `view` | `table` if > 10M rows |
| **silver_mas** | `table` | (business logic layer) |
| **gold dimensions** | `table` | (small, frequently queried) |
| **gold facts** | `incremental` | (large, append-only) |

Uses `TABLE_COUNT.csv` for row count lookup.

---

## Commands Reference

### Migration Commands

```bash
/migrate {dimension}          # Full migration with git push
/improve {dimension}          # Test locally (no git)
/migration-status             # Check all dimensions
/migration-status {dimension} # Check specific dimension
```

### DBT Commands (Local)

```bash
cd tfses-dbt-snowflake-3030

# Validation
dbt parse                              # Syntax check
dbt compile                            # Template resolution
dbt debug                              # Test Snowflake connection

# Execution
dbt run                                # Run all models
dbt run --select tag:dim_customer      # Run specific dimension
dbt test                               # Run all tests
dbt test --select tag:dim_customer     # Test specific dimension

# Documentation
dbt docs generate                      # Generate docs
dbt docs serve                         # View docs in browser
```

### Git Commands (if needed)

```bash
cd tfses-dbt-snowflake-3030

# Check status
git status
git branch  # See current branch
git log --oneline -10

# Create MR/PR manually
glab mr create  # GitLab
gh pr create    # GitHub

# View MR/PR
glab mr view    # GitLab
gh pr view      # GitHub
```

### 🚨 Branch Safety

**CRITICAL:** The system enforces this rule automatically:

```bash
# ✅ GOOD - Feature branch
git checkout -b migrate/dim_customer

# ❌ BAD - Protected branch (BLOCKED!)
git checkout develop  # System will abort migration
git checkout master   # System will abort migration
git checkout main     # System will abort migration
```

**Protection in place:**
1. `/migrate` command creates feature branch automatically
2. quality-validator checks current branch before commit
3. If on protected branch → Migration aborts with error

**You're safe!** The system won't let you commit to protected branches.

---

## Performance Tips

### Speed Up Migrations

1. **Use `/improve` for testing** - No git operations
2. **Migrate small dimensions first** - Test the workflow
3. **Run in parallel** (if multiple dimensions) - Each in separate terminal
4. **Pre-populate TABLE_COUNT.csv** - Faster materialization decisions

### Optimize Snowflake Costs

1. **Use XSMALL warehouse** for development
2. **Limit model selection**: `dbt run --select tag:dimension`
3. **Use views for small tables** (< 10M rows)
4. **Set auto-suspend**: 60 seconds idle time

---

## What's Next?

### After First Migration

1. ✅ Review the Merge Request
2. ✅ Verify models in Snowflake
3. ✅ Run `dbt test` to verify data quality
4. ✅ Deploy custom UDFs (if any)
5. ✅ Merge to main

### Ongoing Usage

- Migrate more dimensions
- Refine variable mappings in `schema_registry.json`
- Update TABLE_COUNT.csv as data grows
- Review and improve generated models

### Optional Enhancements

- Set up GitLab CI/CD for production gate (see `docs/archive/`)
- Add custom dbt macros
- Create data quality tests
- Build data catalog with dbt docs

---

## Getting Help

### Documentation

- **This file:** Getting started guide
- **CLAUDE.md:** Context for Claude Code agents
- **README.md:** Project overview
- **docs/archive/:** Detailed technical documentation

### Check Migration Status

```bash
/migration-status {dimension}
```

Shows:
- Which steps completed
- Current status
- Metadata file locations
- Next steps

### Common Issues

Most issues are auto-fixed or have clear error messages. If stuck:

1. Check validation report: `dimensions/{dimension}/metadata/validation_report.json`
2. Review error in terminal output
3. Check schema_registry.json for missing variables
4. Re-run `/migrate {dimension}` after fixes

---

## Summary

### Key Points

✅ **Two commands:** `/improve` (test) and `/migrate` (production)
✅ **Auto-detects:** GitHub vs GitLab from git remote
✅ **Fast validation:** Local dbt commands (~30 seconds)
✅ **Auto-fix:** Common errors fixed automatically
✅ **No CI/CD needed:** Validates locally (simpler setup)

### Typical Timeline

```
New dimension migration: ~3 minutes
  • Parse: 10 sec
  • Analyze: 20 sec
  • Dependencies: 10 sec
  • Translate: 30 sec
  • Generate: 30 sec
  • Validate (dbt): 30 sec
  • Git push: 20 sec
  • Total: ~3 min
```

---

**Ready to start?** Run `/migrate dim_date` to test with a small dimension! 🚀

---

**Version:** 3.1 (Learning System + Local Validation)
**Last Updated:** 2025-10-29
**Complexity:** Low-Medium
