# Lifebit Pipeline Follow-up

## Purpose

We have been testing a Nextflow repository incrementally on the DoH Lifebit
deployment before running the full `pgsc_calc` toy example. The tests progressed
from a single process, to a two-process file handoff, to selecting an output
from one Batch Analysis as the input to another.

This note consolidates the questions and product suggestions arising from that
work. Workspace, project, analysis, job, storage, session, and deployment
identifiers have been omitted.

## What We Confirmed

- The DoH deployment uses Azure Batch and Azure Blob Storage in the UAE North
  region.
- The platform currently runs Nextflow `22.11.1-edge`, build 5834 from
  29 November 2022.
- A public PGSCatalog image from GitHub Container Registry worked:
  `ghcr.io/pgscatalog/pyyaml:6.0`.
- A two-process workflow successfully passed a file through a Nextflow `path`
  channel. Source, downstream-input, and mounted-output checksums matched.
- Selecting a file from an earlier Batch Analysis worked. The UI displayed a
  short relative path, while the generated command passed a concrete platform
  HTTPS input URL to Nextflow.
- A fresh analysis resolves the latest commit from a selected branch. Clone and
  Resume preserve the revision locked into the original analysis.
- The repository compatibility changes are relevant to this deployment: they
  replace features requiring newer Nextflow releases with equivalents that run
  on the observed 22.11 runtime.

## Priority Technical Questions

### 1. Supported container images and registries

The shorthand image `ubuntu:22.04` was rejected by Azure Batch with:

`One or more container images specified are invalid`

The fully qualified public image `ghcr.io/pgscatalog/pyyaml:6.0` subsequently
ran successfully.

Could Lifebit clarify:

- Which public and private container registries are supported by the DoH Azure
  Batch deployment?
- Is there an allowlist or catalog of currently approved images, registries, or
  repositories?
- Are Docker Hub and GitHub Container Registry supported?
- Must image names be fully qualified or pinned by digest?
- Must images be mirrored into Azure Container Registry or approved through a
  separate process?
- What CPU architecture and image requirements apply to the worker pool?
- Can Lifebit provide the underlying Azure validation details for the rejected
  Ubuntu image, including the image reference Azure received?

### 2. Custom output-directory parameter is not honored

The workflow form showed a custom parameter named `outdir` with the value
`results_jt03`. The generated CloudOS CLI preview represented this as
`out=results_jt03`. The workflow reads `params.outdir`, but the completed
analysis wrote everything beneath the default `results` directory. No
`results_jt03` directory appeared.

Could Lifebit clarify:

- Which parameter name should a custom Nextflow workflow use for its output
  directory?
- Is the UI field `outdir` expected to map to the CloudOS CLI key `out`?
- Does the generated parameter configuration translate `out` back to
  `outdir`?
- Does the platform intentionally force all outputs beneath `results`?
- Are unique output folder names supported for repeated analyses?

This also affects result mounting because repeated analyses publish folders
with the same name.

### 3. Embedded execution report is blocked

The workflow generated its Nextflow execution report, but the analysis
**Report** tab displayed:

`your organization does not allow you to view this site`

The report artifact could be accessed after mounting results into an
interactive session, so generation and embedded viewing appear to be separate
issues.

Could Lifebit confirm:

- Whether embedded reports are intentionally disabled by DoH policy.
- Whether this is an iframe, content-security-policy, or deployment
  configuration issue.
- The supported way to view generated Nextflow reports inside the TRE.

### 4. Nextflow runtime and upgrade policy

The observed runtime is `22.11.1-edge`, built in November 2022. The upstream
`pgsc_calc` release originally required newer Nextflow features, and this fork
contains compatibility changes specifically relevant to the older runtime.

Could Lifebit confirm:

- Which Nextflow versions are supported on the DoH Azure deployment?
- Whether users can select a version.
- The upgrade and security-maintenance policy for the current edge build.
- Whether Lifebit has validated a newer stable Nextflow release with Azure
  Batch.

### 5. Main-script selection and manifest precedence

An imported workflow was configured in the UI with `hello.nf` as its main file,
but Nextflow launched `main.nf` because the repository manifest declared:

```groovy
manifest.mainScript = 'main.nf'
```

Changing the repository manifest to `hello.nf` fixed the launch.

Could Lifebit document the expected precedence between the UI **Main file**
field and `manifest.mainScript`? If the repository manifest is authoritative,
the import screen could detect and warn about conflicting values.

### 6. Schema discovery differs between import and run screens

During tool creation, the schema selector reported:

`No schemas found for the selected version`

The run screen later detected and parsed the repository's root
`nextflow_schema.json` correctly.

Could Lifebit clarify whether these controls serve different purposes, or
whether schema discovery is inconsistent between the two screens?

## Reproducibility and Diagnostics Questions

### Revision reporting

The generated command correctly pinned the exact commit with `-r`, and the
report displayed the correct commit hash, but another report field showed
`revision null`.

Could this field be populated consistently to avoid ambiguity in run records?

### Execution trace access

The generated command enabled a Nextflow trace file, but it was not present in
the mounted published results.

Where can users retrieve the trace referenced by the launch command?

### Lenient caching

The platform adds `-process.cache lenient` and `-resume` automatically.

Could Lifebit explain why lenient caching is the default and document its
reproducibility implications for resumed genomic analyses?

### Azure-specific workflow documentation

Most available Lifebit Nextflow documentation is AWS-focused. Azure behavior
differs for executors, storage paths, file staging, registries, and result
handling.

Could Lifebit provide or identify the Azure-specific workflow-development and
operations guidance for the DoH deployment?

## Product Suggestions

### Allow revision selection when cloning

Preserve the original pinned revision by default for reproducibility, but allow
the user creating a clone to choose one of the following:

- Keep the source analysis commit.
- Resolve the latest commit from the originally selected branch or tag.
- Select another branch, tag, or exact commit.

The clone screen should display both the source revision and the revision the
new analysis will run before submission.

### Add direct navigation to Pipelines and Tools

Provide a persistent **Pipelines and Tools** navigation item in Advanced
Analytics. Currently, the discoverable route begins on the analyses page and
requires clicking **Run Analysis**, even when the intent is to browse, import,
inspect, or manage tools.

### Allow sorting Workspace Project Data by Created At

In **Add Data** -> **Workspace Project Data**, make the **Created At** column
sortable. Newest-first sorting would make recent pipeline outputs easier to
locate among similarly named analyses and result folders.

### Make result mounting collision-safe

Mounting an analysis result into an interactive session fails when a folder
with the same name is already mounted. Repeated workflows commonly produce a
folder named `results`, which prevents side-by-side comparison.

Provide either:

- A user-editable destination name when mounting.
- An automatically unique name derived from the analysis name and a short run
  identifier or timestamp.

The UI should display the proposed destination before mounting.

### Allow whole-folder mounting from the analysis Results page

Allow users to select and mount the complete results folder directly from an
analysis **Results** page. Whole-folder selection works through **Add Data** ->
**Workspace Project Data**, but was not available from the analysis page.
Aligning the two paths would remove an unnecessary workaround.

## Requested Follow-up

The most immediate needs before running the full `pgsc_calc` example are:

1. Confirm the supported container registries and image requirements.
2. Clarify how custom output-directory parameters are mapped or overridden.
3. Confirm the supported method for viewing execution reports and retrieving
   traces.
4. Confirm the supported Nextflow version and Azure-specific operational
   guidance.
