---
description: Run the complete Pentaho to DBT migration pipeline for a dimension
---

# Pentaho to DBT Migration Orchestrator

You are orchestrating the complete migration of a Pentaho entity (dimension or fact) to DBT models.

## User Request

The user wants to migrate: **{{ DIMENSION_NAME }}**

(If name not provided, ask the user which entity to migrate)

---

## Step 0: Configuration & Git Setup

### 0.1 Read Configuration

**First**: Read `project.config.json` to get all paths:

```bash
cat project.config.json
```

Extract these values:
- `dbt_repository` = `paths.dbt_repository`
- `pentaho_sources` = `paths.pentaho_sources`
- `dimensions_output` = `paths.dimensions_output`
- `facts_output` = `paths.facts_output`
- `protected_branches` = `git.protected_branches`
- `branch_prefix` = `git.branch_prefix`

### 0.2 Determine Entity Type and Path

```python
entity_name = "{{ DIMENSION_NAME }}"

if entity_name.startswith("d_") or entity_name.startswith("dim_"):
    entity_type = "dimension"
    entity_path = f"{dimensions_output}/{entity_name}"
elif entity_name.startswith("f_") or entity_name.startswith("fact_"):
    entity_type = "fact"
    entity_path = f"{facts_output}/{entity_name}"
else:
    # Ask user to clarify
    entity_type = ask_user("Is this a dimension or fact?")
    entity_path = f"{dimensions_output if entity_type == 'dimension' else facts_output}/{entity_name}"
```

### 0.3 Detect Git Platform

```bash
cd {dbt_repository}
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

if echo "$REMOTE_URL" | grep -q "github.com"; then
    GIT_PLATFORM="github"
    CLI_TOOL="gh"
elif echo "$REMOTE_URL" | grep -q "gitlab"; then
    GIT_PLATFORM="gitlab"
    CLI_TOOL="glab"
fi
cd ..
```

### 0.4 Git Sync & Create Feature Branch

**Use `git-workflow` skill - operation: `sync-and-branch`**

Read and execute the script from `.claude/skills/git-workflow/SKILL.md` (section 1).

Parameters:
- `{dbt_repository}` - from config
- `{branch_prefix}` - from config (default: `migrate/`)
- `{entity_name}` - {{ DIMENSION_NAME }}

This will:
1. Fetch latest from remote
2. Find base branch (develop > main > master)
3. Pull latest base branch
4. Create feature branch or checkout existing from remote

### 0.5 Repository Analysis

```
Task(
    subagent_type="repo-analyzer",
    prompt="Analyze DBT repository at {dbt_repository}/ and extract context.
    Write to: .claude/skills/dbt-best-practices/reference/repo_context/"
)
```

Display:
```
GIT SETUP COMPLETE
Platform: {GIT_PLATFORM}
Repository: {dbt_repository}/
Branch: {BRANCH_NAME}
Entity: {{ DIMENSION_NAME }} ({entity_type})
```

---

## Steps 1-6: Migration Pipeline

**Execute the shared pipeline from `.claude/commands/_pipeline_steps.md`**

Parameters:
- `entity_name`: {{ DIMENSION_NAME }}
- `entity_type`: {entity_type}
- `entity_path`: {entity_path}
- `dbt_repository`: {dbt_repository}
- `enable_git_ops`: true

**Pipeline Steps:**
1. Parse Pentaho Files (pentaho-parser)
2. Analyze Transformations (pentaho-analyzer) + Gate
3. Build Dependency Graph (dependency-graph-builder) + Gate
4. Translate SQL (sql-translator)
5. Generate DBT Models (dbt-model-generator)
6. Validate Quality (quality-validator)

**Each step includes Safe Mode confirmation** - user reviews before proceeding.

---

## Step 7: Generate Reference Documentation

**NEW**: Auto-generate docs for future `/continue-migration` use.

```
Task(
    subagent_type="migration-docs-generator",
    prompt="""
    Generate migration documentation:
    - entity_name: {{ DIMENSION_NAME }}
    - entity_type: {entity_type}

    Read metadata from: {entity_path}/metadata/

    Generate:
    - {entity_path}/REFERENCE.md
    - {entity_path}/CHANGELOG.md
    """
)
```

---

## Step 8: Git Push & PR

### 8.1 Commit

```bash
cd {dbt_repository}
git add models/
git commit -m "feat({entity_type}): Add {{ DIMENSION_NAME }} DBT models

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
cd ..
```

### 8.2 Push

```bash
cd {dbt_repository}
git push -u origin {BRANCH_NAME}
cd ..
```

### 8.3 Create PR (Optional)

Ask user if they want to create PR/MR now.

---

## Final Report

```
MIGRATION COMPLETE: {{ DIMENSION_NAME }}

Step 1-6: Pipeline - COMPLETED
Step 7: Documentation - COMPLETED
Step 8: Git Push - COMPLETED

ARTIFACTS:
- Metadata: {entity_path}/metadata/
- Reference: {entity_path}/REFERENCE.md
- DBT models: {dbt_repository}/models/

NEXT STEPS:
1. Review Pull Request
2. Deploy UDFs (if any)
3. Merge after approval

To modify later: /continue-migration {{ DIMENSION_NAME }}
```

---

## Error Handling

If any step fails:
1. Stop pipeline
2. Report error with remediation
3. Save state (previous steps preserved)
4. Re-run `/migrate {{ DIMENSION_NAME }}` to resume

---

## Key Points

- **All paths from `project.config.json`** - no hardcoded paths
- **Safe Mode** - user confirms at each checkpoint
- **Git Safety** - never commits to protected branches
- **Auto-docs** - generates REFERENCE.md and CHANGELOG.md
- **Resumable** - state saved after each step
