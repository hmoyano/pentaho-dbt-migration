# Safe Mode Changes for Migration System

## Overview

Making safe-mode the **DEFAULT** behavior for all agents. All ambiguities and unknowns will prompt the user for confirmation before proceeding.

---

## Change 1: pentaho-analyzer.md

### Location: Lines 399-450 (Variable resolution section)

### Current Behavior (REMOVE):
```
**If resolution_status = "RESOLVED" (confidence >= 0.8):**
- Auto-resolve the variable mapping
- Update schema_registry in memory
- Pipeline CONTINUES without asking user
```

### New Behavior (ADD):
```
**If resolution_status = "RESOLVED" (confidence >= 0.8):**

🔒 SAFE MODE (DEFAULT): ASK USER FOR CONFIRMATION

Use AskUserQuestion tool:

AskUserQuestion(
  questions=[{
    "question": "Variable ${UNKNOWN_SCHEMA} not found in schema_registry.json. Found similar: ${EKIP_SCHEMA} → EKIP (confidence: 93%). Use this?",
    "header": "Unknown Var",
    "multiSelect": false,
    "options": [
      {
        "label": "Yes, use EKIP (93% match)",
        "description": "System analyzed similar patterns across Pentaho files"
      },
      {
        "label": "No, I'll provide correct value",
        "description": "Enter the correct Snowflake schema name yourself"
      },
      {
        "label": "Stop, let me fix manually",
        "description": "Block pipeline to update schema_registry.json"
      }
    ]
  }]
)

Handle response:
- "Yes" → Use suggested value, mark as user_confirmed=true
- "No" → Prompt for value, use their input
- "Stop" → Add CRITICAL blocking issue, stop pipeline
```

---

## Change 2: pentaho-analyzer.md

### Location: Step 3 - Analyze Variables (lines 147-232)

### Add New Step: Missing Tables in TABLE_COUNT.csv

**Current:** Silently uses default materialization

**New:** Ask user for materialization preference

```
### Step 3.5: Handle Missing Table Row Counts

For tables NOT in TABLE_COUNT.csv:

AskUserQuestion(
  questions=[{
    "question": "Table STG_CONTRACTS has unknown row count (not in TABLE_COUNT.csv). How should I materialize this model?",
    "header": "Materialization",
    "multiSelect": false,
    "options": [
      {
        "label": "View (recommended for small tables)",
        "description": "Fast to build, slower queries. Good for <1M rows."
      },
      {
        "label": "Table (recommended for large tables)",
        "description": "Slower to build, faster queries. Good for >1M rows."
      },
      {
        "label": "Let me add row count first",
        "description": "Stop so you can update TABLE_COUNT.csv"
      }
    ]
  }]
)
```

---

## Change 3: sql-translator.md

### Location: Lines 296-374 (Unknown SQL function handling)

### Current Behavior:
```
If classification = "CUSTOM_UDF":
- Preserve as-is (AUTO-DECIDED)
- Mark deployment_required
- Pipeline CONTINUES
```

### New Behavior:
```
If classification = "CUSTOM_UDF":

🔒 SAFE MODE: Confirm with user

AskUserQuestion(
  questions=[{
    "question": "Function GETENUMML detected. System classified as Custom UDF (not standard Oracle). Preserve as-is for Snowflake?",
    "header": "Custom UDF",
    "multiSelect": false,
    "options": [
      {
        "label": "Yes, preserve (deploy to Snowflake)",
        "description": "Keep function as-is. You'll need to deploy this UDF to Snowflake."
      },
      {
        "label": "No, it's actually standard Oracle",
        "description": "System should translate this to Snowflake equivalent"
      },
      {
        "label": "Stop, let me research",
        "description": "Block pipeline to investigate this function manually"
      }
    ]
  }]
)
```

---

## Change 4: quality-validator.md

### Location: NEW - Add before Step 3 (dbt validation)

### Add New Step: Pre-Check Source Tables

```
### Step 2.5: Pre-Check Source Tables Exist in Snowflake

BEFORE running dbt run, validate all source tables exist:

1. Extract all source tables from bronze/_sources.yml
2. For each source table, query Snowflake: SELECT 1 FROM {schema}.{table} LIMIT 1
3. If any table missing:

AskUserQuestion(
  questions=[{
    "question": "Source table EKIP.CONTRACTS not found in Snowflake. Referenced in models: stg_ekip_contracts, mas_contracts. What should I do?",
    "header": "Missing Table",
    "multiSelect": false,
    "options": [
      {
        "label": "Skip models using this table",
        "description": "Continue but exclude models that depend on this source"
      },
      {
        "label": "Wait, I'll copy the table now",
        "description": "Pause migration while you load data to Snowflake"
      },
      {
        "label": "Stop migration (critical table)",
        "description": "This table is essential - cannot continue without it"
      }
    ]
  }]
)

Handle response:
- "Skip" → Add --exclude flag to dbt run, log skipped models
- "Wait" → Sleep 30s, retry check (max 3 retries)
- "Stop" → Add CRITICAL error, exit immediately
```

---

## Change 5: migrate.md (orchestrator)

### Location: After each step (Steps 2, 3, 4, 5)

### Add Mandatory Review Screens

```
### Review Screen Template (After Each Step)

After Step 2 (Analysis) completes:

Display review screen and wait for user confirmation:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ STEP 2 COMPLETE: Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESOLVED VARIABLES:
✅ ${EKIP_SCHEMA} → EKIP (from schema_registry.json)
✅ ${ODS_SCHEMA} → ODS (from schema_registry.json)

USER-CONFIRMED VARIABLES:
✅ ${UNKNOWN_SCHEMA} → EKIP (confidence: 93%, you confirmed)

TABLES WITHOUT ROW COUNTS:
⚠️  STG_CONTRACTS → Will use VIEW (you selected)
⚠️  STG_CUSTOMERS → Will use VIEW (you selected)

CUSTOM FUNCTIONS DETECTED:
📋 GETENUMML → Will be preserved (deployment required)

FILES ANALYZED: 17
COMPLEXITY: 5 low, 2 medium, 0 high

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AskUserQuestion(
  questions=[{
    "question": "Review complete. Does everything look correct?",
    "header": "Step 2 Review",
    "multiSelect": false,
    "options": [
      {
        "label": "✅ Yes, continue to Step 3",
        "description": "Everything looks good, proceed with dependency graph"
      },
      {
        "label": "❌ No, let me fix something",
        "description": "Stop pipeline so you can update config files"
      },
      {
        "label": "📝 Show detailed analysis",
        "description": "View full pentaho_analyzed.json before deciding"
      }
    ]
  }]
)
```

---

## Change 6: quality-validator.md

### Location: Step 3.3 (dbt run error handling)

### Enhance Error Handling for Missing Tables

```
### If dbt run fails with "Table does not exist":

Parse error message to extract table name, then:

AskUserQuestion(
  questions=[{
    "question": "dbt run failed: Table EKIP.CONTRACTS does not exist in Snowflake. Models affected: stg_ekip_contracts (1 of 15 models). What should I do?",
    "header": "Missing Table",
    "multiSelect": false,
    "options": [
      {
        "label": "Skip this model, continue others",
        "description": "Exclude stg_ekip_contracts, run remaining 14 models"
      },
      {
        "label": "I'll copy the table now (retry)",
        "description": "Wait 30s for you to load data, then retry"
      },
      {
        "label": "Stop validation",
        "description": "This is a critical table - cannot proceed"
      }
    ]
  }]
)
```

---

## Summary of Changes

| Agent | Change | User Impact |
|-------|--------|-------------|
| **pentaho-analyzer** | Ask before using cross-reference suggestions | Confirms all unknown variables |
| **pentaho-analyzer** | Ask about materialization for tables without row counts | Controls performance strategy |
| **sql-translator** | Ask before preserving custom UDFs | Verifies function classification |
| **quality-validator** | Pre-check source tables before dbt run | Catches missing tables early |
| **quality-validator** | Ask what to do when tables missing | Allows skip/retry/stop |
| **migrate** (orchestrator) | Add review screens after each step | See all assumptions before continuing |

---

## Benefits of Safe Mode as Default

1. ✅ **No surprises** - You approve every decision
2. ✅ **Catch errors early** - Missing tables detected before dbt run
3. ✅ **Build confidence** - Understand what system is doing
4. ✅ **Learn the data** - Discover variables/tables you didn't know about
5. ✅ **Iterate faster** - Stop at first issue, fix, resume

---

## Implementation Checklist

- [ ] Update pentaho-analyzer.md (unknown variables)
- [ ] Update pentaho-analyzer.md (missing row counts)
- [ ] Update sql-translator.md (unknown functions)
- [ ] Update quality-validator.md (pre-check source tables)
- [ ] Update quality-validator.md (handle missing table errors)
- [ ] Update migrate.md (add review screens)
- [ ] Test with a real dimension migration
- [ ] Update CLAUDE.md to document safe-mode as default

---

**Created:** 2025-01-28
**Status:** Ready for implementation
