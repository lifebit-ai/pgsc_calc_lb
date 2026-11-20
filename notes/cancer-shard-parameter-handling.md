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

Remote observation on `john_test_08` revision `2587b11`:

- Lifebit discovered and rendered the schema without a duplicate or ambiguous
  schema entry.
- Parameter search and required-only filtering were available.
- Both parameter groups and their descriptions rendered correctly.
- All six VCF/index fields were blank and marked required, as intended.
- `hold_seconds=1200` and `outdir=results` were prefilled as optional values.
- The Additional parameters controls remained available.

Schema discovery and rendering are accepted. Filled-field command generation is
still pending, and params-file handling is a separate acceptance gate.

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

### Moving a params file from VSCode to File Explorer

The documented session-to-platform route is:

1. Create the YAML file beneath the VSCode session's `session_data` directory.
2. Open the running interactive-analysis session page and click **Save**. This
   was the action that synchronized the file in the tested deployment. Only
   files under `session_data` are saved as session results.
3. Open **File Explorer -> Workspace Project Data -> the session's project ->
   Analyses Results -> the VSCode session folder** and locate the saved file.
4. First test whether the Params file selector can use that Analysis Results
   file directly. For a stable reusable location, select the file, choose
   **Virtual copy**, and place it in the project's **Data** folder.

File Explorer also documents **Data -> Import data -> From Analysis** for moving
analysis outputs into project data, but a virtual copy of the individual file is
more targeted when only the params file is needed. Virtual copies do not create
another physical copy of the underlying object.

The CloudOS dataset CLI documents listing, linking, moving, and copying objects
that are already registered in File Explorer. It does not document copying an
arbitrary local `session_data` path directly into project Data, so it is not the
initial transfer mechanism for this file.

Deployment observation: opening the session folder in **Analyses Results** before
clicking Save on the running session page showed an empty folder. After that Save
action, the params file synchronized and appeared correctly in the pipeline's
Params file control. The session URL and ID are intentionally omitted. File
publication and selector visibility are accepted.

John subsequently confirmed that the command preview contained `-params-file`
and did not duplicate the YAML values as individual `--parameter` arguments.
Params-file command generation is accepted. A fresh non-resumed launch with the
zero-second hold was approved; successful managed submission and completion
remain the final params-file acceptance checks.

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
- [Save a VSCode session and capture a snapshot](https://lifebit.atlassian.net/wiki/spaces/CD/pages/1713800006/Save+a+VSCode+session+and+capture+a+snapshot)
- [Find the results of a VSCode session](https://lifebit.atlassian.net/wiki/spaces/CD/pages/1713800150/Find+the+results+of+a+VSCode+session)
- [Use the File explorer](https://lifebit.atlassian.net/wiki/spaces/CD/pages/1282768899/Use+the+File+explorer)
