---
name: dispatch-scientist-subagents
description: Use when the user explicitly invokes $dispatch-scientist-subagents for two or more independent workstreams that should be delegated to Codex subagents.
---

# Dispatch Scientist Subagents

## Core rule

Give every spawned subagent a random scientist codename as its actual `task_name`. Put professional responsibilities in `message`, never in `task_name`, so supported Codex clients show names such as `newton`, `curie`, and `feynman` instead of work-summary titles.

## Compatibility preflight

Use the native collaboration tools exposed by the current session. They must include `spawn_agent` with a `task_name` argument and agent listing, messaging, waiting, and interruption tools. Tool namespaces can differ between clients; use the names and schemas actually provided. A legacy `spawn_agent` without `task_name` cannot meet this skill's naming contract.

If the required tools are absent, explain the missing capability and point the user to this package's [installation and settings guide](README.md). Do not simulate subagents or substitute ordinary chats. Do not edit user configuration automatically. A Python 3.10+ interpreter is required for the name helper; resolve `python`, `python3`, or Windows `py -3` before running it.

## Workflow

1. Confirm that at least two workstreams can proceed independently. Otherwise explain why fan-out is unsuitable and use the smallest safe execution shape.
2. Call `list_agents` and respect the session's available concurrency. Call collaboration tools directly, never through shell commands or `functions.exec`.
3. Define each assignment's professional role, objective, scope, constraints, deliverable, verification, and file ownership. Use read-only work or sequential waves when writes would overlap.
4. Resolve this skill's directory from the loaded `SKILL.md` path, not from the user's working directory. Run the bundled `scripts/pick_names.py --count N` using the available Python interpreter and a quoted absolute script path. Parse its stdout as a JSON array. For later waves, pass each reserved name with a repeated `--exclude NAME` argument. Stop and report the error if selection fails.
5. Call `spawn_agent` once per assignment. Set `task_name` to exactly one returned lowercase codename. Put all work details in `message`.
6. Refer to agents by codename in updates and follow-ups. Wait for required results, reconcile conflicts, and independently verify material conclusions before reporting completion.

## Assignment message

Include all six fields:

```text
Professional role: state the task-specific expertise
Objective: state one bounded outcome
Scope: list the files, modules, or questions
Constraints: state read-only or edit ownership and prohibited areas
Deliverable: state the exact response or artifact
Verification: list the checks the agent must perform
```

## Sidebar naming contract

- Use `task_name: "newton"`; never use `task_name: "backend_review"` or another semantic title.
- Keep names unique within the invocation and stable for the agent's lifetime.
- The UI may capitalize a name, but the tool value must remain lowercase ASCII.
- Discourage nested fan-out. Allow it only when explicitly required, an unused codename exists, and concurrency and file ownership remain safe.

## Failure rules

- No subagent tools: report the unavailable capability; do not simulate delegation.
- No free slot: wait when appropriate or report the limit; do not over-dispatch.
- Failed agent: report its codename and explicitly retry, replace it with a new unused codename, or finish in the primary agent.
- Name helper failure: stop; do not fall back to semantic sidebar titles.
