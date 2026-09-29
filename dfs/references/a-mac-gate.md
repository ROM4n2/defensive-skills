# The A-MAC admission gate — the quality bar for a `99-Inbox/` draft

Exactly one gate stands between a session insight and a draft landing in `99-Inbox/`. This file is
the single source of truth for what that gate requires, so `dfs-save` and `dfs-debug` cannot drift
apart on it.

**The acronym is never expanded.** It is used as-is across this suite and the knowledge base it
serves, but no file — including the knowledge base's own `01-Rules/INGESTION-WORKFLOW.md` — writes
it out. This file therefore defines the gate **operationally**. If you learn the expansion, record
it here: this is the one place to change.

## What the gate rejects

Trivial one-off fixes — the canonical example being `fixed typo in line 12`. A draft earns admission
only when what it records would save a reader the same investigation.

## The canonical draft schema (4 fields)

| Field | What it holds |
|---|---|
| **Symptom** | The misleading observable — what you saw first, and why it pointed the wrong way. |
| **Root Cause** | The actual mechanism, at the depth where a reader can act on it. |
| **Solution** | The fix, with the code that carries it. |
| **Defensive Rule** | The transferable rule that stops this recurring in another project. |

Those four are the floor, not a ceiling. A skill holding a physical execution receipt appends it as a
fifth field — `dfs-debug` does, because its gate runs on a step whose whole product is a
reproduction.

## Who enforces it

- `dfs-save` — the harvest path; states the gate among its ingestion invariants.
- `dfs-debug` — the self-healing path; composes a draft when a root cause proved non-intuitive.
- The `save_inbox_draft` tool writes the draft, but the gate is **normative, not server-enforced**:
  nothing evaluates the four fields on write, so the agent is the enforcement.

The knowledge base's own statement of this contract lives at
`{vault_root}/01-Rules/INGESTION-WORKFLOW.md`, which also fixes the single-channel rule: one topic,
one channel, once.
