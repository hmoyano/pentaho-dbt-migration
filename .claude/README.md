# .claude Directory Overview

This directory contains all Claude Code automation for the Pentaho-to-DBT migration system.

## Structure

```
.claude/
├── agents/                   # 13 AI-powered agents
├── commands/                 # 6 workflow commands
└── skills/                   # 3 deterministic skills
```

## Quick Start

```bash
# Configure paths
cat project.config.json

# Test locally first
/improve dim_your_dimension

# Full migration with git
/migrate dim_your_dimension

# Modify existing
/continue-migration dim_your_dimension
```

## Commands

| Command | Purpose | Git |
|---------|---------|-----|
| `/migrate` | Full pipeline | Yes |
| `/improve` | Local testing | No |
| `/continue-migration` | Modify existing | Yes |
| `/migration-status` | Check progress | No |

## Configuration

All paths from `project.config.json` - no hardcoded paths.

See `agents/README.md` for agent catalog.
