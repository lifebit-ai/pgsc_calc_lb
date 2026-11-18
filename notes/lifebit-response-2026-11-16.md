# Lifebit Response - 2026-11-16

## Source and Handling

Lifebit responded by email to the three priority questions in
`lifebit-pipeline-follow-up.md`. The source PDF contains personal contact details
and is intentionally excluded from Git. This file records a sanitized technical
digest.

## Executive Summary

- Azure compute has two data access modes: linked/streamed or physically copied.
- Interactive Analysis supports both modes. Azure Batch/Nextflow currently
  supports only physical copies.
- Every Azure Batch task receives its own local copy of each declared Nextflow
  `path` input, even when tasks run on the same worker. Copies are not shared or
  cached between tasks.
- Lifebit recommends full `az://` paths in samplesheets and explicit sibling
  `path` inputs for pfile triplets and VCF/index pairs.
- All public container registries are supported from Lifebit's side, subject to
  the M42/DoH firewall.
- `outdir` is supported and is not renamed or overridden by Lifebit. Our command
  sent `out`, so the workflow correctly fell back to its default `outdir`.
- Lifebit has logged the Azure interactive-session `results` mount collision for
  improvement.

## 1. Azure Data Movement

### Two access modes

**Linked/streamed**

- Blob data is streamed through BlobFuse on access.
- The full object is not copied into session storage.
- This is the default for Azure Interactive Analysis.
- Linked data is read-only under `filesystems`.
- Azure Batch/Nextflow does not support this mode today.

**Copied**

- The full file is copied to compute-local disk before use.
- Interactive Analysis exposes copied data read-only under
  `mounted-data-readonly`, consuming the Mounted Data allocation.
- This is currently the only mode for Azure Batch/Nextflow.
- Lifebit uses "mounted", "staged", and "localized" to describe variants of
  this copied mode in this context.

### Interactive linked-data cache

- BlobFuse reads in 8 MB blocks with read-ahead.
- Each actively read linked item can use up to 10 GB of local disk cache and up
  to 2 GB of memory.
- Old cached blocks are evicted when the limit is reached or after 10 minutes
  without use.
- If cache disk space is exhausted, reads continue without cache but repeated
  access is slower.
- An interactive session supports up to 100 linked items.

### Azure Batch/Nextflow path

For each task:

```text
Blob source
  -> copy input to worker-local disk
  -> process executes
  -> upload outputs to Blob
  -> expose final outputs in the analysis results folder
```

- Each task declaring a file as a Nextflow `path` input receives its own copy.
- Copies are not shared between tasks, including tasks scheduled on the same
  worker.
- A folder declared as a `path` input downloads the entire folder. Avoid this
  for large shared folders.
- Lifebit may scope a linked/streaming mode for Azure Batch and requested
  details about our intended scale and access patterns.

### Unexpected HTTPS input

Lifebit expects launch-form files to reach Nextflow as `az://` Blob paths. Our
single-file ingress test generated an HTTPS platform input URL instead. Lifebit
requested the job ID to investigate. Share the identifier privately; do not
store it in Git.

## 2. Recommended Genomic Input Pattern

- Declare related files together in each process, for example:
  `tuple val(id), path(pgen), path(pvar), path(psam)`.
- An alternative is `Channel.fromFilePairs` with a three-file pfile pattern.
- Nextflow localizes sibling files under their original names, allowing
  `plink2 --pfile <prefix>`.
- Declare `.vcf.gz` and `.tbi`/`.csi` indexes together in the same way.
- Use full `az://` paths in samplesheet rows and convert every file column to a
  Nextflow `path` input.
- Do not depend on resolving data paths relative to the samplesheet location.
- Reduce repeated downloads by combining operations that read the same large
  file into one process where scientifically and operationally appropriate.
- Shard by chromosome so each task copies only the files it needs.

## 3. Worker Disk and Storage

- The Azure Batch worker disk must hold inputs plus intermediates for every task
  running concurrently on that worker.
- The disk size is selected in the UI or CloudOS CLI.
- If the request fits the VM's local disk, local disk is used.
- If the request exceeds local capacity, or the VM has no local disk, the
  platform attaches an Azure Managed Disk using Standard SSD LRS.
- A managed disk can be up to 32 TB. Lifebit reported no additional platform
  quota beyond Azure limits.
- Work storage is Azure Blob storage in the deployment subscription, with no
  Lifebit-specific quota beyond Azure storage-account limits.

## 4. Data Lifetime and Provenance

- Final results remain for completed and failed analyses.
- Non-resumable analyses remove the work directory during teardown.
- Resumable analyses retain the work directory and Nextflow cache so completed
  tasks can be reused.
- Nextflow logs, traces, and reports are retained with each analysis.
- Blob objects retain Azure-native ETag and Content-MD5 properties where set.
- Lifebit does not currently expose per-stage checksums or object versioning.

## 5. Container Registries

- Lifebit supports public registries such as Docker Hub, GHCR, and Quay.
- Registry access remains subject to the M42/DoH network firewall.
- Lifebit identified the Docker Hub hosts that may require firewall access.
- They requested private troubleshooting evidence for the rejected Ubuntu
  image: the job ID, a screenshot showing the error location, the container
  declaration, and the full `.nextflow.log`.
- They also suggested running `podman pull ubuntu:22.04` in an Interactive
  Analysis session to distinguish firewall access from pipeline configuration.

## 6. Output Directory

- Each analysis receives a distinct platform results location.
- `publishDir` controls the hierarchy shown beneath the analysis Results tab.
- A relative `--outdir results_jt03` should create a `results_jt03` subfolder.
- Lifebit does not reserve, rename, or override `outdir`.
- The parameter must be named exactly `outdir` for a workflow reading
  `params.outdir`.
- Our CLI preview sent `out=results_jt03`, not `outdir=results_jt03`, explaining
  why the workflow used its default `results` value.
- Lifebit requested the job ID and a pre-launch screenshot to determine why the
  field name changed.

## 7. Interactive Results Mount Collision

- On Azure, analysis results are currently attached to an interactive session
  under the fixed folder name `results`.
- This collides when a `results` folder is already attached.
- Lifebit has logged this behavior for improvement.
- Current workarounds are to start a new session for each analysis, link the
  analysis results through File Explorer, or link the uniquely named parent job
  folder.

## Implications for This Repository

### Samplesheet contract requires review

The current CSV parser resolves a relative `path_prefix` against the
samplesheet's parent directory. It treats only paths beginning with `/` as
absolute. An `az://` prefix therefore enters the relative-path branch.

Before a Lifebit toy run, decide how to adapt the parser and samplesheet
contract to full Azure URIs. The smallest likely change is to recognize URI
schemes as absolute and preserve a full `az://.../<pfile-prefix>` before
appending `.pgen`, `.pvar`, and `.psam`. This must be validated under Nextflow
`22.11.1-edge` and Azure Batch before use.

### Production process topology requires review

Because each task gets a separate physical copy of each `path` input, review
how many `pgsc_calc` processes independently consume the same target pfiles and
reference files. Task boundaries that repeatedly copy very large shared inputs
may dominate runtime, disk, and network cost.

## Follow-up Actions

1. Quantify the intended UAE workload for Lifebit's Azure Batch streaming
   feature assessment: file sizes, counts, chromosomes, access patterns, task
   fan-out, run frequency, and expected timelines.
2. Privately send Lifebit the job ID and evidence for the HTTPS input URL.
3. Privately send the Ubuntu-container failure job ID, screenshot, declaration,
   and `.nextflow.log`; run the proposed interactive `podman pull` test.
4. Send the output-parameter job ID and pre-launch screenshot showing `outdir`
   in the UI and `out` in the CLI preview.
5. Consider the offered call with Lifebit's product expert.
6. Do not modify the production input contract until the sibling UAE
   repositories and current `pgsc_calc` channel topology have been reviewed.
