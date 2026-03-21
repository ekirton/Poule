#!/usr/bin/env bash
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
FILE="${FILE#./}"
FILE="${FILE#$PWD/}"

if [[ "$FILE" == src/* ]] || [[ "$FILE" == test/* ]]; then
  python -m pytest test/ -x -q 2>&1 | tail -20
fi

exit 0
