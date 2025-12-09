---
name: git-workflow
description: Git workflow operations for DBT migrations. Use when starting a migration (/migrate), pausing (/pause-model-migration), or restarting (/restart-model-migration). Handles fetch, sync, branch creation, and safe commits.
---

# Git Workflow Skill

Centralized Git operations for the Pentaho-to-DBT migration system.

## Operations

### 1. sync-and-branch (for /migrate)

Use when starting a new migration. Creates feature branch from latest base.

```bash
cd {dbt_repository}

# Fetch latest
git fetch origin

# Find base branch (develop > main > master)
BASE_BRANCH=""
for branch in develop main master; do
    if git rev-parse --verify origin/$branch >/dev/null 2>&1; then
        BASE_BRANCH=$branch
        break
    fi
done

[ -z "$BASE_BRANCH" ] && echo "ERROR: No base branch found" && exit 1

# Create or checkout feature branch
BRANCH_NAME="{branch_prefix}{entity_name}"

if git rev-parse --verify origin/$BRANCH_NAME >/dev/null 2>&1; then
    # Branch exists on remote - checkout and pull
    git checkout $BRANCH_NAME 2>/dev/null || git checkout -b $BRANCH_NAME origin/$BRANCH_NAME
    git pull origin $BRANCH_NAME
else
    # New branch - create from base
    git checkout $BASE_BRANCH
    git pull origin $BASE_BRANCH
    git checkout -b $BRANCH_NAME
fi

echo "Branch: $BRANCH_NAME (from $BASE_BRANCH)"
cd ..
```

**Parameters:**
- `{dbt_repository}` - Path from project.config.json
- `{branch_prefix}` - From project.config.json (default: `migrate/`)
- `{entity_name}` - Dimension or fact name

---

### 2. sync-current (for /pause and /restart)

Use when continuing work on existing branch. Syncs current branch with remote.

```bash
cd {dbt_repository}

# Fetch and sync current branch
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)

if git rev-parse --verify origin/$CURRENT_BRANCH >/dev/null 2>&1; then
    git pull origin $CURRENT_BRANCH
fi

# Warn about uncommitted changes
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "WARNING: Uncommitted changes exist"
    git status --short
fi

cd ..
```

---

### 3. commit-and-push

Use after completing a migration step. Commits and pushes changes.

```bash
cd {dbt_repository}

BRANCH_NAME=$(git branch --show-current)

# Stage and commit
git add models/
git add -A
git status

git commit -m "{commit_message}"
git push origin $BRANCH_NAME

cd ..
```

**Parameters:**
- `{commit_message}` - Descriptive commit message

---

### 4. check-protected

Use before any destructive operation. Verifies not on protected branch.

```bash
cd {dbt_repository}

CURRENT=$(git branch --show-current)
PROTECTED="develop main master"

for branch in $PROTECTED; do
    if [ "$CURRENT" = "$branch" ]; then
        echo "ERROR: On protected branch $branch"
        exit 1
    fi
done

echo "OK: On branch $CURRENT"
cd ..
```

---

## Quick Reference

| Command | Operation | When |
|---------|-----------|------|
| `/migrate` | sync-and-branch | Starting new migration |
| `/pause-model-migration` | sync-current | Pausing work |
| `/restart-model-migration` | sync-current | Resuming work |
| After any step | commit-and-push | Saving progress |
| Before destructive ops | check-protected | Safety check |
