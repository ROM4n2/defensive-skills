# Subagent Dispatch Routing, Relocation Briefs & Field Pitfalls (`references/brief-and-pitfalls-playbook.md`)

Load this reference when choosing the execution surface (in-thread vs subagent vs CLI worker), constructing briefs for file splits/relocations, or triaging subagent reports and worktree hazards.

---

## 1. Dual-Layer Dispatch Routing & Context Sizing (MUST)

Route work by **task shape**, never by habit:

| Task Shape | Execution Surface | Why |
|---|---|---|
| Single-turn research, config check, or <=3 file reads | **In-thread (Orchestrator)** | Zero cold-start overhead; immediate synthesis. |
| Independent parallel read/audit streams or isolated single-task TDD | **Fresh Subagent (`delegate_task`)** | Ephemeral clean context (`skip_memory=True`); prevents context window pollution. |
| Multi-step repo coding, LSP navigation, or tasks needing interactive takeover | **Persistent CLI Coding Agent / Isolated Worktree** | Full repo toolchain, incremental session state, and branch isolation. |

- **Never Resurrect a Heavy Session for a Small Follow-Up (MUST)**: Resuming a multi-turn 50K-token worker session just to fix a 5-line review finding risks hitting the 300s subprocess timeout and suffers severe context-degradation (>60% window). Always dispatch a **fresh small-context worker** carrying only the exact `file:line` delta and failing test receipt.
- **Single-Winner Lock & Cooperative Cancellation**: When running parallel exploration or racing workers, enforce a single-winner settlement lock and wrap external subprocess/RPC calls in cooperative cancellation guards so losing/cancelled branches do not leave orphan processes running.

---

## 2. Deep Brief Construction Rules (Relocation, Blast Radius & Hoisting)

1. **Derive the Gate List from the BLAST RADIUS, Not the Touched Files**:
   - When a change alters a symbol's signature, return shape, transport, or shared fixture interface, grep the *entire* test tree for every caller and hand-rolled mock of that symbol, and put all matching test files in the builder's, reviewer's, and orchestrator's gate list.
2. **Impose the Frozen Surface Rule on Relocation Briefs**:
   - When moving or splitting code covering stabilized/sensitive contracts, instruct the child: *change zero assertion text, report suspected defects instead of fixing them, and prove byte-level or Triple-Conservation identity against the pre-move source*.
3. **Require a Residual Inventory Handback in Multi-Batch Splits**:
   - After commit 1 of a multi-batch split, line numbers drift. Require each child to return an empirical inventory of what remains in the source file (section headers, line ranges, symbol/test counts) and instruct subsequent children to locate by **content/symbol name**, never by stale line numbers.
4. **Hoist Forced Copies Before the Next Batch Lands**:
   - If file-ownership boundaries forced a temporary helper/fixture copy in batch 1, hoist it into the shared layer before batch 2 dispatches (verifying empirically that framework registration like `autouse` scope still holds).
5. **Re-Verify Prior Batches' Fixes Survived Restructuring**:
   - After a split or move, grep the parent tree for the distinct text/identity of earlier batches' fixes and confirm they still sit inside the owning test.
6. **Phrase Premise-Dependent Instructions as Intent**:
   - When a brief says "do X because Y holds", require the child to verify Y in the code first and report a contradiction rather than blindly obeying X when Y is false.

---

## 3. Field Pitfalls Catalog (Worktrees, Contention & Turn Hygiene)

- **Parent Workspace Files Misrouting Subagent Worktrees (`GOWORK=off`)**: Inside `.worktrees/subagent-<id>`, a parent `go.work`, `pnpm-workspace.yaml`, or Cargo workspace can silently compile/test the *parent* directory instead of the worktree. Mandate `GOWORK=off` (or equivalent isolated root flag) on every command.
- **Worktree Base Commit Drift**: A harness subagent worktree may branch from `master` HEAD rather than the orchestrator's feature branch. Always check `git log -n 1` on the child branch and cherry-pick/rebase onto the target feature branch before merging.
- **Inner-First & Exact-ID Worktree Cleanup**: Parallel dispatches can nest worktrees (`.worktrees/A/.worktrees/B`). Remove inner before outer, and prune by exact `<subagent-id>` — **never** run `rm -rf .worktrees/*` while sibling subagents are alive. Deduplicate `.worktrees/` entries in `.gitignore` before committing.
- **Never Emit an Empty Turn on Dispatch or Re-Entry**: Always output a one-line status when dispatching, and execute the full closing cascade (merge -> serial test -> ledger update -> worktree prune -> next task) in the same turn upon a Reviewer `PASS`.
- **Child Self-Report & Write-Warning Invalidation**: If the harness logs a failed file write during a child run, treat all numbers reported from that file as unverified and re-derive them in the parent tree.
