# Helper Agents - Problem Solvers

These agents are **NOT part of the main workflow** but can be called on-demand when specific problems arise.

## When to Use Helper Agents

### 1. dbt-validator-fixer
**Purpose**: Auto-fixes DBT validation errors

**When to use**:
- CI/CD fails with syntax errors
- Missing source definitions
- Invalid ref() references

**How to call**:
```
Task(
    subagent_type="dbt-validator-fixer",
    description="Fix DBT error",
    prompt="Fix missing source 'ekip' in d_contracts.sql:
    Error: source 'ekip' is not defined"
)
```

**Note**: Not used in current workflow (static validation only)

---

### 2. dependency-resolver
**Purpose**: Analyzes and resolves circular dependencies

**When to use**:
- Step 3 (dependency-graph-builder) detects circular dependency
- Pipeline blocked by dependency cycle

**How to call**:
```
Task(
    subagent_type="dependency-resolver",
    description="Resolve circular dependency",
    prompt="Resolve circular dependency between:
    adq_contracts.ktr → mas_contracts.kjb → adq_contracts.ktr"
)
```

**Returns**: Resolution strategy with break points

---

### 3. pentaho-cross-reference
**Purpose**: Searches Pentaho files for similar patterns

**When to use**:
- Unknown variable found
- Need to find usage patterns
- Looking for similar transformations

**How to call**:
```
Task(
    subagent_type="pentaho-cross-reference",
    description="Find similar patterns",
    prompt="Search for similar usage of variable ${CONTRACT_DATE}
    in other Pentaho files"
)
```

**Returns**: Suggestions with confidence scores

---

### 4. pentaho-deep-analyzer
**Purpose**: Deep-dives into Pentaho XML when surface analysis fails

**When to use**:
- pentaho-analyzer can't determine something
- Need specific XML node extraction
- Complex transformation logic

**How to call**:
```
Task(
    subagent_type="pentaho-deep-analyzer",
    description="Deep analyze Pentaho file",
    prompt="Extract the exact SQL from TableInput step in
    adq_contracts.ktr - analyzer couldn't parse it"
)
```

**Returns**: Extracted metadata that analyzer missed

---

### 5. sql-function-lookup
**Purpose**: Researches unknown SQL functions

**When to use**:
- sql-translator encounters unknown function
- Need to determine if function is:
  - Standard Oracle (needs translation)
  - Custom UDF (preserve as-is)
  - Truly unknown

**How to call**:
```
Task(
    subagent_type="sql-function-lookup",
    description="Research SQL function",
    prompt="Research function GETMAP() - is it Oracle standard
    or custom UDF?"
)
```

**Returns**: Classification with Snowflake equivalent or preservation instruction

---

## Integration Status

| Agent | Integrated? | Why Not? |
|-------|------------|----------|
| dbt-validator-fixer | ❌ No | We use static validation only (no dbt commands) |
| dependency-resolver | ❌ No | Pipeline stops on circular deps (manual fix) |
| pentaho-cross-reference | ❌ No | Not critical for main flow |
| pentaho-deep-analyzer | ❌ No | Current analyzer is sufficient |
| sql-function-lookup | ❌ No | We preserve unknown functions by default |

---

## Future Integration

These agents COULD be integrated into the main workflow:

### Automatic Calling:
```python
# In pentaho-analyzer:
if ambiguous_variable:
    call pentaho-cross-reference

# In sql-translator:
if unknown_function:
    call sql-function-lookup

# In dependency-graph-builder:
if circular_dependency:
    call dependency-resolver
```

### Current Approach:
- Main workflow handles 90% of cases
- Helper agents available for edge cases
- Manual intervention for complex issues

---

## Usage Example

When migration fails with unknown issue:

```bash
# 1. Main workflow fails
/migrate dim_contract
# ERROR: Unknown function CUSTOM_CALC()

# 2. Call helper agent
Task(
    subagent_type="sql-function-lookup",
    prompt="Research CUSTOM_CALC function"
)
# Returns: "Custom UDF, add to schema_registry.json"

# 3. Fix and retry
# Edit schema_registry.json
/migrate dim_contract
# SUCCESS
```

---

**Status**: Available but not integrated
**Recommendation**: Keep as emergency tools
**Future**: May integrate based on usage patterns