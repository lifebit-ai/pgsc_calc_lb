# Agent Guide for Lifebit pgsc_calc

## Purpose

This repository is the Lifebit-hosted Nextflow implementation used to run
`pgsc_calc` pipelines in the Lifebit Trusted Research Environment (TRE). Local
work adapts and validates pipeline code; John manually launches and observes
production runs through Lifebit's Nextflow architecture.

The repository is a fork of the PGS Catalog `pgsc_calc` workflow. At the time
this guide was created, `nextflow.config` identifies version `2.3.0`, the
pipeline uses Nextflow DSL2, and the Lifebit remote is
`git@github.com:lifebit-ai/pgsc_calc_lb.git`.

## Non-Negotiable Execution Boundary

- The agent does not have access to the Lifebit TRE, its mounted data, its
  secrets, or its managed Nextflow runtime.
- Work performed here is outside the TRE. Local tests cannot prove that a
  pipeline works on Lifebit infrastructure or production data.
- John must manually push or confirm the branch, select the branch/revision in
  Lifebit, launch the workflow, and return logs or results for diagnosis.
- Never claim a remote run succeeded unless John supplies direct run evidence.
- Produce copy-paste-ready commands and an explicit manual handoff whenever a
  change requires TRE execution.

## Protected Branch Policy

- Never edit, commit, merge, or push directly on `main` or `master`.
- Before changing files, run `git status --short --branch`, `git branch --show-current`,
  and `git remote -v`.
- Work only on John's dedicated branch or a clearly named feature branch.
- If the current branch is `main` or `master`, stop and create or check out a
  non-protected branch before editing.
- Push only the current non-protected branch to `origin`; never force-push and
  never change the default branch.
- Before any requested push, inspect `git status`, `git diff`, and recent
  commits, then state the exact branch and commit SHA John should run.

Current historical branch names are not permanent policy. Verify live Git
state every session rather than assuming `john_test_00` still exists or is the
correct branch.

## Repository Map

- `main.nf`: DSL2 entry point.
- `workflows/pgsc_calc.nf`: top-level `pgsc_calc` workflow composition.
- `subworkflows/local/`: reusable workflow stages for input checks, matching,
  scoring, reports, and ancestry.
- `modules/local/`: individual Nextflow processes.
- `nextflow.config`: defaults, profiles, runtime settings, reports, and
  manifest metadata.
- `conf/base.config`: process defaults and container/runtime definitions.
- `conf/modules.config`: process-specific options and publish behavior.
- `conf/test.config` and `conf/test_full.config`: bundled test profiles.
- `nextflow_schema.json`: public parameter contract.
- `assets/examples/`: synthetic/minimal test inputs.
- `notes/`: dated session notes for environment exploration, test attempts,
  findings, and unresolved questions.
- `tests/`: pytest-workflow and module-level tests.

Do not make broad upstream-style refactors when a small Lifebit-specific
configuration or workflow change is sufficient.

## Exploration Notes

- Keep a dated session log at `notes/session-YYYY-MM-DD.md` while exploring the
  local repository or Lifebit environment and while attempting test runs.
- Create the file for the current date if it does not exist; otherwise append
  new findings to the existing dated file rather than creating duplicates.
- Record confirmed repository state, commands or run settings, observations,
  failures, decisions, unresolved questions, and the next intended step.
- Clearly distinguish confirmed facts from hypotheses or inferences.
- Note whether observations came from local inspection or evidence returned
  from a manual Lifebit run.
- Do not place credentials, private URLs, production paths containing direct
  identifiers, row-level data, or other sensitive TRE material in session
  notes.
- Update the session log as discoveries are made, including when no code change
  is required.

## Related DoH Repositories

Treat these sibling repositories as required design context, not code to copy
blindly:

### `../adjusted-prs`

- Canonical source for the UAE adjusted-PRS preparation and evaluation flow.
- Produces dense genotype data, PLINK2 pfiles, and the `pgsc_calc` samplesheet
  consumed by this workflow.
- Contains the current score-file, ancestry, GRCh38, matching, and downstream
  PRS assumptions in `README.md`, `PIPELINE_CHECKLIST.md`, and
  `notes/uae_prs_methods.md`.
- Reuse its accepted input/output contracts and utilities rather than
  reimplementing them here.

### `../uae-GAP-analysis`

- Canonical source for the UAE GAP study scope, scientific decisions, M42
  delivery contracts, and downstream Lifebit analysis design.
- The active Lifebit implementation namespace is `scripts/lifebit/`; relevant
  governance and join constraints live under `contracts/gap/` and
  `notes/gap-analysis/`.
- M42 performs joint calling and delivers the DRAGEN multi-sample VCF plus QC
  and provenance. This repository must not silently restore local joint
  calling as part of the active GAP path.
- GAP production joins and row-level clinical data remain governed by the
  approved TRE custody boundaries documented there.

When a pipeline change affects file formats, sample identifiers, scoring
outputs, ancestry outputs, or GAP handoffs, inspect both sibling repositories
and identify the exact contract being changed.

## Intended Workflow

1. Confirm the active non-protected branch and cleanly separate unrelated work.
2. Read the relevant contracts in `../adjusted-prs` and
   `../uae-GAP-analysis` before changing pipeline behavior.
3. Make the smallest necessary change to this Nextflow repository.
4. Run feasible local static checks and synthetic tests outside the TRE.
5. Review the diff and record the exact branch, commit, parameters, and
   expected outputs.
6. Push the non-protected branch to Lifebit's Git repository only when John
   requests or approves the push.
7. Give John the precise branch/revision and Lifebit run parameters. John
   manually launches the run in Lifebit's Nextflow architecture.
8. Use the logs, trace, report, timeline, and output checks John returns to
   diagnose the remote behavior and prepare the next small revision.

## Local Validation

Start with checks that do not require production data:

```bash
nextflow -version
nextflow config -profile test
```

When Docker and the required network/container access are available, the
repository's existing test paths are:

```bash
nextflow run . -profile test,docker
make test
```

Use only bundled examples, synthetic fixtures, or approved non-sensitive test
data locally. If a dependency, image, or service is unavailable, report the
limitation rather than weakening a check or fabricating a result.

Local success verifies code structure and the tested local runtime only. The
Lifebit run remains the production acceptance test.

## Lifebit Manual Handoff

Every TRE-facing change should end with a concise handoff containing:

- Git remote, branch, and exact commit SHA.
- Files changed and intended behavior.
- Lifebit workflow entry point and profile/config selection.
- Complete parameter names and non-sensitive values or placeholders.
- Expected inputs, outputs, and acceptance checks.
- Container tags or digests, Nextflow version assumptions, and external
  resource requirements.
- Whether `-resume` is safe for the change.
- Known risks and the exact logs/artifacts John should return.

Do not invent a Lifebit CLI command or hidden platform setting. If the managed
launcher syntax is not documented in this repository or supplied by John,
describe the required fields and let John perform the platform-specific launch.

## Run Evidence

For each manual Lifebit run, ask John to preserve where available:

- Branch and commit SHA selected by Lifebit.
- Nextflow version, execution profile, parameters, and configuration overrides.
- Container image names and immutable digests.
- `.nextflow.log` or the managed equivalent.
- Execution trace, report, timeline, and DAG artifacts.
- Process work directory or task identifiers for failures.
- Output manifests, row/sample counts, checksums, and validation summaries.
- Exact error text and the first failing process, not only screenshots of the
  final failure status.

Keep troubleshooting evidence free of production row-level data and direct
identifiers before placing it in Git.

## Data, Security, and Scientific Guardrails

- Never commit production genomic, phenotype, clinical, score, ancestry, or
  linkage data.
- Never commit credentials, tokens, private URLs, TRE paths containing direct
  identifiers, or secrets copied from Lifebit.
- Use synthetic IDs and small approved fixtures in tests.
- Preserve genome build, contig convention, sample-ID semantics, score-file
  provenance, and matching thresholds explicitly.
- `pgsc_calc` warns that WGS is not directly supported. For UAE workflows,
  follow the accepted conversion and samplesheet contracts from the sibling
  repositories; do not silently pass raw WGS/msVCF inputs into an unsupported
  path.
- Do not silently change `min_overlap`, ambiguous/multiallelic handling,
  liftover behavior, ancestry references, or normalization methods. Treat
  these as scientific decisions requiring explicit review.
- Pin workflow revisions, containers, references, and configuration used for
  accepted runs.

## Engineering Expectations

- Keep Nextflow DSL2 modules and channels explicit and composable.
- Prefer parameterized paths and configuration over hard-coded Lifebit mounts.
- Preserve fail-fast behavior and actionable process errors.
- Update `nextflow_schema.json` and relevant docs when public parameters change.
- Add or adjust synthetic tests when changing process inputs, outputs, channel
  shapes, or parameter validation.
- Keep changes small enough to diagnose from one remote run.
- Do not edit sibling repositories unless John explicitly asks for a coordinated
  contract change.

## Completion Checklist

Before reporting a pipeline revision ready for John:

1. Confirm the branch is neither `main` nor `master`.
2. Inspect the complete diff and ensure no sensitive data is present.
3. Run the feasible local checks and state what could not be run.
4. Confirm compatibility with the relevant `adjusted-prs` and
   `uae-GAP-analysis` contracts.
5. Provide the exact branch/SHA and manual Lifebit launch handoff.
6. Define observable acceptance criteria and requested return artifacts.
