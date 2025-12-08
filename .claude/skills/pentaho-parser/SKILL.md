---
name: pentaho-parser
description: Parse Pentaho XML files (.ktr/.kjb) and extract structured metadata for DBT migration
---

# Pentaho Parser Skill

## Purpose

Parse Pentaho ETL files (transformations and jobs) to extract structured metadata needed for migrating to DBT models on Snowflake. This skill handles the deterministic task of XML parsing and metadata extraction without interpretation.

## What This Skill Does

- **Parses .ktr files** (Kettle transformations): Extracts steps, SQL queries, variables, source/target tables
- **Parses .kjb files** (Kettle jobs): Extracts job entries, transformation calls, execution order
- **Extracts metadata**: Variables, connections, table references, SQL queries (preserved as-is)
- **Detects patterns**: Layer identification (adq_, mas_, d_, f_), complexity estimation
- **Generates JSON**: Structured output in dimension-specific `metadata/pentaho_raw.json`
- **Tracks parsed files**: Uses `config/migration_registry.json` to avoid re-parsing unchanged files
- **Hash-based detection**: Only re-parses files that have been modified since last run

## When to Use This Skill

Use this skill when you need to:
- Parse Pentaho XML files in a dimension folder
- Extract metadata from transformations before migration
- Analyze existing ETL logic and dependencies
- Generate structured input for translation agents

**Don't use this skill for:**
- SQL translation (use translation agents instead)
- DBT model generation (use generator agents instead)
- Business logic interpretation (use analysis agents instead)

## Usage Examples

### Parse All Files in a Dimension
```
Parse all Pentaho files in dimensions/dim_approval_level/
```

### Parse Another Dimension
```
Parse Pentaho files in dimensions/dim_customer/
```
Note: The skill will skip any files already parsed (tracked in migration registry).

### Force Re-parse (if needed)
To re-parse files that have already been processed, you would need to clear the registry entry or modify the source files.

## Output Format

The skill generates files in two locations:

1. **Dimension metadata**: `<dimension_folder>/metadata/pentaho_raw.json`
2. **Migration registry**: `config/migration_registry.json` (tracks all parsed files)

**JSON Structure:**
```json
{
  "files": [
    {
      "file_name": "adq_ekip_contracts.ktr",
      "file_type": "transformation",
      "level": "adq",
      "transformation_name": "ADQ - EKIP Contracts",
      "variables": ["${EKIP_SCHEMA}", "${ODS_SCHEMA}"],
      "sql_queries": ["SELECT * FROM ${EKIP_SCHEMA}.CONTRACTS WHERE..."],
      "tables_input": ["${EKIP_SCHEMA}.CONTRACTS"],
      "tables_output": ["ODS_SCHEMA.STG_CONTRACTS"],
      "steps": [
        {
          "step_name": "Get Contracts",
          "step_type": "TableInput",
          "sql_query": "...",
          "connection": "EKIP_CONN"
        },
        {
          "step_name": "Write to STG_CONTRACTS",
          "step_type": "TableOutput",
          "table_name": "STG_CONTRACTS",
          "truncate": true,
          "commit_size": "1000"
        }
      ],
      "statistics": {
        "total_steps": 5,
        "sql_steps": 2,
        "estimated_complexity": "low"
      }
    }
  ]
}
```

## Implementation Details

### Script Location
- `scripts/pentaho_parser.py`

### Key Features
1. **XML Parsing**: Handles Pentaho's XML structure with namespaces
2. **CDATA Extraction**: Properly extracts SQL from CDATA sections
3. **Variable Detection**: Regex pattern `\$\{([A-Z_]+)\}` finds all variables
4. **Layer Detection**: Identifies adq, mas, d_, f_ prefixes from filenames
5. **Dimension Detection**: Automatically detects dimension from folder name
6. **Registry Tracking**:
   - Stores MD5 hash of each parsed file
   - Skips re-parsing if file hash matches registry
   - Tracks which dimension each file belongs to
   - Auto-detects registry location in project root
7. **Complexity Estimation**:
   - Low: < 5 steps
   - Medium: 5-15 steps
   - High: > 15 steps
8. **Error Handling**: Graceful handling of malformed XML or missing elements

### Script Arguments
- `directory_path`: Path to folder containing .ktr/.kjb files (e.g., `dimensions/dim_approval_level/`)
- `--output` (optional): Custom output path for pentaho_raw.json
- Automatically creates output in `<directory_path>/metadata/pentaho_raw.json`
- Automatically updates `config/migration_registry.json` in project root

## Architecture Notes

**Project Layer Naming:**
- `adq_*` = Acquisition layer (Bronze) - Raw data ingestion
- `mas_*` = Master layer (Silver) - Cleaned and transformed
- `d_*` = Dimension tables (Gold) - Business entities
- `f_*` = Fact tables (Gold) - Business events

**Important:**
- This skill does NOT translate SQL (Oracle → Snowflake)
- This skill does NOT interpret business logic
- This skill PRESERVES original SQL formatting exactly
- Output is used as input for downstream translation agents

## Error Handling

The parser handles:
- Missing XML elements (uses empty arrays/null)
- Malformed XML (reports error, continues with other files)
- Missing CDATA sections (captures empty string)
- File read errors (skips file, logs error)

## Dependencies

- Python 3.7+
- Standard library only: `xml.etree.ElementTree`, `json`, `re`, `pathlib`, `argparse`
