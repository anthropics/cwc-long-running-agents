#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
#
# Denies any Write/Edit to the results file unless the agent has opened at least
# one evidence file (screenshot/console log) since the gate last fired.
#
# This is a teaching example, not a security boundary. Known gaps a real
# enforcement layer would close: this only hooks Write/Edit (Bash sed/jq can
# rewrite the file unchecked); the path match is basename-only and
# case-sensitive; and any evidence read unlocks any result row, not the
# corresponding one. Tighten in your project as needed.
log="${VERIFY_READ_LOG:-./.claude/.evidence-reads}"
results="${RESULTS_FILE:-test-results.json}"

input=$(cat)
target=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null)

# Only guard the results file (anchor on path separator so e.g. vitest-results.json doesn't match)
case "$target" in "$results"|*/"$results") ;; *) exit 0 ;; esac

if [ ! -s "$log" ]; then
  cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Cannot modify the results file: no screenshot or console-log evidence has been Read this session. Open the evidence file with the Read tool first, then retry."}}
JSON
  exit 0
fi
# consume the evidence so the next change needs fresh proof
: > "$log"
