---
description: Run test suite
allowed-tools: Bash
argument-hint: "[test-path]"
---

Run tests:

!`source .venv/bin/activate && pytest $ARGUMENTS -xvs --cov=src --cov-report=term-missing`

Analyze failures and suggest fixes.
