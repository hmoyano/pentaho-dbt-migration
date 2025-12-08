#!/bin/bash

# DBT PATH Setup Script
# This script adds the dbt.exe folder to your PATH so you can use 'dbt compile' instead of './dbt.exe compile'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DBT PATH Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get absolute path to dbt folder
DBT_FOLDER="$(cd "$(dirname "${BASH_SOURCE[0]}")/tfses-dbt-snowflake-3030" && pwd)"

echo "DBT folder: $DBT_FOLDER"
echo ""

# Check if dbt.exe exists
if [ ! -f "$DBT_FOLDER/dbt.exe" ]; then
    echo "❌ Error: dbt.exe not found in $DBT_FOLDER"
    exit 1
fi

echo "✓ Found dbt.exe"
echo ""

# Option 1: Add to .bashrc (permanent for Git Bash)
echo "Adding to ~/.bashrc..."

# Backup existing .bashrc
if [ -f ~/.bashrc ]; then
    cp ~/.bashrc ~/.bashrc.backup
    echo "✓ Backed up existing .bashrc to ~/.bashrc.backup"
fi

# Check if already added
if grep -q "# DBT PATH - 3030-pentaho-dbt" ~/.bashrc 2>/dev/null; then
    echo "⚠️  DBT PATH already configured in .bashrc"
else
    # Add to .bashrc
    cat >> ~/.bashrc << EOF

# DBT PATH - 3030-pentaho-dbt
export PATH="\$PATH:$DBT_FOLDER"
EOF
    echo "✓ Added DBT folder to PATH in ~/.bashrc"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To activate in current terminal:"
echo "  source ~/.bashrc"
echo ""
echo "Or close and reopen your terminal"
echo ""
echo "Test it:"
echo "  dbt --version"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
