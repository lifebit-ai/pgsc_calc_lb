# Cancer Shard Probe Parameter Handling

## Purpose

The probe has eight launch parameters: six required Azure VCF/index paths and
two execution options. Concrete storage locations are environment-specific and
must remain in the TRE rather than Git. This note defines the supported reusable
parameter paths and the acceptance checks for Lifebit.

## Schema Parameters

The repository root contains:

- `schema.json`, which names the selectable probe schema.
- `nextflow_schema.json`, which groups six required inputs and two execution
  options.
- `nextflow.config`, which is the authoritative source for parameter defaults.

The schema intentionally does not prefill Azure paths. It should display six
required file inputs and prefill only `hold_seconds=1200` and `outdir=results`.
The existing config default, `$launchDir/results`, resolves to the same
launch-relative location; the schema presents the portable relative form.
Select the exact test branch or commit before opening the Schema view because
Lifebit discovers schemas from the selected revision.

Acceptance checks:

1. The Schema view lists `Cancer chromosome scale-out probe`.
2. All six VCF/index parameters are visible and marked required.
3. The hold is an integer constrained to 0-1,800 seconds and defaults to 1,200.
4. The output directory defaults to `results`.
5. No concrete account, container, or blob path is prefilled from Git.
6. The command preview contains each selected value exactly once.

## Nextflow Params File

For repeated launches with many parameters, prefer a TRE-held YAML params file.
Copy `assets/examples/cancer_shard_probe.params.example.yaml` into approved TRE
storage, replace every placeholder there, and select it with Lifebit's
**Params file** option. The platform should pass the selected file directly to
Nextflow as `-params-file`; it does not resolve Lifebit workspace or user
variables inside the file.

Before launching, verify that the command preview contains `-params-file`, the
selected revision is correct, and no duplicate individual `--parameter` values
were added. Keep one immutable copy of the submitted params file with the
analysis evidence, subject to TRE policy.

## Lifebit Platform Config

The **Custom -> Import** control does not accept a plain Nextflow JSON object.
It expects the Lifebit Platform Config array exposed by a prior analysis. Each
entry contains `prefix`, `name`, `parameterKind`, and `value`. The accepted run
represented account-short Azure URIs as `textValue`, preserving them verbatim.

This is useful for cloning a configuration in the same workspace. Change the
output directory and any experiment-specific values before launch, then inspect
the generated command. Do not commit an exported Platform Config containing
concrete storage paths.

## CloudOS CLI and API Follow-up

The analysis page generated a `cloudos job run` command with placeholders for an
API key and explicit options for platform URL, workspace, project, workflow,
job name, master instance, disk, parameters, Nextflow version, cost limit,
revision, and accelerated result saving. This could make scripted submission
from an analytics node more reproducible than repeated UI entry. The generated
command itself contained workspace and complete storage identifiers and is not
retained in Git.

Questions for Lifebit:

1. Is `cloudos job run` supported from this TRE's analytics/interactive nodes?
2. Is the API key from User Settings the only missing authentication component,
   or is a workspace role, CLI profile, firewall rule, or feature enablement also
   required?
3. What is the approved way to supply and rotate the API key without placing it
   in a script, shell history, environment capture, notebook, or Git repository?
4. Do interactive nodes automatically know the platform URL and workspace ID in
   this deployment, as described in the general CloudOS CLI documentation?
5. Does `--instance-type` control only the master? How are the Azure worker SKU,
   lifecycle, disk, queue, and autoscaling bounds selected programmatically?
6. Can `--job-config` reference a TRE-held params/config file, and which format
   should be preferred for Nextflow jobs with many paths?
7. How should an exact Git commit and the deployment's Nextflow
   `22.11.1-edge` runtime be pinned and audited through the CLI/API?
8. Can CLI-submitted jobs retrieve or link logs without the interactive-session
   `Internal Server Error` observed in the UI?
9. Which audit events record API-key creation, scripted submission, parameter
   values, and job ownership?

Do not create or use an API key until Lifebit confirms the approved secret
handling and scripted-submission procedure for this TRE.

## Documentation Sources

- [Run a pipeline](https://lifebit.atlassian.net/wiki/spaces/CD/pages/813040723/Run+a+pipeline)
- [Add multiple schemas to your pipeline repository](https://lifebit.atlassian.net/wiki/spaces/CD/pages/1231716381/Add+multiple+schemas+to+your+pipeline+repository)
- [Submit and Monitor Jobs through the CLI](https://lifebit.atlassian.net/wiki/spaces/CD/pages/1798701103/Submit+and+Monitor+Jobs+through+the+CLI)
- [View pipeline metrics/results](https://lifebit.atlassian.net/wiki/spaces/CD/pages/813040996/View+pipeline+metrics+results+and+mount+results+into+an+interactive+session)
