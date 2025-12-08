# Pentaho to DBT Migration Project

Automated migration system for converting Pentaho Data Integration (Kettle) transformations to production-ready DBT models.

## 🔒 Safe Mode (Default Behavior)

**As of v3.1, SAFE MODE is now the default** - the system will automatically pause and ask for your confirmation at critical decision points:

- ✅ **Unknown variables** → Suggests mappings, asks for confirmation
- ✅ **Missing row counts** → Asks for materialization preference (VIEW vs TABLE)
- ✅ **Custom UDFs** → Confirms classification before preservation
- ✅ **Missing source tables** → Lets you skip, wait, or stop
- ✅ **Step reviews** → Shows results after each step for confirmation

This ensures no surprises and gives you full control over the migration process.

---

## 📚 Learning System (NEW in v3.1)

**The system now learns from each migration to prevent repeated mistakes!**

### How It Works

```
quality-validator encounters issue → Signals 📚 LEARNING
    ↓
learning-logger agent → Processes and stores
    ↓
repo-analyzer → Reads knowledge base
    ↓
All agents → Receive proactive guidance
    ↓
Future migrations → Catch issues earlier!
```

### Knowledge Base

- **Location**: `.claude/skills/dbt-best-practices/reference/repo_context/lessons_learned.md`
- **Categories**: SQL_TRANSLATION, UDF_HANDLING, CASE_SENSITIVITY, PERFORMANCE, etc.
- **Benefit**: System gets smarter with each migration, reducing manual intervention

### Example

From dim_contract (2025-10-29):
- **GETENUMML UDF Issue** (HIGH): Function broken → Replace with explicit JOINs
- **Case Sensitivity** (MEDIUM): Lowercase columns → Use quoted identifiers

See **CLAUDE.md** for full learning system documentation.

---

## 🚀 Quick Start

### Test Improvements Locally (NOW)

```bash
# Test improvements without git operations
/improve dim_approval_level
```

Creates test models in `tfses-dbt-snowflake-3030-ai/` for comparison.

### Production Migration (After GitHub)

```bash
# Full migration with git operations and CI/CD
/migrate dim_approval_level
```

Creates branch, commits, pushes, and waits for CI/CD validation.

### Check Migration Status

```bash
/migration-status dim_approval_level
```

---

## 📁 Project Structure

```
3030-pentaho-dbt/
├── .claude/                           # Claude Code configuration
│   ├── agents/                        # AI agents for analysis and generation
│   ├── commands/                      # Custom commands (/migrate, /improve)
│   └── skills/                        # Deterministic operations and templates
├── config/                            # Configuration files
│   ├── schema_registry.json          # Variable mappings and UDF definitions
│   ├── TABLE_COUNT.csv               # Row counts for optimization
│   └── tables_columns_info.csv       # Column metadata
├── dimensions/                        # Migration metadata per dimension
│   └── <dimension>/
│       ├── metadata/                  # JSON analysis results
│       └── sql/                       # Translated SQL files
├── docs/                              # Documentation
│   └── GITHUB_CICD_WORKFLOW.md      # CI/CD setup guide
├── pentaho-sources/                           # INPUT: Pentaho source files
│   └── <dimension>/
│       ├── *.ktr                     # Transformations
│       └── *.kjb                     # Jobs
├── tfses-dbt-snowflake-3030/         # OUTPUT: Production DBT repository
│   └── models/                        # Generated DBT models
├── archive/                           # Archived old files (cleanup)
└── Core documentation files
    ├── README.md                      # This file
    ├── CLAUDE.md                      # Claude Code context
    ├── MIGRATION_WORKFLOW.md          # Detailed workflow
    └── SYSTEM_OVERVIEW.md             # Architecture overview
```

---

## 📖 Documentation

- **[Migration Workflow Guide](MIGRATION_WORKFLOW.md)** - Complete step-by-step guide
- **[System Overview](SYSTEM_OVERVIEW.md)** - Architecture and components
- **[Claude Context](CLAUDE.md)** - Context for Claude Code
- **[GitHub CI/CD Guide](docs/GITHUB_CICD_WORKFLOW.md)** - CI/CD setup instructions

---

## 🏗️ System Architecture

### Two Migration Workflows

| Command | Purpose | Git Operations | Output Location | When to Use |
|---------|---------|----------------|-----------------|-------------|
| `/improve` | Test improvements locally | ❌ No | `tfses-dbt-snowflake-3030-ai/` | Before committing changes |
| `/migrate` | Production migration | ✅ Yes | `tfses-dbt-snowflake-3030/` | After GitHub setup |

### Pipeline Flow (7 Steps)

```
Step 0:   Git Setup (branch or copy repo)           ← NEW!
Step 0.5: Repository Analysis (scan existing)       ← NEW!
Step 1:   Parse Pentaho Files
Step 2:   Analyze Transformations
Step 3:   Build Dependencies
Step 4:   Translate SQL
Step 5:   Generate DBT Models
Step 6:   Validate & Push (if /migrate)
```

### Agent Relationships

```
                    repo-analyzer (NEW!)
                         ↓
                [Creates context files]
                         ↓
pentaho-parser → pentaho-analyzer → dependency-graph-builder
       ↓                ↓                      ↓
              sql-translator (reads all)
                         ↓
            dbt-model-generator (avoids duplicates)
                         ↓
            quality-validator (git ops if /migrate)
```

### Components

**Main Workflow Agents** (AI-powered reasoning):
1. `repo-analyzer` - Scans DBT repo, identifies shared models, reads learnings
2. `pentaho-analyzer` - Resolves variables, classifies tables
3. `dependency-graph-builder` - Detects circular dependencies
4. `sql-translator` - Oracle → Snowflake with UDF expansion
5. `dbt-model-generator` - Creates models, skips existing shared
6. `quality-validator` - Static validation + git/CI/CD + signals learnings 📚

**Helper Agents** (Problem solvers - call on-demand):
- `learning-logger` - Processes and persists learnings to knowledge base 📚 NEW!
- `dependency-resolver` - Fixes circular dependencies
- `pentaho-deep-analyzer` - Deep-dives into Pentaho XML
- `pentaho-cross-reference` - Finds similar patterns
- `sql-function-lookup` - Researches unknown functions
- `dbt-validator-fixer` - Auto-fixes DBT errors

See [docs/HELPER_AGENTS.md](docs/HELPER_AGENTS.md) for when to use helper agents.

**Skills** (Deterministic operations):
- `pentaho-parser` - Extracts metadata from Pentaho XML
- `oracle-snowflake-rules` - SQL translation patterns
- `dbt-best-practices` - Templates and naming conventions

**Commands** (Workflow orchestrators):
- `/improve <dimension>` - Test improvements locally
- `/migrate <dimension>` - Production migration with git
- `/migration-status [dimension]` - Check progress

---

## 🎯 Prerequisites

### 1. Required Files

**Schema Registry** (`config/schema_registry.json`):

Defines Pentaho variable mappings and custom functions.

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

### 2. Optional Files

**Table Count** (`config/TABLE_COUNT.csv`):

Helps optimize materialization strategies.

```csv
schema,table,row_count
EKIP,CONTRACTS,50234
EKIP,CUSTOMERS,12500
```

### 3. Source Files

Place Pentaho files in `pentaho-sources/<dimension>/`:

```
pentaho-sources/dim_approval_level/
├── *.ktr  (transformations)
└── *.kjb  (jobs)
```

---

## 🔄 Migration Workflow

### Option 1: Automated (Recommended)

Run the full pipeline with one command:

```bash
/migrate dim_approval_level
```

This executes all 6 steps automatically with progress tracking.

### Option 2: Manual (Step-by-Step)

Run each step individually for more control:

```bash
# Step 1: Parse
/pentaho-parser dim_approval_level

# Step 2: Analyze
[Ask Claude to run pentaho-analyzer agent]

# Step 3: Build dependency graph
[Ask Claude to run dependency-graph-builder agent]

# Step 4: Translate SQL
[Ask Claude to run sql-translator agent]

# Step 5: Generate DBT models
[Ask Claude to run dbt-model-generator agent]

# Step 6: Validate
[Ask Claude to run quality-validator agent]
```

See [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md) for detailed instructions.

---

## ✅ Validation & Testing

After migration completes:

### 1. Check Validation Status

```bash
/migration-status dim_approval_level
```

### 2. Review Validation Report

```bash
cat dimensions/dim_approval_level/metadata/validation_report.json | jq
```

### 3. Deploy Custom UDFs (if needed)

If validation report shows custom functions:

```sql
-- Deploy to Snowflake
CREATE OR REPLACE FUNCTION GETENNUML(...)
RETURNS VARCHAR
AS
$$
  -- Your UDF logic
$$;
```

### 4. Test DBT Models

```bash
# Compile
dbt compile

# Run models
dbt run --select tag:dim_approval_level

# Run tests
dbt test --select tag:dim_approval_level

# Generate docs
dbt docs generate
dbt docs serve
```

---

## 📊 Output Files

### Metadata (Per Dimension)

Located in `dimensions/<dimension>/metadata/`:

| File | Source | Contains |
|------|--------|----------|
| `pentaho_raw.json` | pentaho-parser | Parsed Pentaho metadata |
| `pentaho_analyzed.json` | pentaho-analyzer | Variable resolution, complexity |
| `dependency_graph.json` | dependency-graph-builder | Dependencies, execution order |
| `translation_metadata.json` | sql-translator | SQL translation details |
| `dbt_generation_report.json` | dbt-model-generator | Generated models summary |
| `validation_report.json` | quality-validator | Quality validation results |

### DBT Models

Located in `models/`:

| Layer | Directory | File Pattern | Example |
|-------|-----------|--------------|---------|
| Bronze | `staging/<source>/` | `staging__<source>_<table>.sql` | `staging__ekip_contracts.sql` |
| Silver | `intermediate/` | `intermediate__<table>.sql` | `intermediate__contracts.sql` |
| Gold | `marts/core/` | `dim_<entity>.sql` | `dim_approval_level.sql` |
| Gold | `marts/core/` | `fact_<subject>.sql` | `fact_sales.sql` |

---

## 🔧 Configuration

### Schema Registry

The schema registry maps Pentaho variables to Snowflake schemas and defines custom functions.

**Location**: `config/schema_registry.json`

**Structure**:

```json
{
  "variables": {
    "VARIABLE_NAME": {
      "snowflake_name": "SCHEMA_NAME",
      "type": "external" | "internal",
      "description": "Description",
      "layer": "bronze" | "silver" | "gold"
    }
  },
  "custom_functions": [
    {
      "name": "FUNCTION_NAME",
      "description": "What it does",
      "preserve": true,
      "deployment_required": true
    }
  ]
}
```

### DBT Project Configuration

The migration system creates/updates `dbt_project.yml` automatically.

**Manual overrides** can be added for specific models:

```yaml
models:
  pentaho_migration:
    marts:
      core:
        dim_approval_level:
          +materialized: table  # Override default
```

---

## 🐛 Troubleshooting

### Common Issues

#### "Variable not found in schema_registry.json"

**Safe Mode Behavior**: System will suggest similar variables and ask for confirmation.

**Manual Fix**: Add variable to `config/schema_registry.json`

#### "Source table not found in Snowflake"

**Safe Mode Behavior**: System will ask if you want to:
- Skip models using this table
- Wait while you load the table
- Stop migration (for critical tables)

**Manual Fix**: Load missing tables to Snowflake before running migration

#### "Circular dependency detected"

**Solution**: Review `dependency_graph.json` and refactor Pentaho transformations

#### "dbt parse failed"

**Solution**: Check `validation_report.json` for specific syntax errors

#### "Custom function not preserved"

**Safe Mode Behavior**: System will ask if function is custom UDF or standard Oracle.

**Manual Fix**: Add function to `schema_registry.json` custom_functions

#### "Migration paused at review screen"

**Solution**: This is normal safe mode behavior. Review the results and choose:
- ✅ Continue to next step
- ❌ Stop to fix issues
- 📝 View detailed information

See [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md#troubleshooting) for more solutions.

---

## 📈 Migration Checklist

For each dimension:

- [ ] Pentaho files in `pentaho-sources/<dimension>/`
- [ ] Schema registry configured
- [ ] Run `/migrate <dimension>`
- [ ] Review validation report
- [ ] Deploy custom UDFs (if needed)
- [ ] Test with `dbt run` and `dbt test`
- [ ] Verify data in Snowflake
- [ ] Commit to version control

---

## 🎓 Learning Resources

### Key Concepts

- **Pentaho Transformations (.ktr)**: Define ETL logic
- **Pentaho Jobs (.kjb)**: Orchestrate transformations
- **DBT Models**: SQL transformations in version control
- **Materialization**: How DBT builds models (table, view, incremental)
- **Sources**: External data (bronze layer)
- **Refs**: Internal dependencies between models

### Documentation

- [DBT Documentation](https://docs.getdbt.com/)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference)
- [Pentaho Documentation](https://help.hitachivantara.com/Documentation/Pentaho)

### Migration System Docs

- [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md) - Complete workflow guide
- [oracle-snowflake-rules](.claude/skills/oracle-snowflake-rules/) - SQL translation reference
- [dbt-best-practices](.claude/skills/dbt-best-practices/) - DBT patterns and conventions

---

## 🤝 Contributing

### Adding New Source Systems

1. Add to `schema_registry.json`:
   ```json
   "NEW_SCHEMA": {
     "snowflake_name": "NEW_SYSTEM",
     "type": "external",
     "layer": "bronze"
   }
   ```

2. Create sources.yml in `models/staging/new_system/`

### Adding Custom UDFs

1. Add to `schema_registry.json`:
   ```json
   {
     "name": "NEW_UDF",
     "preserve": true,
     "deployment_required": true
   }
   ```

2. Deploy to Snowflake before running models

### Extending Translation Rules

Edit `.claude/skills/oracle-snowflake-rules/reference/function_mappings.md`

---

## 📝 Version History

- **v3.1** (2025-01-28)
  - **SAFE MODE now default** - Interactive confirmation at all decision points
  - Added review screens after each pipeline step
  - Enhanced error handling with user choices
  - Pre-validation checks for source tables

- **v3.0** (2025-01-27)
  - Local validation with dbt commands
  - GitLab support added
  - Enhanced repository analysis

- **v1.0** (2025-10-23)
  - Initial release
  - 3 skills, 5 agents, 2 commands
  - Complete migration pipeline
  - Automated workflow orchestration

---

## 🚦 Next Steps

After setting up the system:

1. **Configure** `schema_registry.json` for your environment
2. **Place** Pentaho files in `pentaho-sources/` folder
3. **Run** `/migrate <dimension>` for first dimension
4. **Review** validation results
5. **Test** DBT models in Snowflake
6. **Iterate** on additional dimensions

---

## 📞 Support

For issues or questions:

1. Check [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md#troubleshooting)
2. Review metadata JSON files for details
3. Check validation report for specific errors
4. Review agent documentation in `.claude/agents/`

---

## 📜 License

Internal project for Pentaho to DBT migration.

---

**Built with Claude Code** 🤖

Automated migration system using AI-powered agents for intelligent transformation, analysis, and code generation.
