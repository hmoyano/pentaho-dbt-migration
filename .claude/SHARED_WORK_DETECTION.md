# Shared Work Detection System

## Overview

This document describes how the migration system detects and handles shared work across dimensions to prevent redundant processing and file overwrites.

## Problem Statement

Multiple dimensions can share the same Pentaho files (especially ADQ/MAS layers):
- `dim_customer` and `dim_contract` both use `adq_ekip_customers.ktr`
- `dim_approval_level` and `dim_contract` both use `adq_status.ktr`

Without shared work detection:
- ❌ Same file gets parsed, translated, generated multiple times
- ❌ DBT models get overwritten, losing tags from previous dimensions
- ❌ Documentation gets lost
- ❌ Wasted processing time

## Solution: Migration Registry

**Location:** `config/migration_registry.json`

**Purpose:** Track all work done across dimensions at every pipeline stage

**Structure:**
```json
{
  "pentaho_files": {
    "<filename>": {
      "file_hash": "md5_hash",
      "dimensions": ["dim_a", "dim_b"],
      "dbt_model": "stg_model_name",
      "status": "completed",
      "parsed_date": "timestamp",
      "translated_date": "timestamp",
      "generated_date": "timestamp"
    }
  },
  "dbt_models": {
    "<model_name>": {
      "source_file": "pentaho_file.ktr",
      "dimensions": ["dim_a", "dim_b"],
      "model_path": "models/.../model.sql",
      "model_hash": "md5_hash",
      "shared": true,
      "tags": ["layer", "dim_a", "dim_b"]
    }
  },
  "sql_translations": {
    "<translation_file>": {
      "source_file": "pentaho_file.ktr",
      "dimensions": ["dim_a"],
      "translation_hash": "md5_hash"
    }
  },
  "dimensions": {
    "<dimension_name>": {
      "status": "completed|incomplete|failed",
      "pentaho_files": [...],
      "models_generated": [...]
    }
  }
}
```

## Registry Operations

### Read Registry
```python
def read_registry():
    registry_path = "config/migration_registry.json"
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            return json.load(f)
    else:
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "pentaho_files": {},
            "dbt_models": {},
            "sql_translations": {},
            "dimensions": {}
        }
```

### Update Registry
```python
def update_registry(registry, updates):
    registry["last_updated"] = datetime.now().isoformat()
    # Merge updates
    registry.update(updates)

    with open("config/migration_registry.json", 'w') as f:
        json.dump(registry, f, indent=2)
```

### Check if File Already Processed
```python
def is_file_processed(registry, filename, stage):
    if filename in registry["pentaho_files"]:
        file_info = registry["pentaho_files"][filename]
        return file_info.get(f"{stage}_date") is not None
    return False
```

### Check if File Hash Changed
```python
def has_file_changed(registry, filename, current_hash):
    if filename in registry["pentaho_files"]:
        return registry["pentaho_files"][filename]["file_hash"] != current_hash
    return True  # New file
```

## Stage-by-Stage Integration

### Stage 1: pentaho-parser (Skill)

**Check:**
- Read registry before parsing
- Skip files already parsed with same hash
- Update registry with parsed files and their dimensions

**Logic:**
```python
for pentaho_file in pentaho_files:
    current_hash = compute_md5(pentaho_file)

    if is_file_processed(registry, pentaho_file, "parsed"):
        if not has_file_changed(registry, pentaho_file, current_hash):
            print(f"[SKIP] {pentaho_file} already parsed (unchanged)")
            # Add dimension to existing entry
            registry["pentaho_files"][pentaho_file]["dimensions"].append(current_dimension)
            continue
        else:
            print(f"[RE-PARSE] {pentaho_file} changed since last parse")

    # Parse file
    parsed_data = parse_pentaho_file(pentaho_file)

    # Update registry
    registry["pentaho_files"][pentaho_file] = {
        "file_hash": current_hash,
        "dimensions": [current_dimension],
        "parsed_date": datetime.now().isoformat(),
        "status": "parsed"
    }
```

### Stage 2: pentaho-analyzer (Agent)

**Check:**
- Read registry at start
- Check which files have been analyzed
- Reuse analysis for shared files across dimensions

**Logic:**
```
1. Read dimensions/<dimension>/metadata/pentaho_raw.json
2. Read config/migration_registry.json
3. For each file in pentaho_raw.json:
   - Check if file already analyzed (same hash)
   - If yes and dimensions differ:
     → Reuse analysis from previous dimension
     → Add current dimension to registry
   - If no or hash changed:
     → Perform full analysis
     → Update registry
4. Write pentaho_analyzed.json (may include shared analyses)
5. Update registry with analyzed files
```

### Stage 3: dependency-graph-builder (Agent)

**Check:**
- Read registry to identify shared models
- Mark dependencies that span dimensions

**Logic:**
```
1. Read pentaho_analyzed.json + registry
2. Build dependency graph
3. For each node (file):
   - Check if file is shared across dimensions (registry.pentaho_files[file].dimensions)
   - If shared:
     → Mark as "shared_model: true"
     → List all dimensions using it
4. Write dependency_graph.json with shared indicators
5. Update registry with dependency metadata
```

### Stage 4: sql-translator (Agent)

**Check:**
- Skip translation if SQL already exists with same source hash
- Reuse translations for shared files

**Logic:**
```
1. Read translation_metadata.json from registry
2. For each SQL query:
   - Compute source hash (original SQL + variables)
   - Check registry.sql_translations[filename]
   - If translation exists and source_hash matches:
     → Skip translation
     → Add dimension to registry entry
   - Else:
     → Translate SQL
     → Write new translated file
     → Update registry
3. Return summary of translated + reused files
```

### Stage 5: dbt-model-generator (Agent)

**Check:**
- **CRITICAL** - Check if model already exists
- Merge tags if model is shared
- Update documentation without overwriting

**Logic:**
```
1. Read registry before generating any models
2. For each model to generate:

   A. Check if model exists in registry:
      if model_name in registry["dbt_models"]:
          existing = registry["dbt_models"][model_name]

          # Compare source file hash
          if existing["model_hash"] == current_source_hash:
              # Model unchanged - just add dimension tag
              add_dimension_tag_to_model(model_name, current_dimension)
              existing["dimensions"].append(current_dimension)
              existing["shared"] = True
              continue  # Skip generation
          else:
              # Source changed - regenerate
              print(f"[REGENERATE] {model_name} source changed")

   B. Check if model file exists on disk:
      if os.path.exists(model_path):
          # Read existing model
          existing_content = read_file(model_path)
          existing_tags = extract_tags(existing_content)

          # Merge tags
          merged_tags = list(set(existing_tags + [current_dimension]))

          # Update model with merged tags
          edit_model_tags(model_path, merged_tags)

          # Update registry
          registry["dbt_models"][model_name]["dimensions"].append(current_dimension)
          registry["dbt_models"][model_name]["tags"] = merged_tags
          registry["dbt_models"][model_name]["shared"] = True

          continue  # Skip generation

   C. Generate new model:
      write_dbt_model(model_path, model_content)

      # Add to registry
      registry["dbt_models"][model_name] = {
          "source_file": pentaho_file,
          "dimensions": [current_dimension],
          "model_path": model_path,
          "model_hash": compute_hash(model_content),
          "shared": False,
          "tags": [layer, current_dimension]
      }

3. For _models.yml documentation:
   - ALWAYS use Edit tool if file exists
   - Check if model already documented
   - Append new docs only if not present
   - Never overwrite existing docs

4. Update registry with all models (generated + skipped)
```

### Stage 6: quality-validator (Agent)

**Check:**
- Read registry to understand shared models
- Validate that shared models have correct tags
- Check documentation completeness

**Logic:**
```
1. Read registry
2. For each model:
   - If model is shared (registry.dbt_models[model]["shared"] == true):
     → Validate tags include ALL dimensions
     → Validate documentation mentions shared nature
3. Report shared model status in validation
```

## Migration Command Updates

### /migrate Command

**Before starting pipeline:**
```
1. Read migration_registry.json
2. Check dimension status:
   - If dimension completed: Ask user if they want to re-run
   - If dimension incomplete: Resume from last completed stage
3. Display shared files summary:
   "The following files are shared with other dimensions:
    - adq_ekip_customers.ktr (also used by: dim_contract)
    - Will reuse existing translations and merge tags"
```

**After pipeline completes:**
```
1. Update dimension status to "completed"
2. Display shared work summary:
   "Shared work detected:
    - 3 files reused from previous dimensions
    - 2 models updated with merged tags
    - Saved ~15 minutes of processing time"
```

## /migration-status Command

**Enhanced output:**
```
Dimension: dim_customer
Status: completed
Models: 7 (4 new, 3 shared)

Shared Models:
- stg_customers (also used by: dim_contract, dim_risk)
  Last updated: 2025-10-23
  Tags: [silver_adq, dim_customer, dim_contract, dim_risk]

- stg_status (also used by: dim_approval_level)
  Last updated: 2025-10-23
  Tags: [silver_adq, dim_customer, dim_approval_level]
```

## Benefits

1. **No Redundant Work**
   - Parse each file once
   - Translate SQL once
   - Generate models once

2. **No Overwrites**
   - Detect existing models
   - Merge tags instead of replacing
   - Append documentation instead of overwriting

3. **Fast Re-runs**
   - Skip unchanged files
   - Resume incomplete migrations
   - Quick validation-only runs

4. **Clear Visibility**
   - See which models are shared
   - Track which dimensions use which files
   - Understand cross-dimension dependencies

5. **Safe Incremental Migration**
   - Migrate dimensions one at a time
   - No risk of breaking existing work
   - Easy to add new dimensions

## Implementation Checklist

- [ ] Create migration_registry.json structure
- [ ] Update pentaho-parser skill with registry logic
- [ ] Update pentaho-analyzer agent with registry checks
- [ ] Update dependency-graph-builder agent to mark shared files
- [ ] Update sql-translator agent with translation reuse
- [ ] Update dbt-model-generator agent with merge logic
- [ ] Update quality-validator agent with shared model checks
- [ ] Update /migrate command with registry checks
- [ ] Update /migration-status command with shared model display
- [ ] Add utility functions for registry operations
- [ ] Test with overlapping dimensions
- [ ] Document in README.md

## Testing Plan

1. **Test Case: Non-overlapping dimensions**
   - Migrate dim_date
   - Migrate dim_customer
   - Verify: No shared work, all models independent

2. **Test Case: Overlapping dimensions**
   - Migrate dim_customer (has adq_ekip_customers.ktr)
   - Migrate dim_contract (also uses adq_ekip_customers.ktr)
   - Verify:
     - File parsed once
     - SQL translated once
     - Model has merged tags: [silver_adq, dim_customer, dim_contract]
     - Documentation preserved

3. **Test Case: Changed file**
   - Migrate dim_customer
   - Modify adq_ekip_customers.ktr
   - Migrate dim_customer again
   - Verify: File re-parsed, SQL re-translated, model regenerated

4. **Test Case: Resume incomplete**
   - Migrate dim_approval_level (incomplete)
   - Re-run /migrate dim_approval_level
   - Verify: Skips completed stages, resumes from failure point

## Notes

- Registry file should be committed to git
- Consider registry backup before major migrations
- Registry enables future features:
  - Impact analysis ("which dimensions affected by this file change?")
  - Selective re-generation ("regenerate only models from changed Pentaho files")
  - Dependency visualization across dimensions
