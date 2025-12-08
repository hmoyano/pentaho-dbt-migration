# Pentaho to DBT Migration Project

## Project Overview

This project provides an automated migration system to convert **Pentaho Data Integration (Kettle)** transformations into production-ready **DBT models** for Snowflake.

### 🔒 Safe Mode (Default Behavior)

**As of 2025-01-28, SAFE MODE is the default for all migration operations.**

The system will automatically pause and ask for user confirmation at critical decision points:
- **Unknown variables**: Confirm suggested schema mappings before proceeding
- **Missing row counts**: Choose materialization strategy for tables
- **Custom UDFs**: Confirm function classification before preservation
- **Missing source tables**: Decide whether to skip, wait, or stop
- **Step reviews**: Confirm results after each major pipeline step

This ensures no surprises and gives you full control over the migration process.

### Core Purpose
- Parse Pentaho XML files (.ktr transformations, .kjb jobs)
- Analyze transformation logic and dependencies
- Translate Oracle SQL to Snowflake SQL
- Generate DBT models following best practices
- Validate quality and readiness for deployment

---

## Configuration (project.config.json)

**All paths are configurable** - no hardcoded paths in commands or agents.

```json
{
  "project_name": "tfses-pentaho-dbt-migration",
  "paths": {
    "dbt_repository": "./tfses-dbt-snowflake-3030",
    "pentaho_sources": "./pentaho-sources",
    "dimensions_output": "./dimensions",
    "facts_output": "./facts"
  },
  "snowflake": {
    "database": "TFSES_ANALYTICS",
    "schemas": {
      "bronze": "TFS_BRONZE",
      "silver": "TFS_SILVER",
      "gold": "TFS_GOLD"
    }
  },
  "git": {
    "protected_branches": ["main", "master", "develop"],
    "branch_prefix": "migrate/"
  }
}
```

**Key paths:**
- `dbt_repository` - DBT Git repo (models output)
- `pentaho_sources` - Source Pentaho files (.ktr, .kjb)
- `dimensions_output` - Dimension migration output (d_*, dim_*)
- `facts_output` - Fact migration output (f_*, fact_*)

---

## Project Structure

**CRITICAL**: This project uses TWO separate directories:

### 1. Main Project Directory (C:/Users/hecto/Documents/projects/3030-pentaho-dbt/)
**Working directory for Claude Code** - Contains all migration logic, config, and metadata

```
3030-pentaho-dbt/                  [MAIN PROJECT - Claude working directory]
├── .claude/
│   ├── agents/                    # AI-powered analysis (13 agents)
│   │   ├── pentaho-analyzer.md
│   │   ├── pentaho-deep-analyzer.md
│   │   ├── pentaho-cross-reference.md
│   │   ├── dependency-graph-builder.md
│   │   ├── dependency-resolver.md
│   │   ├── sql-translator.md
│   │   ├── sql-function-lookup.md
│   │   ├── dbt-model-generator.md
│   │   ├── dbt-validator-fixer.md
│   │   ├── quality-validator.md
│   │   ├── repo-analyzer.md
│   │   ├── migration-docs-generator.md  # NEW
│   │   └── learning-logger.md
│   │
│   ├── commands/                  # Workflow orchestration (6 commands)
│   │   ├── migrate.md             # Full pipeline with git
│   │   ├── improve.md             # Test locally (no git)
│   │   ├── continue-migration.md  # Modify existing migrations
│   │   ├── migration-status.md    # Check progress
│   │   └── _pipeline_steps.md     # Shared pipeline logic
│   │
│   └── skills/                    # Deterministic operations (4 skills)
│       ├── pentaho-parser/        # Parse Pentaho XML
│       ├── oracle-snowflake-rules/# SQL translation rules
│       ├── dbt-best-practices/    # DBT templates & conventions
│       └── sql-translation-rules/ # Additional SQL rules
│
├── config/
│   ├── schema_registry.json       # Variable mappings (${VAR} → Snowflake schema)
│   ├── TABLE_COUNT.csv            # Table row counts for optimization
│   └── migration_registry.json    # Auto-generated tracking file
│
├── pentaho-sources/                       # INPUT: Source Pentaho files
│   └── <dimension>/
│       ├── *.ktr                  # Pentaho transformations
│       └── *.kjb                  # Pentaho jobs
│
├── dimensions/                    # OUTPUT: Dimension-specific metadata
│   └── <dimension>/
│       ├── metadata/
│       │   ├── pentaho_raw.json              # Step 1: Parsed Pentaho
│       │   ├── pentaho_analyzed.json         # Step 2: Analysis
│       │   ├── dependency_graph.json         # Step 3: Dependencies
│       │   ├── translation_metadata.json     # Step 4: SQL translation
│       │   ├── dbt_generation_report.json    # Step 5: DBT models
│       │   └── validation_report.json        # Step 6: Validation
│       └── sql/
│           └── *_translated.sql   # Translated SQL files
│
├── facts/                         # OUTPUT: Fact-specific metadata (f_*, fact_*)
│   └── <fact>/
│       ├── metadata/              # Same structure as dimensions
│       └── sql/
│
└── tfses-dbt-snowflake-3030/      # → See DBT Git Repository below
```

### 2. DBT Git Repository (./tfses-dbt-snowflake-3030/)
**Separate Git repo** - Contains DBT models, macros, and configuration

```
tfses-dbt-snowflake-3030/          [GIT REPO - GitLab tracked]
├── .git/                          # Git repository (remote: gitlab.stratebi.com)
├── models/                        # OUTPUT: DBT models
│   ├── bronze/
│   │   └── _sources.yml           # All source definitions
│   ├── silver/
│   │   ├── silver_adq/
│   │   │   ├── stg_*.sql          # Staging models
│   │   │   └── _models.yml        # Documentation
│   │   └── silver_mas/
│   │       ├── mas_*.sql          # Master models
│   │       └── _models.yml        # Documentation
│   └── gold/
│       ├── d_*.sql                # Dimension models
│       ├── f_*.sql                # Fact models (if any)
│       └── _models.yml            # Documentation
│
├── macros/                        # Custom DBT macros
├── dbt_project.yml                # DBT configuration
├── dbt.exe                        # DBT executable
└── profiles.yml                   # Snowflake connection (not in repo)
```

### Key Path Conventions

**All paths in agents/commands must be explicit:**

- **Main project paths** (relative to `3030-pentaho-dbt/`):
  - `config/schema_registry.json`
  - `pentaho-sources/<dimension>/`
  - `dimensions/<dimension>/metadata/`
  - `.claude/agents/`, `.claude/skills/`

- **DBT repo paths** (relative to `3030-pentaho-dbt/tfses-dbt-snowflake-3030/`):
  - `tfses-dbt-snowflake-3030/models/`
  - `tfses-dbt-snowflake-3030/macros/`
  - `tfses-dbt-snowflake-3030/dbt_project.yml`

**Agents must know:**
- `repo-analyzer`, `dbt-model-generator`, `quality-validator` → Work in DBT repo
- All other agents → Work in main project directory

---

## Migration Pipeline

### 6-Step Process

**Step 1: Parse** (`pentaho-parser` skill)
- Input: `pentaho-sources/<dimension>/*.ktr, *.kjb`
- Output: `dimensions/<dimension>/metadata/pentaho_raw.json`
- What: Extracts SQL, variables, steps, tables from Pentaho XML

**Step 2: Analyze** (`pentaho-analyzer` agent)
- Input: `pentaho_raw.json`, `schema_registry.json`
- Output: `pentaho_analyzed.json`
- What: Resolves variables, classifies tables, assesses complexity

**Step 3: Dependencies** (`dependency-graph-builder` agent)
- Input: `pentaho_raw.json`, `pentaho_analyzed.json`
- Output: `dependency_graph.json`
- What: Builds dependency graph, determines execution order

**Step 4: Translate** (`sql-translator` agent)
- Input: `pentaho_analyzed.json`, `dependency_graph.json`, `oracle-snowflake-rules`
- Output: Translated SQL files, `translation_metadata.json`
- What: Converts Oracle SQL to Snowflake, preserves custom UDFs

**Step 5: Generate** (`dbt-model-generator` agent)
- Input: `translation_metadata.json`, `dependency_graph.json`, `dbt-best-practices`
- Output: DBT models in `models/silver/`, `models/gold/`, `dbt_generation_report.json`
- What: Creates production-ready DBT models with tests & docs following team conventions

**Step 6: Validate** (`quality-validator` agent)
- Input: All metadata + DBT models
- Output: `validation_report.json`
- What: Validates syntax, references, documentation, tests

---

## Key Concepts

### Layers (Team Conventions)
- **Bronze**: Source definitions → `models/bronze/_sources.yml`
- **Silver ADQ**: Raw data extraction → `models/silver/silver_adq/stg_*.sql`
- **Silver MAS**: Business logic applied → `models/silver/silver_mas/mas_*.sql`
- **Gold**: Dimensional/fact models → `models/gold/d_*.sql`, `f_*.sql`

### Naming Conventions
- Pentaho `adq_*.ktr` → DBT `silver/silver_adq/stg_*.sql` (remove adq_, add stg_)
- Pentaho `mas_*.kjb` → DBT `silver/silver_mas/mas_*.sql` (keep mas_)
- Pentaho `d_*.ktr` → DBT `gold/d_*.sql` (keep d_ prefix)
- Pentaho `f_*.ktr` → DBT `gold/f_*.sql` (keep f_ prefix)

**Examples:**
- `adq_ekip_contracts.ktr` → `silver/silver_adq/stg_ekip_contracts.sql`
- `mas_contracts.kjb` → `silver/silver_mas/mas_contracts.sql`
- `d_approval_level.ktr` → `gold/d_approval_level.sql`
- `d_date.ktr` → `gold/d_date.sql`

### Folder Structure (in DBT Git Repo)
**Location**: `tfses-dbt-snowflake-3030/models/`

```
tfses-dbt-snowflake-3030/models/
├── bronze/
│   └── _sources.yml              # All source definitions (ekip, miles, etc.)
├── silver/
│   ├── silver_adq/
│   │   ├── stg_*.sql             # From adq_*.ktr files
│   │   └── _models.yml           # Documentation
│   └── silver_mas/
│       ├── mas_*.sql             # From mas_*.kjb files
│       └── _models.yml           # Documentation
└── gold/
    ├── d_*.sql                   # From d_*.ktr files
    ├── f_*.sql                   # From f_*.ktr files (if any)
    └── _models.yml               # Documentation
```

### Materialization Strategy
- **silver_adq**: `view` (default) or `table` if >10M rows (uses TABLE_COUNT.csv)
- **silver_mas**: `table` (business logic layer)
- **gold dimensions**: `table` (small, frequently queried)
- **gold facts**: `incremental` (large, append-only)

### Tags
- **silver_adq**: Layer tag for ADQ models
- **silver_mas**: Layer tag for MAS models
- **gold**: Layer tag for dimensions and facts
- **<dimension_name>**: Dimension group tag (e.g., `dim_approval_level`)

### Variable Resolution
- Pentaho: `${EKIP_SCHEMA}.CONTRACTS`
- Resolved: `EKIP.CONTRACTS` (via `config/schema_registry.json` in main project)
- DBT: `{{ source('ekip', 'contracts') }}` (defined in `tfses-dbt-snowflake-3030/models/bronze/_sources.yml`)

### Custom Functions

**CRITICAL INSTRUCTION**: The `GETENUMML()` UDF is **NOT WORKING CORRECTLY** in Snowflake and must be replaced with explicit JOINs.

#### GETENUMML Replacement Pattern (MANDATORY)

**Never use**: `TFSES_ANALYTICS.TFS_SILVER.GETENUMML(column, language_id)`

**Always replace with this pattern**:

```sql
-- 1. Add these source CTEs if not already present:
source_sysenumeration as (
    select * from {{ source('bronze', 'MILES_SYSENUMERATION') }}
),

source_translatedstring as (
    select * from {{ source('bronze', 'MILES_TRANSLATEDSTRING') }}
),

source_language as (
    select * from {{ source('bronze', 'MILES_LANGUAGE') }}
),

-- 2. Add enum_translations CTE:
enum_translations as (
    select
        s.sysenumeration_id,
        coalesce(
            t1.translation,           -- Direct translation for language_id=4
            t2.translation,           -- Parent language fallback
            s.description             -- Final fallback to base description
        ) as description_ml
    from source_sysenumeration s
    left join source_translatedstring t1
        on t1.language_id = 4
        and t1.multilanguagestring_id = s.description_mlid
    left join source_language l
        on l.language_id = 4
    left join source_translatedstring t2
        on l.parentlanguage_id = t2.language_id
        and t2.multilanguagestring_id = s.description_mlid
),

-- 3. In main query, replace function call with JOIN:
-- BEFORE: TFSES_ANALYTICS.TFS_SILVER.GETENUMML(ls1.Insurance_TC, 4) as insurance_desc
-- AFTER:  enum_ins.description_ml as insurance_desc

-- 4. Add LEFT JOIN in main query:
left join enum_translations enum_ins
    on enum_ins.sysenumeration_id = ls1.Insurance_TC
```

**Reference Implementation**: See `tfses-dbt-snowflake-3030/models/silver/silver_adq/stg_miles_product.sql` (lines 53-73) and `stg_miles_contract.sql` (lines 126-348)

**Benefits**:
- Avoids broken UDF dependency
- More maintainable and debuggable
- Better performance (computed once in CTE)
- Explicit fallback chain visible in code

**Other Custom Functions**:
- `GETMAP()` and other UDFs should be evaluated case-by-case
- If UDF is working correctly, it can be preserved
- Always test UDFs in Snowflake before using

---

## How to Use

### Quick Start
```bash
# Run complete migration for a dimension
/migrate dim_approval_level

# Check migration status
/migration-status dim_approval_level
```

### Step-by-Step
```bash
# Step 1: Parse
/pentaho-parser dim_approval_level

# Steps 2-6: Run agents individually
# (Ask Claude to invoke each agent)
```

---

## Important Files

### schema_registry.json
Defines Pentaho variable mappings and custom functions.

**Purpose**: Maps Pentaho variables like `${EKIP_SCHEMA}` to Snowflake schemas like `EKIP`.

**Structure**:
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

### TABLE_COUNT.csv
Optional file with table row counts for performance optimization.

**Format**:
```csv
schema,table,row_count
EKIP,CONTRACTS,50234
EKIP,CUSTOMERS,12500
```

---

## Agent Behavior

### How Agents Work
1. **Agents write files DURING execution** (using Bash, Write, Edit tools)
2. **Agents return TEXT REPORT** to main conversation
3. **Each agent reads previous agent outputs** from metadata files
4. **Agents are stateless** - they read all context on startup

### Agent Output Pattern
- **During execution**: Writes JSON metadata file (e.g., `pentaho_analyzed.json`)
- **Returns to main**: Text summary of what was done, issues found, recommendations

### Example Agent Flow
```
User → Invokes pentaho-analyzer
  ↓
Agent reads: pentaho_raw.json, schema_registry.json
  ↓
Agent analyzes: Resolves variables, classifies tables
  ↓
Agent writes: pentaho_analyzed.json (using Write tool)
  ↓
Agent returns: "✅ Analysis complete. 17 files analyzed, 3 variables resolved..."
  ↓
Main conversation receives text summary
```

---

## Common Tasks

### Add a New Dimension
1. Place Pentaho files in `pentaho-sources/<dimension>/`
2. Run `/migrate <dimension>`
3. Review validation report
4. Deploy custom UDFs if needed
5. Test with `dbt run` and `dbt test`

### Update Schema Registry
Edit `config/schema_registry.json` to add new variables or custom functions.

### Check Migration Status
```bash
/migration-status              # All dimensions
/migration-status <dimension>  # Specific dimension
```

### Troubleshooting
- **"Variable not found"**: Add to `schema_registry.json`
- **"Circular dependency"**: Review `dependency_graph.json`
- **"dbt parse failed"**: Check `validation_report.json` for syntax errors
- **"Custom function not preserved"**: Add to `schema_registry.json` custom_functions

---

## Dependencies

### Required
- DBT installed and configured
- Snowflake connection
- Python 3.8+ (for pentaho-parser skill)

### Optional
- dbt_utils package (for surrogate keys, tests)

---

## Documentation

- **README.md**: Quick start and overview
- **MIGRATION_WORKFLOW.md**: Detailed step-by-step guide
- **SYSTEM_OVERVIEW.md**: Architecture and diagrams
- **This file (CLAUDE.md)**: Context for Claude Code

---

## Learning System (Automatic Knowledge Accumulation)

**NEW as of 2025-10-29**: The migration system now automatically learns from each migration to prevent repeated mistakes.

### How It Works

1. **quality-validator** (and other agents) encounter issues → signal learnings using `📚 LEARNING:` format
2. User invokes **learning-logger** agent → extracts and categorizes learnings
3. **learning-logger** updates knowledge base → `.claude/skills/dbt-best-practices/reference/repo_context/lessons_learned.md`
4. **repo-analyzer** reads knowledge base → provides context to all downstream agents
5. **Future migrations** automatically benefit → common pitfalls caught earlier

### Learning Format

Agents signal learnings using this format:

```markdown
📚 LEARNING: [Category]
**Pattern**: [What went wrong]
**Solution**: [How it was fixed]
**Prevention**: [How to detect proactively]
**Impact**: [HIGH/MEDIUM/LOW]
**Agents Affected**: [agent1, agent2]
**Dimension**: [dimension_name]
**Date**: [YYYY-MM-DD]
```

### Categories

- **SQL_TRANSLATION** - Oracle to Snowflake issues
- **DBT_SYNTAX** - DBT configuration/syntax
- **UDF_HANDLING** - Custom function issues (like GETENUMML)
- **CASE_SENSITIVITY** - Snowflake case issues
- **PERFORMANCE** - Performance optimizations
- **DEPENDENCY** - Cross-dimension dependencies
- **SCHEMA_MAPPING** - Variable/schema resolution
- **DATA_QUALITY** - Data validation issues
- **OTHER** - General learnings

### How to Use

**After a migration completes with issues:**

```bash
# quality-validator will include 📚 LEARNING blocks in its report

# Then invoke learning-logger to persist them:
# (This will be added to workflow automation in future)
Task(
  subagent_type="learning-logger",
  prompt="Extract learnings from quality-validator report for dimension dim_contract and log to knowledge base"
)
```

**Knowledge base location**: `.claude/skills/dbt-best-practices/reference/repo_context/lessons_learned.md`

### Benefits

- ✅ **Prevents repeated mistakes** - System learns from each migration
- ✅ **Proactive error detection** - Agents check for known issues before they fail
- ✅ **Faster migrations over time** - Less manual intervention needed
- ✅ **Knowledge sharing** - All agents benefit from learnings
- ✅ **Continuous improvement** - System gets smarter with each dimension

### Example Learning

From dim_contract migration (2025-10-29):

**GETENUMML UDF Issue (HIGH IMPACT)**:
- **Pattern**: GETENUMML UDF exists but produces incorrect results
- **Solution**: Replace with explicit JOINs using enum_translations CTE
- **Prevention**: sql-translator now auto-detects and replaces this pattern
- **Impact**: Prevents data corruption in all future migrations

See full knowledge base for all accumulated learnings.

---

## Best Practices

1. **Migrate one dimension at a time** - Test thoroughly before moving to next
2. **Review metadata files** - Check for unresolved variables, circular dependencies
3. **Handle custom UDFs early** - Deploy to Snowflake before running models
4. **Validate before deploying** - Only proceed after validation passes
5. **Test in Snowflake** - Run `dbt test` to verify data quality
6. **Signal learnings** - When encountering novel issues, use `📚 LEARNING:` format so system learns

---

## Agent Responsibilities (Summary)

### Main Workflow Agents (6)
| Agent | Reads | Writes | Returns |
|-------|-------|--------|---------|
| repo-analyzer | DBT repository | repo_context/*.md | Repository analysis |
| pentaho-analyzer | pentaho_raw.json, schema_registry.json | pentaho_analyzed.json | Analysis summary |
| dependency-graph-builder | pentaho_raw.json, pentaho_analyzed.json | dependency_graph.json | Dependency summary |
| sql-translator | pentaho_analyzed.json, dependency_graph.json | *_translated.sql, translation_metadata.json | Translation summary |
| dbt-model-generator | translation_metadata.json, dependency_graph.json, repo_context | DBT models, dbt_generation_report.json | Generation summary |
| quality-validator | All metadata + DBT models | validation_report.json | Validation results |

### Helper Agents (5) - On-Demand
| Agent | Purpose | When to Call |
|-------|---------|--------------|
| dependency-resolver | Resolve circular dependencies | When Step 3 detects cycles |
| pentaho-deep-analyzer | Deep XML parsing | When analyzer needs more detail |
| pentaho-cross-reference | Find similar patterns | When unknown variables found |
| sql-function-lookup | Research SQL functions | When unknown functions found |
| dbt-validator-fixer | Fix DBT errors | When CI/CD fails |

---

## 🚨 MEGA-IMPORTANT SAFETY RULE

**NEVER commit directly to `develop`, `master`, or `main` branches!**

**Protection in place:**
- `/migrate` command automatically creates feature branches (`migrate/{dimension}`)
- `quality-validator` agent checks current branch before git operations
- If on protected branch → **Migration aborts immediately with error**

**Protected branches:** `develop`, `master`, `main`
**Safe branches:** `migrate/*`, `feature/*`, `fix/*`

This protection is **CRITICAL** and must never be disabled.

---

## Project Status

**Current State**: Complete migration system with 3 skills, 11 agents (6 main + 5 helpers), 3 commands

**Commands**:
- `/improve` - Test improvements locally (no git)
- `/migrate` - Production migration (with git push + MR/PR)
- `/migration-status` - Check migration progress

**Validation**: Local dbt commands (parse/compile/run/test) - ~30 seconds

**Ready For**: Production use on Pentaho dimensions

**Next Steps**: Configure schema_registry.json and migrate first dimension

---

## Safe Mode Features (NEW)

### What Safe Mode Does

**Safe Mode is now the DEFAULT behavior** - the system will automatically:

1. **Ask for confirmation** when encountering ambiguities:
   - Unknown Pentaho variables → Suggests mappings, asks for confirmation
   - Missing table row counts → Asks for materialization preference
   - Unknown SQL functions → Asks if custom UDF or standard Oracle
   - Missing source tables → Asks to skip, wait, or stop

2. **Review screens after each step** (during `/migrate` command):
   - Step 2 Review: Confirm analysis results
   - Step 3 Review: Confirm dependency graph
   - Step 4 Review: Confirm SQL translation
   - Step 5 Review: Confirm DBT models generated
   - Each review allows you to continue, stop, or view details

3. **Pre-validation checks**:
   - Checks if source tables exist BEFORE running dbt
   - Validates schema mappings before translation
   - Confirms custom functions before preservation

### Benefits of Safe Mode

✅ **No surprises** - You approve every critical decision
✅ **Catch errors early** - Missing tables detected before dbt run
✅ **Build confidence** - Understand what system is doing
✅ **Learn the data** - Discover variables/tables you didn't know about
✅ **Iterate faster** - Stop at first issue, fix, resume

### Example Safe Mode Interactions

**Unknown Variable Example:**
```
Variable ${UNKNOWN_SCHEMA} not found in schema_registry.json.
Found similar: ${EKIP_SCHEMA} → EKIP (confidence: 93%). Use this?

Options:
1. Yes, use EKIP (93% match)
2. No, I'll provide correct value
3. Stop, let me fix manually
```

**Missing Table Example:**
```
Source table EKIP.CONTRACTS not found in Snowflake.
Referenced in models: stg_ekip_contracts, mas_contracts. What should I do?

Options:
1. Skip models using this table
2. Wait, I'll copy the table now
3. Stop migration (critical table)
```

**Step Review Example:**
```
✅ STEP 2 COMPLETE: Analysis

RESOLVED VARIABLES:
✅ ${EKIP_SCHEMA} → EKIP (from schema_registry.json)
✅ ${ODS_SCHEMA} → ODS (from schema_registry.json)

USER-CONFIRMED VARIABLES:
✅ ${UNKNOWN_SCHEMA} → EKIP (confidence: 93%, you confirmed)

Review complete. Does everything look correct?
1. ✅ Yes, continue to Step 3
2. ❌ No, let me fix something
3. 📝 Show detailed analysis
```

## File Path Rules (Workaround for Claude Code v1.0.111 Bug)
- When reading or editing a file, **ALWAYS use relative paths.**
- Example: `./src/components/Component.tsx` ✅
- **DO NOT use absolute paths.**
- Example: `C:/Users/user/project/src/components/Component.tsx` ❌
- Reason: This is a workaround for a known bug in Claude Code v1.0.111 (GitHub Issue

---

**Version**: 3.1 (Safe Mode Default + Interactive Migration)
**Created**: 2025-10-23
**Updated**: 2025-01-28
**Maintained By**: Data Engineering Team

