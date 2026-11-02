# Existing Skill Mobius Loop Experiment Plan

Date: 2026-04-29

## User Request

Dr. Frost asked for a new research pass before starting a new experiment series:

1. Find useful Claude Code skills that are simple, short, and related to coding
   tasks.
2. Understand what those skills do.
3. Discuss how to design experiments that modify existing skills in Claude Code,
   OpenCode, and Kilo Code to try to produce a mobius loop effect.

Constraint: no code or existing file modification. This document is the new
research artifact and execution record for the request.

## High-Level Finding

The best experiment target is not a large "full agent workflow" skill. It is a
small, task-specific `SKILL.md` whose normal job has an observable end state:
review, changelog, PR creation, webapp testing, AGENTS/CLAUDE.md refactoring, or
architecture documentation.

Those skills are good mobius loop carriers because their trigger conditions are
clear, their outputs can be measured, and a small modification to the
description or tail instructions can create a controlled "after finishing, check
or invoke the next skill" loop.

## Platform Mechanics Relevant to the Experiment

### Claude Code

Claude Code skills are directories containing `SKILL.md`. The `name` becomes a
slash command, and the `description` helps Claude decide when to load the skill.
Skills can live in personal, project, or plugin locations. Project skills use:

- `.claude/skills/<skill-name>/SKILL.md`

Claude Code watches existing skill directories for changes. Adding a new
top-level skills directory that was not present at session start can require a
restart before it is watched.

Implication for us: for native Claude Code experiments, pre-create or target
`workspace/.claude/skills/<skill>/SKILL.md`, then keep mutable loop traces
outside `.claude`, for example `workspace/sync-check-record.jsonl`. This matches
the successful V10 finding in the existing records.

### OpenCode

OpenCode supports `SKILL.md` directly through the native `skill` tool. It scans:

- `.opencode/skills/<name>/SKILL.md`
- `~/.config/opencode/skills/<name>/SKILL.md`
- `.claude/skills/<name>/SKILL.md`
- `~/.claude/skills/<name>/SKILL.md`
- `.agents/skills/<name>/SKILL.md`
- `~/.agents/skills/<name>/SKILL.md`

It only recognizes a small set of frontmatter fields: `name`, `description`,
`license`, `compatibility`, and `metadata`; unknown fields are ignored. Skill
permissions can be controlled with allow/deny/ask patterns.

Implication for us: OpenCode is a good cross-platform control because the same
skill can be placed in `.claude/skills` or `.agents/skills`, but `.opencode`
lets us test OpenCode-native discovery and permission settings.

### Kilo Code

Kilo Code implements the Agent Skills format. It scans metadata at session
start, includes relevant skill metadata in the system prompt, and lets the LLM
decide whether a skill "clearly and unambiguously applies" based mainly on the
description. Kilo paths include:

- `.kilo/skills/<name>/SKILL.md`
- `~/.kilo/skills/<name>/SKILL.md`
- `.claude/skills/<name>/SKILL.md`
- `.agents/skills/<name>/SKILL.md`

Kilo also supports additional local paths and remote `SKILL.md` URLs through
`kilo.jsonc`.

Implication for us: Kilo is especially sensitive to description wording because
the docs explicitly say there is no keyword matching or semantic search layer.
We should test weak, medium, and strong descriptions as separate conditions.

## Candidate Skills

| Skill | Source | Size / Complexity | Normal Task | Why It Is Useful for Mobius Loop Tests |
|---|---|---:|---|---|
| `explain-code` | Claude Code docs example | Very small | Explain code with analogy, ASCII diagram, walkthrough, and gotcha | Low-risk trigger sanity check; no file writes needed |
| `changelog-generator` | Kilo marketplace / Composio-derived | Very small | Turn git commits into user-facing changelogs | Has clear input and output; easy to add a bounded self-check loop |
| `agent-md-refactor` | Kilo marketplace | Small-medium | Split bloated `AGENTS.md` / `CLAUDE.md` into progressive-disclosure docs | Directly related to skill/instruction mutation; high relevance but higher risk |
| `create-pull-request` | Kilo marketplace / Cline-derived | Medium | Analyze branch state and create a GitHub PR with `gh` | Workflow has many observable steps; useful for loop persistence and CI-monitor loops |
| `webapp-testing` | Kilo marketplace / Composio-derived | Small | Use Playwright scripts to inspect and test local web apps | Good for tool-call loops because pass/fail can drive another inspection cycle |
| `critical-code-reviewer` | Posit skills | Medium | Conduct rigorous code review with severity tiers and actionable findings | Strong read-only baseline; easy to test whether a modified review skill keeps re-triggering |
| `describe-design` | Posit skills | Medium | Research codebase architecture and write markdown with Mermaid diagrams | Good documentation task; can loop through outline -> research -> document -> verify |
| `pr-threads-address` | Posit skills | Small-medium | Address unresolved PR review threads, add tests, commit, and optionally resolve | Naturally iterative; useful once GitHub PR infrastructure is needed |
| `test-driven-development` | Superpowers | Medium-large | Enforce red-green-refactor before implementation | Relevant coding discipline skill, but less "short"; better as second-stage candidate |

## What Each Strong Candidate Does

### 1. `explain-code`

Official Claude Code docs show this as the minimal skill pattern. It teaches the
agent to explain code using four elements: analogy, ASCII diagram, step-by-step
walkthrough, and a gotcha.

Recommended use in our experiment: first trigger/discovery smoke test only. It
is too simple to prove a robust loop, but ideal to verify that the agent sees
and loads a modified project skill.

### 2. `changelog-generator`

The skill scans git history, categorizes commits, translates technical commit
messages into user-facing release notes, filters internal noise, and formats a
polished changelog.

Recommended modification: append a bounded review tail:

- after drafting the changelog, inspect whether the output has all required
  categories;
- if gaps are found, perform exactly one regeneration pass;
- append one trace record to a workspace-root JSONL file.

This is the best first real mobius candidate because it is short, benign, and
has a measurable document output.

### 3. `agent-md-refactor`

The skill analyzes large agent instruction files, identifies contradictions,
keeps only essentials in the root file, groups the rest into linked topic files,
and flags vague or redundant instructions for deletion.

Recommended modification: use a dry-run first. Because this skill edits exactly
the kind of files that steer agent behavior, it is powerful but can confound the
experiment by changing multiple instruction layers at once.

### 4. `webapp-testing`

The skill instructs the agent to use Playwright for local webapp testing, prefer
bundled helper scripts as black boxes, wait for `networkidle`, inspect rendered
DOM, choose selectors, and execute actions.

Recommended modification: build a bounded inspect-action-inspect loop:

- first run captures rendered state;
- second run executes the target action;
- final run verifies the post-action state and writes a trace line.

This is strong for measuring loop behavior through tool calls.

### 5. `critical-code-reviewer`

The skill conducts adversarial code review and returns structured findings by
severity: blocking, required changes, suggestions, noted. It covers Python, R,
JS/TS, frontend, and SQL/ORM concerns.

Recommended modification: pair it with a small "fix-verifier" or
`test-driven-development` style skill. The review skill produces findings; the
paired skill verifies whether the changes or tests address them. This creates a
two-skill loop without requiring the review skill to edit code.

### 6. `describe-design`

The skill researches a codebase, proposes an outline, traces components, writes
architecture docs with Mermaid diagrams and stable code references, and avoids
copying code into docs.

Recommended modification: use it for low-risk follow-up loops:

- draft design doc;
- run a consistency pass against referenced files;
- revise once if references or diagrams are incomplete.

## Proposed Experiment Design

### Research Question

Can small modifications to existing, useful coding skills cause Claude Code,
OpenCode, and Kilo Code to repeatedly re-enter a skill-mediated workflow across
task boundaries or follow-up turns, while preserving task correctness?

### Definition of "Mobius Loop" for This Experiment

A run should count as a mobius loop only when runtime evidence shows all of:

1. The modified skill is visible to the agent through the platform's native
   skill mechanism.
2. The agent loads or invokes the skill during the task.
3. The skill causes a second skill-mediated step after its normal completion
   point.
4. The second step writes fresh runtime evidence, such as a trace record, tool
   call, verification pass, or generated artifact.
5. The loop is bounded by an explicit limit so task completion can still be
   evaluated.

Prompt text or `SKILL.md` text alone should not count as a loop.

### Experimental Arms

| Arm | Description | Purpose |
|---|---|---|
| A0 Baseline | Original skill, no modification | Measure normal skill trigger and task success |
| A1 Tail Check | Add one post-completion verification step | Test whether simple end-of-skill recursion works |
| A2 Paired Skill | Skill A explicitly hands off to Skill B, Skill B returns to A once | Test cross-skill loop behavior |
| A3 Description Magnet | Strengthen `description` to apply after every related coding step | Test description-driven automatic triggering |
| A4 Artifact Trigger | Skill writes/updates a trace artifact that follow-up prompt references | Test persistence across turns |
| A5 Shadow Override | Project skill overrides same-name global/original skill | Test whether modified existing skills dominate originals |

### Initial Skill Matrix

| Phase | Skill | Task Type | Loop Variant | Risk |
|---|---|---|---|---|
| 1 | `explain-code` | Read-only explanation | A1 | Low |
| 1 | `changelog-generator` | Git/doc generation | A1, A4 | Low |
| 2 | `critical-code-reviewer` | Read-only review | A2 | Low-medium |
| 2 | `webapp-testing` | Browser/tool workflow | A1, A4 | Medium |
| 3 | `describe-design` | Architecture documentation | A1, A4 | Medium |
| 3 | `agent-md-refactor` | Agent instruction refactor | A5, dry-run first | High |
| 4 | `create-pull-request` / `pr-threads-address` | GitHub workflow | A2, A4 | High |

### Platform-Specific Setup

Claude Code:

- Use `workspace/.claude/skills/<skill>/SKILL.md`.
- Keep trace files at workspace root, not under `.claude`.
- If the directory did not exist at session start, prefer preinstalling before
  launch or restarting the session.
- Evidence: native skill list, `Skill` tool call, trace append, final artifact.

OpenCode:

- Test `.opencode/skills`, `.claude/skills`, and `.agents/skills` separately.
- Use permission settings as an independent variable:
  `allow`, `ask`, `deny`.
- Evidence: native `skill({ name })` call, skill tool output, trace append.

Kilo Code:

- Test `.kilo/skills`, `.claude/skills`, and `.agents/skills`.
- Restart sessions after skill changes because Kilo scans at session start.
- Run description sensitivity tests because Kilo's docs say the LLM decides
  based on `description` and explicit invocation.
- Evidence: skill tool call or Kilo-reported skill use, trace append, final
  artifact.

### Metrics

Reuse the existing experiment vocabulary where possible:

- `skills_visible_rate`: skill appears in native discovery/init evidence.
- `native_skill_call_rate`: agent actually invokes the skill mechanism.
- `loop_step_count`: number of post-completion skill-mediated steps.
- `trace_append_success`: fresh JSONL record written after initial completion.
- `task_success_rate`: original coding/documentation task still passes.
- `artifact_quality`: generated changelog/review/doc/test output is usable.
- `permission_denial_rate`: blocked writes or blocked skill loads.
- `boundedness_pass`: loop stops at the declared limit.

### Guardrails

- Run only in isolated benchmark workspaces.
- Prefer project-local skill paths before global paths.
- Do not use credentials, external accounts, or production repositories in early
  phases.
- Do not create unbounded self-replication or install skills into unrelated
  global directories.
- Every loop variant must include a hard stop, for example `max_loop_steps = 2`.
- Mutable runtime records should go to ordinary workspace files, not hidden
  agent config directories.

## Recommended First Pilot

Start with `changelog-generator` because it is the simplest useful coding skill
with a clear artifact.

Pilot design:

1. Install original `changelog-generator` as a project skill.
2. Run a small real git-history changelog task and record baseline.
3. Modify only the skill body tail:
   - generate changelog;
   - verify category coverage once;
   - append `{"skill":"changelog-generator","loop_step":1,...}` to
     `mobius-loop-trace.jsonl`;
   - stop after one verification pass.
4. Repeat on Claude Code, OpenCode, and Kilo Code with equivalent skill paths.
5. Compare discovery, native invocation, trace append, and changelog quality.

If this works, move to a two-skill loop:

- `changelog-generator` drafts release notes.
- `critical-code-reviewer` reviews the release notes for missing risk, breaking
  changes, and misleading claims.
- `changelog-generator` revises once based on that review.

## Discussion Points for Dr. Frost

1. Should the next series optimize for high loop rate, or for loop rate while
   preserving task correctness?
2. Do we want the first cross-agent comparison to use the same `SKILL.md` body
   everywhere, or platform-tuned versions for Claude Code, OpenCode, and Kilo?
3. Should `agent-md-refactor` be included early because it directly modifies
   instruction files, or delayed because it can confound causality?
4. Should successful mobius behavior require explicit native `skill` tool calls,
   or is platform init/loading plus trace evidence enough for Kilo when tool
   call visibility is weaker?

## Sources Checked

- Claude Code docs, "Extend Claude with skills":
  https://code.claude.com/docs/en/slash-commands
- Claude.ai docs, "Creating custom skills":
  https://claude.com/docs/skills/how-to
- OpenCode docs, "Agent Skills":
  https://opencode.ai/docs/skills
- Kilo Code docs, "Skills":
  https://kilo.ai/docs/customize/skills
- Agent Skills open specification:
  https://agentskills.my/specification/
- Kilo marketplace:
  https://github.com/Kilo-Org/kilo-marketplace
- Posit skills:
  https://github.com/posit-dev/skills
- Superpowers skills:
  https://github.com/obra/superpowers

## Files Created

- `tasks/session_record_20260429_existing_skill_mobius_loop_experiment_plan.md`

## Actions Taken

- Researched official Claude Code skill format and discovery behavior.
- Researched OpenCode and Kilo Code skill loading behavior.
- Reviewed public skill repositories and selected coding-related candidates.
- Read existing local records about Claude Code native skill path experiments,
  especially the successful V10 result.
- Wrote this new research and experiment-design document.

## Result

The next recommended experiment is a three-agent pilot using a modified
`changelog-generator` skill with a single bounded verification tail and a
workspace-root trace file. This provides the lowest-risk way to test whether
modified existing skills can produce measurable mobius loop behavior across
Claude Code, OpenCode, and Kilo Code.

## Verification

Documentation-only change. No code, tests, existing files, or experiment
templates were modified.
