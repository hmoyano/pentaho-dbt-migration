# .claude Directory Overview

This directory contains all Claude Code automation for the Pentaho-to-DBT migration system.

## Structure

```
.claude/
├── agents/                   # 13 AI-powered agents
├── commands/                 # 5 workflow commands
└── skills/                   # 5 deterministic skills
```

## Quick Start

```bash
# Configure paths
cat project.config.json

# Test locally first
/improve dim_your_dimension

# Full migration with git
/migrate dim_your_dimension

# Pause if dependencies missing
/pause-model-migration dim_your_dimension

# Resume or modify (smart detection)
/continue-migration dim_your_dimension
```

## Commands

| Command | Purpose | Git |
|---------|---------|-----|
| `/migrate` | Full pipeline | Yes |
| `/improve` | Local testing | No |
| `/pause-model-migration` | Pause incomplete | Yes |
| `/continue-migration` | Resume paused OR modify completed | Yes |
| `/migration-status` | Check progress | No |

## Skills

| Skill | Purpose |
|-------|---------|
| `pentaho-parser` | Parse Pentaho XML files |
| `oracle-snowflake-rules` | SQL translation rules |
| `dbt-best-practices` | Templates and conventions |
| `git-workflow` | Git sync, branching, commits |

## Configuration

All paths from `project.config.json` - no hardcoded paths.

See `agents/README.md` for agent catalog.
