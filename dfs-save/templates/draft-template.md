---
title: "{Concise, Searchable Title}"
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
type: source-notes
tags:
  - lang/{lang}
  - topic/{topic}
  - category/troubleshooting
  - status/draft
status: draft
audience: both
source: "Session Discovery ({Project Name})"
---

# {Title}

## 1. 现象与成因分析 (Symptom & Root Cause)
{Describe what broke, the misleading symptoms, and why it occurred.}

## 2. 终极解决方案 (Permanent Solution & Code)
{Provide the clean, reproducible code fix.}

## 3. 防御性工程规范 (Defensive Rule)
{State the universal rule to prevent recurrence in other projects.}

## 4. 确定性评估信号 (Deterministic Evaluation Signals)
- **Tool Results Count**: {Number of tool executions / verified outputs, e.g. 3 terminal commands, 2 test runs}
- **Error Receipts**: {Exact exit code, stderr snippet, or compiler diagnostic captured before fix}
- **Environment State Check**: {OS, runtime/toolchain versions, working directory, git branch/status}
