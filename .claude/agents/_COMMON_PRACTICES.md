# Agent Common Practices

**ALL AGENTS MUST FOLLOW THESE PRACTICES**

This document defines mandatory patterns that every agent in the Pentaho-to-DBT migration system must follow. These practices prevent common failures like infinite retry loops, large file handling errors, and write conflicts.

---

## 1. Large File Handling (MANDATORY)

### Problem
Metadata files (pentaho_raw.json, pentaho_analyzed.json, dependency_graph.json) can exceed 800 lines and 36K tokens, causing Read tool failures.

### Solution: Always Check Size First

**Pattern**:
```bash
# Step 1: Check file size
wc -l dimensions/<dimension>/metadata/pentaho_raw.json

# Step 2: If >500 lines, read in chunks
if lines > 500:
    # Read first chunk
    Read(file_path="...", offset=1, limit=500)

    # Read subsequent chunks
    Read(file_path="...", offset=501, limit=500)
    Read(file_path="...", offset=1001, limit=500)
    # ... until all content read
```

### Rules
- ✅ **ALWAYS** check file size before reading JSON metadata
- ✅ **ALWAYS** use offset/limit for files >500 lines
- ❌ **NEVER** retry a failed Read without changing strategy
- ❌ **NEVER** assume files are small

---

## 2. Retry Prevention (CIRCUIT BREAKER)

### Problem
Agents can enter infinite loops retrying the same failed operation.

### Solution: Track Attempts and Stop

**Pattern**:
```
Attempt 1: Try operation → Fails with error X
Attempt 2: Try different approach → Still fails with error X
STOP: Report "Tried 2 approaches, both failed. Need help."
```

### Rules
- ✅ **Track** how many times you've tried the same operation
- ✅ **Change strategy** after first failure (e.g., chunked reading)
- ✅ **Stop after 2 failed attempts** with same approach
- ✅ **Report what you tried** and what errors occurred
- ❌ **NEVER** retry the exact same command that just failed
- ❌ **NEVER** loop more than 3 times on similar operations

### Self-Monitoring Checklist

Ask yourself before each tool call:
- Have I called this same tool in the last 3 actions?
- Did it fail last time with the same error?
- Am I changing my approach or just retrying?

If you detect a pattern → **STOP** and report:
```
❌ I'm stuck in a retry loop.

Attempted: <operation>
Tried: <approach 1>, <approach 2>
Errors: <error messages>

I need a different strategy or human intervention.
```

---

## 3. Write-Safe File Operations

### Problem
Using Write tool on existing files without reading them first causes "File has been unexpectedly modified" errors.

### Solution: Check Existence, Read First

**Pattern**:
```bash
# Step 1: Check if file exists
ls -la dimensions/<dimension>/metadata/

# Step 2a: If file DOES NOT exist
if not exists:
    Write(file_path="...", content="...")

# Step 2b: If file EXISTS
if exists:
    # Read it first (even just first 50 lines)
    Read(file_path="...", offset=1, limit=50)

    # Then either:
    # - Use Edit to update specific sections, OR
    # - Use Write to replace entire file (now safe)
    Write(file_path="...", content="...")
```

### Rules
- ✅ **Check existence** before writing (ls -la or Glob)
- ✅ **Read first** if file exists
- ✅ **Use Edit** for updating portions of files
- ✅ **Use Write** for new files or full replacements (after reading)
- ❌ **NEVER** use Write on existing file without reading first

---

## 4. Error Classification (STRICT CRITERIA)

### CRITICAL: Blocking, Requires Human
**Use when**:
- Variable not found in schema_registry.json
- Circular dependency with no auto-fix possible
- Missing required configuration file
- Cannot parse source files (corrupt/missing)
- Custom function not in registry and not standard Oracle
- Genuinely ambiguous data that needs business decision

**Required fields**:
```json
{
  "severity": "CRITICAL",
  "file": "filename.ktr",
  "issue": "Clear description of problem",
  "requires_human": true,
  "blocking": true,
  "auto_resolved": false,
  "action_needed": "Specific action user must take",
  "context": "Additional helpful information"
}
```

### WARNING: Non-Blocking, Review Recommended
**Use when**:
- Missing optional data (e.g., row counts in TABLE_COUNT.csv)
- High complexity transformation detected
- Auto-resolution with medium confidence (0.5-0.8)
- Best practice violation but not breaking
- Performance concern

**Required fields**:
```json
{
  "severity": "WARNING",
  "file": "filename.ktr",
  "issue": "Description of concern",
  "requires_human": false,
  "blocking": false,
  "auto_resolved": false,
  "recommendation": "Suggested action"
}
```

### INFO: Successfully Handled
**Use when**:
- Auto-fixed an ambiguity (confidence >0.8)
- Applied best practice automatically
- Detected and preserved custom function
- Informational recommendations

**Required fields**:
```json
{
  "severity": "INFO",
  "file": "filename.ktr",
  "issue": "What was ambiguous or needed handling",
  "resolution": "How it was resolved",
  "auto_resolved": true,
  "requires_human": false,
  "blocking": false,
  "resolved_by": "agent-name"
}
```

### Decision Tree

```
Is this issue?
├─ Blocks next step in pipeline?
│  ├─ YES → Can we auto-fix it?
│  │  ├─ YES (conf >0.8) → INFO (document the fix)
│  │  ├─ MAYBE (conf 0.5-0.8) → WARNING (use fix, but flag)
│  │  └─ NO → CRITICAL (escalate to human)
│  └─ NO → Does it affect quality?
│     ├─ YES → WARNING
│     └─ NO → INFO (or don't report)
```

---

## 5. Self-Monitoring (Prevent Infinite Loops)

### Mental Checklist

Before each tool call, check:

1. **Am I repeating myself?**
   - Same tool called 3+ times?
   - Same parameters used?
   - Same error received?

   → If YES: **STOP and change approach**

2. **Is this the same error again?**
   - Error message identical to previous?
   - Root cause the same?

   → If YES: **STOP, don't retry**

3. **Have I been working on this issue for >5 tool calls?**
   - Spent many attempts on one problem?
   - No progress made?

   → If YES: **STOP and escalate**

### When to Stop and Report

**Stop immediately if**:
- Same command failed 2 times
- Called same tool 3 times in a row with similar params
- Spent >10 tool calls on one issue
- Error is unclear and you're guessing

**Report format**:
```
❌ I need help - I'm stuck

Issue: <what you're trying to do>
Attempts:
  1. <approach 1> → <result/error>
  2. <approach 2> → <result/error>

I've tried different approaches but cannot resolve this.
Recommendation: <what needs to happen>
```

---

## 6. Output Validation (ALWAYS)

### Why
Ensure your output is valid before the next agent consumes it. Prevents garbage-in-garbage-out.

### Pattern

**After writing your output file, validate it**:

```bash
# Step 1: Read what you just wrote
Read(file_path="dimensions/<dimension>/metadata/<your_output>.json", offset=1, limit=50)

# Step 2: Validate structure
- Is it valid JSON?
- Do required top-level keys exist?
- Are there null/undefined in critical fields?

# Step 3: Validate semantics (agent-specific)
Examples:
- pentaho_analyzed.json: Must have "files" array with length >0
- dependency_graph.json: Must have "execution_order" array
- translation_metadata.json: Must have "translations" array matching input count

# Step 4: If validation fails
if not valid:
    Add CRITICAL issue:
    {
      "severity": "CRITICAL",
      "issue": "Output validation failed: <specific reason>",
      "blocking": true,
      "requires_human": true,
      "action_needed": "Review agent logs and rerun"
    }

    Return error summary:
    "❌ Output validation failed: <reason>"

# Step 5: If validation passes
else:
    Include in summary:
    "✅ Output validated successfully"
```

### Agent-Specific Validation

**pentaho-analyzer**:
- `files` array must match number of input files
- Every file must have `operation_analysis` object
- Every variable must be resolved or flagged
- `issues` array must have proper structure

**dependency-graph-builder**:
- `execution_order` must be complete topological sort
- `nodes` count must match input files count
- No orphan nodes (all connected)

**sql-translator**:
- Number of translated files matches input count
- Every translation has confidence score
- Custom functions list is populated

**dbt-model-generator**:
- Model count matches expected output
- All models have materialization config
- Schema YAML files exist

**quality-validator**:
- Validation ran successfully
- Overall status is set (PASSED/FAILED/WARNINGS)
- Error count is accurate

---

## 7. Bash Command Safety

### Timeout Rules

**Always set appropriate timeout**:
```bash
# Quick commands (<30 sec expected)
Bash(command="ls -la", timeout=30000)  # 30 seconds

# Medium commands (1-2 min expected)
Bash(command="dbt parse", timeout=120000)  # 2 minutes

# Long commands (5-10 min expected)
Bash(command="dbt run --select +dim_contracts", timeout=600000)  # 10 minutes

# Default if unsure
Bash(command="...", timeout=120000)  # 2 minutes
```

### Error Handling

**Never assume success**:
```bash
# Check exit code and output
result = Bash(command="dbt parse")

if "error" in result.stderr.lower():
    # Handle error
    add_issue(severity="CRITICAL", issue="dbt parse failed")
else:
    # Success
    continue
```

### Rules
- ✅ **Always set timeout** (don't use default)
- ✅ **Check stderr** for errors
- ✅ **Parse output** to verify success
- ✅ **Handle failures** gracefully
- ❌ **NEVER** assume command succeeded
- ❌ **NEVER** use timeout >600000ms (10 min)

---

## 8. JSON Parsing Safety

### Handle Malformed JSON

```python
# Read JSON file
content = Read("file.json")

# Try to parse
try:
    data = json.parse(content)
except JSONDecodeError as e:
    # Report error
    add_issue(
        severity="CRITICAL",
        issue=f"Cannot parse JSON: {e}",
        action_needed="Check file for syntax errors"
    )
    return error
```

### Validate Expected Structure

```python
# Check required keys
required_keys = ["dimension", "files", "summary"]

for key in required_keys:
    if key not in data:
        add_issue(
            severity="CRITICAL",
            issue=f"Missing required key: {key}",
            action_needed="Regenerate the file"
        )
```

### Rules
- ✅ **Always validate** JSON structure after reading
- ✅ **Check for required keys** before accessing
- ✅ **Handle missing data** gracefully
- ❌ **NEVER** assume JSON is well-formed

---

## 9. Tool Call Efficiency

### Grep vs Read

**Use Grep when**:
- Searching for specific pattern across many files
- Need line numbers or context
- File contents are large

**Use Read when**:
- Need to parse structured data (JSON, CSV)
- Need entire file content
- File is small (<500 lines)

### Parallel vs Sequential

**Use parallel tool calls when**:
- Operations are independent
- Results don't depend on each other
- Example: Reading multiple small config files

**Use sequential when**:
- Later operation depends on earlier result
- File must be read before writing
- Example: Read → Edit → Validate

### Rules
- ✅ **Use specialized tools** (Grep for search, Read for content)
- ✅ **Parallelize independent operations**
- ✅ **Minimize tool calls** (batch when possible)
- ❌ **NEVER** use Bash for file operations that have dedicated tools

---

## Summary: Quick Reference

| Situation | Required Action |
|-----------|----------------|
| Reading large file | Check `wc -l` first, use chunking if >500 lines |
| Operation fails once | Try different approach |
| Operation fails twice | STOP, report issue |
| Writing to file | Check existence, read first if exists |
| Unknown variable | Try auto-fix (cross-reference), then escalate if needed |
| Tool called 3x in row | STOP, self-monitor triggered |
| Created output file | Read it back, validate structure |
| Bash command | Set timeout, check stderr |
| Error severity unclear | Use decision tree in section 4 |

---

## Enforcement

**These are not suggestions - they are requirements.**

- Every agent is expected to follow these practices
- Violations lead to pipeline failures
- Self-monitoring is mandatory
- Output validation is mandatory

**When in doubt**:
1. Stop and think
2. Check this document
3. Ask for help vs. guessing

**Remember**: It's better to escalate early than to propagate bad data through the pipeline.
