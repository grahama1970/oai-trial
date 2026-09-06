# Skill reuse — source-only presentation references

**Scope:** Extra Credit slide `r26-wrapper`; no additional runtime or skill build. Project behavior stays at `0375af56bf681e9441edcb7433cfe58951db77b2`. The excerpts below were inspected through GitHub at the explicitly pinned skill snapshot `00c144b3077f6498becd1514c1c8106fba2f0943`. This known earlier source version explains the established pattern; it is not asserted to be the source of a later execution receipt or the present workstation installation.

## Concise contract

Source: [anonymize-data/SKILL.md](https://github.com/grahama1970/agent-skills/blob/00c144b3077f6498becd1514c1c8106fba2f0943/skills/anonymize-data/SKILL.md).

Exact passage:

> Operate the canonical `oai-trial` project. Do not duplicate its matcher,
> format adapters, verifier, schemas or error handling in this skill. The
> project's existing argparse CLI is intentionally retained; this wrapper adds
> no Python CLI or service.

Exact passage:

> Do not declare success from an exit code alone: read the
> actual report, validate its readiness fields, and inspect output for the requested
> format. Corrupt or missing reports are not READY.

## Thin delegation

Source: [anonymize-data/run.sh](https://github.com/grahama1970/agent-skills/blob/00c144b3077f6498becd1514c1c8106fba2f0943/skills/anonymize-data/run.sh).

Exact excerpt:

```bash
# The installed entrypoint preserves the caller's cwd for relative data paths.
exec "$ENTRY" "$@"
```

The inspected source checks the imported package directory against the selected checkout before this delegation. That is source inspection, not an installation or test performed by this authoring task.

## Retained behavior

Source: [anonymize-data/sanity.sh](https://github.com/grahama1970/agent-skills/blob/00c144b3077f6498becd1514c1c8106fba2f0943/skills/anonymize-data/sanity.sh).

Exact excerpt:

```bash
export ANONYMIZE_DATA_TEST_RUNNER="$HERE/run.sh"
```

Exact excerpt:

```bash
    if result.returncode == 0 or 'anonymize_data_wrong_install' not in result.stderr:
        raise SystemExit('wrong installed project was not refused')
```

These excerpts show the delegation/test boundary and a wrong-install control. The current project's retained path regression is separately linked at its frozen implementation commit. No new execution result is inferred.

## best-practices-skills guidance

Source: [best-practices-skills/SKILL.md](https://github.com/grahama1970/agent-skills/blob/00c144b3077f6498becd1514c1c8106fba2f0943/skills/best-practices-skills/SKILL.md), Required structure.

Exact passage:

> - A skill is a folder with a required `SKILL.md` at the root.
> - `SKILL.md` must start with YAML frontmatter (no code fences).
> - Frontmatter delimiters must be standalone lines: opening `---` on line 1 and closing `---` on its own line.
> - Frontmatter must include `name` and `description`.
> - The `description` should contain explicit trigger contexts (what users will say).
> - Keep `SKILL.md` concise; move large content into `references/` or `scripts/`.

The presentation uses the concise-contract/delegation/behavioral-check pattern for workflows worth reusing. It does not claim a fresh skill-validation run, universal best-practices compliance, live construction, or permission for assessment assistance.
