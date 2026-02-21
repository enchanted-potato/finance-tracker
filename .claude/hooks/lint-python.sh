#!/bin/bash
# Hook: runs ruff format + mypy on .py files after Edit/Write

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only process Python files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0

# Make path relative for cleaner output
REL_PATH="${FILE_PATH#$CLAUDE_PROJECT_DIR/}"

# Run ruff format
echo "--- ruff format ---"
uv run ruff format "$FILE_PATH" 2>&1

# Run ruff check with auto-fix (import sorting, etc.)
echo "--- ruff check ---"
uv run ruff check --fix "$FILE_PATH" 2>&1

# Run mypy
echo "--- mypy ---"
uv run mypy "$FILE_PATH" 2>&1

exit 0
