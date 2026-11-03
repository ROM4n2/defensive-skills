# Harness field mapping

This repository contains 28 skills. Frontmatter behavior is harness-specific; do not infer it from a key's presence alone.

## 1. Portable core

| Key | Meaning | Runtime note |
|---|---|---|
| `name` | Skill identifier; must match the directory name | Read by skill loaders |
| `description` | Capability and trigger summary | Used for model selection |
| `license` | License declaration | Informational |
| `metadata.version` | Skill version | Informational |
| `metadata.platforms` | Declared platforms | Informational; not a runtime filter |
| `metadata.hermes.tags` | Classification metadata | Informational |
| `metadata.hermes.related_skills` | Related skill names | Checked by the conformance suite |

## 2. Invocation and extension fields

| Key | Current roster | Behavior |
|---|---|---|
| `disable-model-invocation` | `dfs-bootstrap`, `dfs-inbox-consolidate`, `dfs-incident`, `dfs-pipeline` | Top-level boolean. These four are excluded from model invocation in the current Trae harness and retain explicit-only banners. |
| `metadata.author` | `dfs-handoff` | Optional author credit; informational only. |
| `metadata.hermes.mcp_tools` | 12 skills | DFS-internal declaration only; no harness support for filtering or authorization. Conformance checks consume the declaration. |
| `metadata.hermes.requires_tools` / `metadata.hermes.fallback_for_tools` | Not used by the current skills | Optional Hermes-specific capability declarations. |

`dfs`, `dfs-interview`, and `dfs-handoff` are model-invocable. Their bodies constrain the allowed behavior: routing-only, read-only interview, and convention-bound handoff respectively.

### 2.1 Explicit-only banner check

The four disabled skills carry an `Invocation — explicit only` banner. The banners are **applied** and checked with:

```bash
grep -l 'Invocation — explicit only' dfs*/SKILL.md
```

The expected result is exactly the four names in the table above. `skillOverrides` or a harness `permission rule` may provide an additional control layer, but the top-level field is the current Trae control.

## 3. Cross-harness trade-off

The generic Agent Skills validator does not allow `disable-model-invocation` at the top level. It reports `Unexpected fields` for `dfs-incident` and `dfs-pipeline`. This is an intentional compatibility trade-off, not a claim of full validation success. Other files with flow-list YAML can fail earlier with `Invalid YAML`; that is a separate pre-existing style issue.

Do not remove the four fields merely to silence the generic validator. Doing so would re-enable model invocation for repository initialization, inbox deletion, production incident response, and end-to-end delivery.

## 4. Verification

```bash
python -c "import pathlib,yaml; [yaml.safe_load(p.read_text(encoding='utf-8').split('---',2)[1]) for p in pathlib.Path('.').glob('dfs*/SKILL.md')]"
python tests/test_harness_field_mapping.py
uvx --from skills-ref agentskills validate dfs-incident
uvx --from skills-ref agentskills validate dfs-pipeline
```
