---
description: Check the status of a dimension migration
---

# Migration Status Checker

You are checking the migration status for a dimension.

## User Request

The user wants to check status for: **{{ DIMENSION_NAME }}**

(If dimension name not provided, ask the user which dimension to check, or list all dimensions)

---

## Status Check Process

### Step 1: Identify Dimension

If dimension name not provided:

```bash
# List all dimensions
ls dimensions/
```

If user wants summary of all dimensions, proceed to check each one.

---

### Step 2: Check Metadata Files

For the specified dimension, check which metadata files exist:

```bash
# Check metadata folder
ls dimensions/{{ DIMENSION_NAME }}/metadata/ 2>/dev/null || echo "No metadata found"
```

**Expected files** (in order of pipeline):
1. `pentaho_raw.json` - Step 1 complete
2. `pentaho_analyzed.json` - Step 2 complete
3. `dependency_graph.json` - Step 3 complete
4. `dependency_graph.mmd` - Step 3 complete
5. `translation_metadata.json` - Step 4 complete
6. `dbt_generation_report.json` - Step 5 complete
7. `validation_report.json` - Step 6 complete

---

### Step 3: Check Translated SQL

```bash
# Check SQL folder
ls dimensions/{{ DIMENSION_NAME }}/sql/ 2>/dev/null || echo "No translated SQL found"
```

---

### Step 4: Check DBT Models

```bash
# Search for models that likely came from this dimension
# This is approximate - models don't store dimension origin explicitly

# Check for models tagged with dimension name
grep -r "tag.*{{ DIMENSION_NAME }}" models/ --include="*.sql" 2>/dev/null || echo "No models found with dimension tag"
```

---

### Step 5: Read Key Metrics

If `validation_report.json` exists (final step):

```bash
cat dimensions/{{ DIMENSION_NAME }}/metadata/validation_report.json | jq '{
  dimension: .dimension,
  validation_date: .validation_date,
  overall_status: .overall_status,
  error_count: .error_count,
  warning_count: .warning_count,
  models_validated: .models_validated,
  documentation_coverage: .validation_results.documentation_validation.column_coverage,
  test_coverage: .validation_results.test_validation.overall_coverage
}'
```

If `dbt_generation_report.json` exists:

```bash
cat dimensions/{{ DIMENSION_NAME }}/metadata/dbt_generation_report.json | jq '{
  dimension: .dimension,
  generation_date: .generation_date,
  total_models: .summary.total_models,
  staging_models: .summary.staging_models,
  intermediate_models: .summary.intermediate_models,
  mart_models: .summary.mart_models,
  total_tests: .summary.total_tests,
  all_documented: .summary.all_documented
}'
```

If `translation_metadata.json` exists:

```bash
cat dimensions/{{ DIMENSION_NAME }}/metadata/translation_metadata.json | jq '{
  dimension: .dimension,
  translation_date: .translation_date,
  files_translated: .summary.total_files_translated,
  confidence_breakdown: .summary.confidence_breakdown,
  custom_functions: .summary.custom_functions_detected
}'
```

If `dependency_graph.json` exists:

```bash
cat dimensions/{{ DIMENSION_NAME }}/metadata/dependency_graph.json | jq '{
  dimension: .dimension,
  total_nodes: .summary.total_nodes,
  execution_steps: .summary.execution_steps,
  parallel_groups: .summary.parallel_groups,
  circular_dependencies: .summary.circular_dependencies_count
}'
```

If `pentaho_analyzed.json` exists:

```bash
cat dimensions/{{ DIMENSION_NAME }}/metadata/pentaho_analyzed.json | jq '{
  dimension: .dimension,
  total_files: .summary.total_files,
  complexity_breakdown: .summary.complexity_breakdown,
  unresolved_variables: .summary.unresolved_variables,
  external_sources: (.summary.external_sources | length)
}'
```

If `pentaho_raw.json` exists:

```bash
cat dimensions/{{ DIMENSION_NAME }}/metadata/pentaho_raw.json | jq '{
  dimension: .dimension,
  files_parsed: (.files | length)
}'
```

---

## Status Report Format

Provide a clear, visual status report:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MIGRATION STATUS: {{ DIMENSION_NAME }}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pipeline Progress:

[✅/❌] Step 1: Parse Pentaho Files
   [If complete: Files parsed: X]
   [If complete: Output: pentaho_raw.json (created YYYY-MM-DD)]
   [If incomplete: Not started]

[✅/❌] Step 2: Analyze Transformations
   [If complete: Variables resolved: X/Y]
   [If complete: Complexity: X low, Y medium, Z high]
   [If complete: Output: pentaho_analyzed.json (created YYYY-MM-DD)]
   [If incomplete: Not started / Pending Step 1]

[✅/❌] Step 3: Build Dependency Graph
   [If complete: Dependencies: X nodes, Y execution steps]
   [If complete: Circular dependencies: X]
   [If complete: Output: dependency_graph.json (created YYYY-MM-DD)]
   [If incomplete: Not started / Pending Step 2]

[✅/❌] Step 4: Translate SQL
   [If complete: Files translated: X]
   [If complete: Confidence: X high, Y medium, Z low]
   [If complete: Custom functions: [list]]
   [If complete: Output: X SQL files (created YYYY-MM-DD)]
   [If incomplete: Not started / Pending Step 3]

[✅/❌] Step 5: Generate DBT Models
   [If complete: Models generated: X (Y staging, Z intermediate, W marts)]
   [If complete: Documentation: X%]
   [If complete: Tests: X]
   [If complete: Output: DBT models (created YYYY-MM-DD)]
   [If incomplete: Not started / Pending Step 4]

[✅/❌] Step 6: Validate Quality
   [If complete: Status: PASSED/PASSED_WITH_WARNINGS/FAILED]
   [If complete: Errors: X, Warnings: Y]
   [If complete: Test coverage: X%]
   [If complete: Documentation coverage: X%]
   [If complete: Output: validation_report.json (created YYYY-MM-DD)]
   [If incomplete: Not started / Pending Step 5]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Progress: [X/6 steps complete]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[If incomplete]:
Next Step: [Name of next step]
Command: [How to run next step]

[If complete and PASSED]:
✅ Migration complete and validated!

Next steps:
1. Deploy custom UDFs (if any): [list]
2. Run: dbt compile
3. Run: dbt run --select tag:{{ DIMENSION_NAME }}
4. Run: dbt test --select tag:{{ DIMENSION_NAME }}

[If complete and PASSED_WITH_WARNINGS]:
⚠️  Migration complete with warnings

Warnings to address:
[List warnings from validation_report.json]

Next steps:
1. Review warnings above
2. Deploy custom UDFs (if any): [list]
3. Run: dbt compile
4. Run: dbt run --select tag:{{ DIMENSION_NAME }}
5. Run: dbt test --select tag:{{ DIMENSION_NAME }}

[If complete and FAILED]:
❌ Migration failed validation

Errors found:
[List errors from validation_report.json]

Remediation:
[List recommendations from validation_report.json]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Metadata Location: dimensions/{{ DIMENSION_NAME }}/metadata/
[If models generated]: Models Location: models/staging/, models/intermediate/, models/marts/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Summary Mode (All Dimensions)

If user wants status for all dimensions:

```bash
# List all dimensions
for dim in dimensions/*/; do
  dim_name=$(basename "$dim")
  echo "=== $dim_name ==="

  # Count metadata files
  metadata_count=$(ls "dimensions/$dim_name/metadata/" 2>/dev/null | wc -l)
  echo "Metadata files: $metadata_count/7"

  # Check validation status if exists
  if [ -f "dimensions/$dim_name/metadata/validation_report.json" ]; then
    status=$(cat "dimensions/$dim_name/metadata/validation_report.json" | jq -r '.overall_status')
    echo "Validation: $status"
  else
    echo "Validation: Not yet run"
  fi

  echo ""
done
```

Provide summary table:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MIGRATION STATUS: ALL DIMENSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Dimension              | Progress | Status                |
|------------------------|----------|-----------------------|
| dim_approval_level     | 6/6      | ✅ PASSED             |
| dim_customer           | 5/6      | ⏳ Pending validation |
| dim_product            | 3/6      | ⏳ Pending translation |
| dim_contract           | 0/6      | ❌ Not started        |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary:
- Total dimensions: X
- Complete: Y
- In progress: Z
- Not started: W
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tip: Use /migration-status <dimension> for detailed status
```

---

## Additional Checks

### Check for Issues

If any step shows low confidence, errors, or warnings:

```bash
# Check translation issues
cat dimensions/{{ DIMENSION_NAME }}/metadata/translation_metadata.json | jq '.issues'

# Check validation issues
cat dimensions/{{ DIMENSION_NAME }}/metadata/validation_report.json | jq '{
  errors: .errors,
  warnings: .warnings
}'

# Check unresolved variables
cat dimensions/{{ DIMENSION_NAME }}/metadata/pentaho_analyzed.json | jq '.summary.unresolved_variables'

# Check circular dependencies
cat dimensions/{{ DIMENSION_NAME }}/metadata/dependency_graph.json | jq '.circular_dependencies'
```

### Check Custom Functions

```bash
# List custom functions detected
cat dimensions/{{ DIMENSION_NAME }}/metadata/translation_metadata.json | jq '.summary.custom_functions_detected'

# Check if UDFs need deployment
cat dimensions/{{ DIMENSION_NAME }}/metadata/dbt_generation_report.json | jq '[.models_generated[] | select(.requires_udf_deployment == true) | {model: .model_name, functions: .custom_functions_used}]'
```

---

## Important Notes

- **Progress is sequential** - Steps must be completed in order
- **Metadata files are the source of truth** - If file exists, step is complete
- **Timestamps matter** - Check file modification times to see when steps ran
- **Validation is final gate** - Only proceed to DBT deployment after validation passes

Be clear, concise, and helpful in status reporting.
