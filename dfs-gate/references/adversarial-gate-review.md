# Commissioning an Adversarial Evasion Pass Over a New Gate

A mutation self-proof is written by the same hand as the matcher, so it inherits that hand's
assumptions: a matcher that reads one quote style gets mutated with that same quote style, the run
passes, and a one-character change walks straight through the criterion. A gate is worth trusting
only after someone with no stake in it has tried to break it. This is the brief to hand that
reviewer, and what to do with what comes back.

## When to run it
- The gate introduces a **matcher** — a pattern, a regex, a token predicate — rather than an exact
  structural comparison. Matchers have syntactic blind spots; structural checks have semantic ones.
- The gate guards a boundary whose erosion is silent: a layer's permitted imports, a banned API, a
  required call shape.
- You are about to present the gate as evidence that a defect class is closed.

Skip it for gates that are pure identity comparisons (byte-equality, exact set equality); there is
nothing in them to paraphrase around.

## The brief
The reviewer shares none of your context, so the message must carry all of it:
1. An absolute path to a scratch tree, and the instruction to mutate **copies** — never the tracked
   files — and to report the tree clean at the end.
2. The gate's rules, one line each, in plain language: what it forbids or requires, and on which
   files.
3. The exact command that runs the gate, and its exit-code contract.
4. **The mechanisms the gate itself leans on**, named: the comment stripper, the value extractor,
   the import parser. Naming them points the reviewer at the places worth digging.
5. The attack classes to probe, at minimum:
   - **Same semantics, renamed shape** — alias the banned name into a local, reach it by subscript,
     through optional chaining, via a wrapper or an indirection.
   - **Orthographic variants** — every quote style; with and without whitespace; template vs
     concatenation; one line vs many; one statement vs two on a line.
   - **The unparsable case** — a value the extractor cannot resolve (a variable, a shorthand
     property, a computed key). A permissive default here is the hole, not a tolerance.
   - **Forms the parser was not written for** — side-effect-only imports, re-exports, dynamic
     import, namespace/default bindings, generator declarations.
   - **For any guard whose subject is "what this module exports":** re-add the forbidden names as a
     single `export { a as b, … }` block, then again on an **indented** line, then as `export * from`.
     The exported name of `a as b` is `b`, and nothing inside the brace block follows the `export`
     keyword — so a line-anchored `^export` extractor sees none of it and the full forbidden surface
     comes back green. Also re-add the alias from a *different* specifier to test whether the
     companion "every export is imported somewhere" rule scopes its imports per statement.
   - **Lexical traps** — a quote or a `/*` inside a regex literal, `//` inside a URL string, a
     template literal spanning lines.
   - **Negative controls** — legitimate code that must stay green. Without these the report is a
     list of true positives with no false-positive signal.

## The report contract
Findings **worst-first**; each with (a) the exact snippet, (b) the file it belongs in, (c) the gate's
actual behaviour — the command and its real exit code, (d) why it is a real hole rather than a
non-issue, (e) a one-line fix or an explicit `acceptable, reason: ...` verdict.
**Plus an explicit list of the attacks that WERE caught.** A report of misses alone cannot be told
apart from a reviewer that never ran the gate.

## Disposal — the report is a specification, not a bug list
- Every **confirmed evasion becomes a parametrized regression case** in the gate's suite, asserting
  the named criterion fires — not merely that the tool exits non-zero, since a later change that
  makes the tool crash would then read as a fix.
- Where the **matcher** is at fault (a quote style, an unparsable value), **rewrite the criterion**;
  do not special-case the one input. A patched matcher leaks the same class through the next variant.
- Where the **target code** is at fault, fix the code and leave the gate narrow.
- Unparsable input gets **fail-closed** handling behind its own named violation
  (`unverifiable-<thing>`), never a permissive default — the default is exactly the value that
  passes.
- **Re-run the real-file mutation harness after the rewrite**, and again after every later criterion
  change: a criterion change invalidates every proof taken before it.
- Record the **surviving limit** in the gate's own rationale comment. A block list cannot be
  exhaustive; saying so is what stops the next author from treating a green run as proof.

## Special case: the gate itself was refactored during the task

Implementers routinely discover mid-task that the clause they were told to register is *not
reachable* for the new member, and refactor the gate's internals to make it so — typically by
extracting a helper out of another criterion's loop, or adding a second pass over a membership list.
That is gate logic, not the feature under test, and it must be proven **behaviour-preserving for
every pre-existing member** before the task is signed off. A review that only checks the new member
cannot see a narrowing that silently drops an old one.

The proof is a differential run, not an argument:
1. Materialise **both** versions of the gate — the parent commit's file and the reviewed one —
   importable side by side from scratch copies.
2. Build **one** identical fixture tree containing every module from every registry, each with a
   placeholder that is clean by construction.
3. For each pre-existing member of each registry, inject the defect shape the clause forbids and run
   **both** gates. Compare `(path, line, rule)` triples as sets, not counts — a count match can hide
   a swapped site. The expected result is *identical* triples, and the rule string must survive
   verbatim (a pass that renames the criterion breaks downstream `-k` filters silently).
4. If a member sits in **two** registries, confirm the new pass skips it (`if name in OTHER: continue`)
   so the clause is not reported twice under two different rule strings — dedupe by set membership
   will not save you, because the strings differ.
5. Widen the injected shapes past the obvious: multiple declarations, function-scoped and
   method-scoped ones, declaration inside a top-level block or `for` init, a stray leading brace,
   comment and string decoys, template-literal braces, an unbalanced open. Equivalence on one shape
   is equivalence on none.
6. Filter the new member's own entries out of the comparison and require the **remaining violation
   list to be order-identical**, not merely equal as a set: downstream consumers eyeball the first
   few lines, and a reordered report reads as a changed gate.

A refactor that passes this is safe to keep even though it exceeded the plan's declared interface;
say so explicitly in the review, including the fact that it was **necessary** to reach the plan's
own success criterion. A refactor that fails it is a narrowing, and the plan's RED count is the
evidence — not an opinion.

## Why it pays
One reviewer, one scratch tree, a handful of one-line mutations — cheap against the cost of a gate
that is green and does not work. The finding it reliably produces is in the matcher you were most
confident about.
