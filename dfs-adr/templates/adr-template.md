---
title: "ADR-{NNNN}: {Decision Title}"
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
type: project
tags:
  - category/project
  - topic/adr
  - topic/architecture
status: stable
audience: both
---

# ADR-{NNNN}: {Decision Title}

## 1. Context and Problem Statement
{Describe the engineering context, forces at play, and why a decision is necessary.}

## 2. Decision Drivers
- {Driver 1: e.g. Maximize read throughput under concurrent workers}
- {Driver 2: e.g. Zero external daemon dependencies for embedded desktop use}
- {Driver 3: e.g. Prevent database write lock starvation}

## 3. Considered Options
- **Option 1**: {Title & Brief Description}
  - [NOTE] Pros: {Key advantages}
  - [NOTE] Cons: {Key drawbacks}
- **Option 2**: {Title & Brief Description}
  - [NOTE] Pros: {Key advantages}
  - [NOTE] Cons: {Key drawbacks}

## 4. Decision Outcome
Chosen option: **Option {X}**, because {First-Principles rationale justifying the trade-off}.

## 5. Consequences and Trade-offs
- [OK] **Positive**: {What becomes easier or faster}
- [NOTE] **Negative**: {What becomes more complex, and how we mitigate it}
- [MUST] **Compliance Guardrail**: {Code rules or static tests enforcing this decision}
