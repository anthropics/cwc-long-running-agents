#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
# Halt every tool call while ./AGENT_STOP exists. `touch AGENT_STOP` to engage; `rm AGENT_STOP` to resume.
if [ -e "${AGENT_STOP_FILE:-./AGENT_STOP}" ]; then
  cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Kill switch engaged: AGENT_STOP file exists. Agent is halted. Remove the file to resume."}}
JSON
fi
