# TRE Data and Code Inventory - 2026-11-16

## Purpose

Build a metadata-only inventory of data and code available in the DoH Lifebit
TRE for review with Bartek before continuing the `pgsc_calc` workflow or
modifying production input contracts.

Do not record participant-level values, protected crosswalks, credentials,
opaque workspace/job/session identifiers, or direct production URLs in Git.
Use logical project/folder names and retain sensitive details only inside the
TRE.

The shareable output must distinguish platform-visible assets from assets that
were directly read or executed. Visibility alone is not acceptance.

The concise Bartek-facing location/access summary is maintained separately in
`notes/bartek-tre-data-cheatsheet.md`. This detailed inventory may contain
validation questions that are intentionally omitted from the cheatsheet.

## Inventory Surfaces

Official Lifebit documentation identifies four distinct surfaces that must be
inventoried separately:

| Surface | What to capture | Key limitation |
| --- | --- | --- |
| Workspace Project Data | Every project and its `Data`, `Cohorts`, and `Analyses Results` trees | File Explorer search covers `Analyses Results`, not all imported `Data` |
| Workspace Catalog Data | Datasets shared through the Data Catalog | Catalog visibility does not prove project access or readability |
| My Workspace Tools | Current and archived Nextflow/bash tools, owner, type, source repository, and visible revision | A listed tool still requires an accepted launch/run record |
| Interactive sessions | Code in `session_data`, linked inputs in `filesystems`, and copied inputs in `mounted-data-readonly` | Session-local code may not be represented in Workspace Tools or Git |

Documented navigation:

- **Data:** Federated Data -> File Explorer -> Workspace Project Data.
- **Catalog data:** Federated Data -> File Explorer -> Workspace Catalog Data.
- **Tools:** Advanced Analytics -> Run Analysis -> My Workspace Tools; inspect
  both Current workflows and Archived workflows.
- **Interactive linked data:** `filesystems`.
- **Interactive copied data:** `mounted-data-readonly`.
- **Persistent session files/code:** `session_data`.

## Access Mode Vocabulary

| Mode | Meaning on Azure | Appropriate inventory use |
| --- | --- | --- |
| File Explorer reference | Platform metadata pointing to an existing Blob object | Find ownership, project and logical location without copying |
| Interactive linked | BlobFuse streaming under `filesystems`; read-only; bounded local cache | Preferred for metadata inspection of large folders |
| Interactive copied | Full read-only copy under `mounted-data-readonly`; consumes Mounted Data storage | Avoid for initial inventory unless a tool requires a local copy |
| Batch `path` input | Full copy to each Azure Batch task's local disk | Use only when executing a workflow; not for discovery |

## Inventory Fields

For each asset, capture:

- Status: found, partial, missing, inaccessible, or unknown.
- Logical project and folder.
- File or folder pattern.
- Access method: File Explorer, linked BlobFuse, catalog, Cohort Browser, or
  governed handoff.
- Owner/custodian and access restrictions.
- File count and total bytes from platform metadata or a manifest.
- Genome build, reference accession/checksum, and contig convention where
  relevant.
- Sample count and variant count from an existing manifest or QC report, not by
  extracting row-level data during the first pass.
- Index companions and required sibling files.
- Manifest, checksum, QC, provenance, and acceptance-marker availability.
- Whether the asset is ready for use, requires validation, or must be generated.

## Direct TRE Observations

### ILM3400 project

Environment: `IHLAD-TRE`

Logical location: `ILM3400 / Imported data / Data`

Three top-level artifacts are directly visible:

| Artifact | Type | Initial classification | Safe next check |
| --- | --- | --- | --- |
| `GAP_genome_metadata.csv` | File | Genomic metadata; contents and provenance not yet validated | Record displayed size, owner, and timestamp; do not inspect rows yet |
| `hie_genome_mapping.csv` | File | Protected clinical/genomic linkage artifact | Record metadata only; do not open, preview, copy, or sample without confirmed authorization |
| `export-to-lifebit/` | Folder | Likely migrated PRS support package root | Browse top-level names and platform metadata without copying or recursive reads |

The presence of `hie_genome_mapping.csv` does not establish that the governed
GAP clinical handoff exists or is approved for analysis. Treat it as a protected
crosswalk until its custodian, authorization, schema, provenance, and intended
use are confirmed.

### Workspace Project Data clinical folders

The **Add Data** -> **Select from file explorer** view now exposes:

```text
ClinicalOMOP/
ClinicalPGPMap/
```

These folders were subsequently linked into the current session. Their
top-level filenames were inventoried without opening any CSV content.
`ClinicalPGPMap/` is treated as protected linkage data. Visibility and linking
do not establish authorization, schema, snapshot, provenance, or suitability
for the GAP clinical handoff.

`findmnt` confirms that both `ClinicalOMOP` and `ClinicalPGPMap` are independent
read-only BlobFuse2/FUSE mounts under `/mnt/file-systems`, with a 1 MiB maximum
FUSE read request.

Observed `ClinicalOMOP/` files:

```text
concept_25k.csv
condition_occurrence_25k.csv
death_25k.csv
drug_exposure_25k.csv
lb_file_paths_and_types_25k.csv
lb_omics_metadata_25k.csv
measurement_25k.csv
note_25k.csv
observation_25k.csv
observation_period_25k.csv
payer_plan_period_25k.csv
person_25k.csv
procedure_occurrence_25k.csv
provider_25k.csv
specimen_25k.csv
visit_occurrence_25k.csv
```

Observed exact `ClinicalPGPMap/` filenames:

```text
20k_pgp_person_map_25k.csv
2k_pgp_person_map_25k.csv
3-5_pgp_person_map_25k.csv
```

The names were verified using shell quoting. Do not inspect mapping rows.

### Linked interactive-session view

The selected data were linked, not copied, into an interactive VSCode session.
They appear read-only under `session_data/filesystems`, confirming BlobFuse
linked access.

`findmnt` directly confirmed the mount implementation:

```text
target: /mnt/file-systems/export-to-lifebit
source: blobfuse2
filesystem type: fuse
mode: read-only
maximum read request: 1,048,576 bytes
```

The user-facing `~/session_data/filesystems/export-to-lifebit` path resolves to
this separate mount. It is not part of the writable session-data filesystem,
despite appearing beneath that path in the session interface.

Immediate linked entries:

```text
GAP_genome_metadata.csv
export-to-lifebit/
hie_genome_mapping.csv
ilm_20000/
```

`ilm_20000/` is a newly observed candidate for the 20K genomic delivery. Its
immediate child is `version-2/`. Source, ownership, size, build, shard
completeness, indexes, QC, and acceptance state remain unknown.

`findmnt` confirms that `ilm_20000` is a separate read-only BlobFuse2/FUSE
mount. A shell glob counted exactly 323 numbered directories under `version-2/`,
from `shard-001/` through `shard-323/`. A numeric sequence check found no
missing directory names. This confirms directory continuity, not genomic
coverage or delivery acceptance.

Representative shards contain these file classes:

```text
cohort.list
dragen-replay.json
dragen.console.log
dragen.metrics.json
dragen.ml-filtered.vcf.gz       # not present in sampled shard-323
dragen.ml-filtered.vcf.gz.tbi   # not present in sampled shard-323
dragen.time_metrics.csv
dragen.vcf.gz
dragen.vcf.gz.tbi
dragen_run_*.log
```

Displayed representative sizes:

| Shard | ML-filtered VCF | Unfiltered VCF | Metrics JSON | Observation |
| --- | ---: | ---: | ---: | --- |
| `shard-001` | 686 MB | 88 GB | 336 B after OCR correction | Both VCF/index pairs shown |
| `shard-162` | 583 MB | 73 GB | 336 B | Both VCF/index pairs shown |
| `shard-323` | Not shown | 1.1 GB | 336 B | Unfiltered VCF/index shown; ML-filtered pair absent |

The initial 33 GB reading for `shard-001/dragen.metrics.json` was an OCR error.
The exact aggregate is 108,528 bytes across 323 files, or 336 bytes each. The
missing ML-filtered pair in the sampled final shard may be expected, empty, or
failed; do not classify it until pair completeness and delivery manifests are
reconciled. BlobFuse directory `total 0` and projected permission bits are not
meaningful measures of content size or writability.

An all-shard pair check confirmed:

```text
complete ML-filtered VCF/index pairs: 322
both ML-filtered files absent:          1
VCF without index:                      0
index without VCF:                      0
```

Combined with the direct listing of `shard-323`, this identifies the final
shard as the one with both ML-filtered files absent. There are no orphaned
ML-filtered VCFs or indexes. All 323 `cohort.list` files contain exactly 67
lines. The purpose of those 67 entries remains to be confirmed from provenance;
do not interpret them as a sample count.

### All-shard metadata totals

| File pattern | Count | Exact bytes | Approximate size |
| --- | ---: | ---: | ---: |
| `cohort.list` | 323 | 1,115,189 | 1.1 MB |
| `dragen-replay.json` | 323 | 14,873,405 | 15 MB |
| `dragen.console.log` | 323 | 57,596,125 | 55 MB |
| `dragen.metrics.json` | 323 | 108,528 | 106 KB |
| `dragen.ml-filtered.vcf.gz` | 322 | 273,324,287,661 | 254.6 GiB |
| `dragen.ml-filtered.vcf.gz.tbi` | 322 | 2,742,208 | 2.7 MB |
| `dragen.time_metrics.csv` | 323 | 14,490 | 15 KB |
| `dragen.vcf.gz` | 323 | 24,343,197,850,008 | 22.1 TiB |
| `dragen.vcf.gz.tbi` | 323 | 2,856,722 | 2.8 MB |
| `dragen_run_*.log` | 323 | 251,509,317 | 240 MB |

The listed patterns total 24,616,852,953,653 bytes, approximately 22.4 TiB.
The unfiltered VCFs dominate storage. The ML-filtered VCFs alone total about
254.6 GiB. On Azure Batch, every task declaring one of these files as a `path`
input receives its own local copy, making task topology and worker disk sizing
critical.

### Shard region source

Each small `dragen-replay.json` contains a structured `dragen_config` list. The
item named `gg-regions` gives the intended shard interval. For `shard-001`, the
observed value is:

```text
chr1:1-10000000
```

The embedded `command_line` contains the same `--regions` value and also
confirms multi-sample VCF generation, gVCF genotyping, a GRCh38 analysis-set
reference, filtering, and omit-reference behavior. Do not use or publish the
raw command for the manifest because it includes credential and internal
storage paths.

The structured `gg-regions` value is the authoritative metadata source for a
shard-to-region manifest. TBIs may be used later for lightweight validation,
but they do not define the intended shard boundaries. Reading all 323 replay
JSON files totals only about 15 MB and does not require VCF access.

A structured manifest was generated in writable session storage at
`~/session_data/ilm_20000_shard_regions.tsv`. All 323 shards produced valid
contig/start/end fields. The first rows confirm contiguous 10 Mb windows:

```text
shard-001  chr1:1-10000000
shard-002  chr1:10000001-20000000
shard-003  chr1:20000001-30000000
```

| Contig | Shards | Contig | Shards |
| --- | ---: | --- | ---: |
| chr1 | 25 | chr13 | 12 |
| chr2 | 25 | chr14 | 11 |
| chr3 | 20 | chr15 | 11 |
| chr4 | 20 | chr16 | 10 |
| chr5 | 19 | chr17 | 9 |
| chr6 | 18 | chr18 | 9 |
| chr7 | 16 | chr19 | 6 |
| chr8 | 15 | chr20 | 7 |
| chr9 | 14 | chr21 | 5 |
| chr10 | 14 | chr22 | 6 |
| chr11 | 14 | chrM | 1 |
| chr12 | 14 | chrX | 16 |
|  |  | chrY | 6 |

The distribution totals 300 autosomal shards and 23 non-autosomal shards, or
323 total.

Observed `export-to-lifebit/` top level:

```text
code/
data/
```

Observed `export-to-lifebit/data/` top level:

```text
_transfer/
custom_scores/
ldblocks/
liftover/
pgs_catalog/
phenotypes/
prs_reference/
reference_genome/
```

This matches the expected migrated PRS support-package families. Presence is
confirmed at folder level only; contents, sizes, checksums, and acceptance
markers still require inventory.

The data transfer-provenance directory is `_transfer/`; an earlier screen
capture was misread as `transfer/`. Its immediate contents are:

```text
DATA_EXPORT_VERIFIED.complete  241 bytes
asset_catalog.tsv              2,862 bytes
destination_SHA256SUMS         666,395 bytes
source_SHA256SUMS              666,395 bytes
logs/
status/
```

The four files share an observed 2026-10-15 timestamp. This is strong evidence
that the expected verified migration package is present, but the marker and
manifests have not yet been content-validated in this inventory. BlobFuse
reports synthetic file permissions; those modes do not override the confirmed
read-only mount.

Observed `export-to-lifebit/code/` top level:

```text
transfer/
adjusted-prs/
intro/
local-jup/
```

## Priority A: Genomic Deliveries

### GAP 20K M42 DRAGEN delivery

| Field | Expected contract | TRE observation |
| --- | --- | --- |
| Status | Sharded msVCFs were previously observed, but delivery acceptance is incomplete | Exactly 323 contiguous directory names, `shard-001`-`shard-323`; acceptance pending |
| Cohort | 20,000 approved samples | TODO |
| Data | Indexed, sharded DRAGEN multi-sample VCF/BCF | 323 unfiltered VCFs totaling 22.1 TiB; 322 ML-filtered VCFs totaling 254.6 GiB |
| Build | GRCh38; exact immutable reference identity still required | TODO |
| Indexes | `.tbi` or `.csi` for every shard | 323 complete unfiltered pairs; 322 complete ML-filtered pairs; one both-absent ML-filtered pair at `shard-323`; no orphans |
| Sample manifest | `sample_manifest.tsv` | TODO |
| Sample QC | `sample_qc.tsv` | TODO |
| Variant QC | `variant_qc.tsv.gz` | TODO |
| Target disposition | `target_site_status.tsv.gz` | TODO |
| Provenance | `dragen_command.txt`, `software_versions.txt`, `checksums.sha256` | TODO |
| Key checks | Complete shard coverage; same sample set/order; replacement mapping; reference/build; filters; checksums | TODO |

M42 performs joint calling. This repository and Lifebit must not silently
restore local GATK/GenomicsDB joint calling.

### Accepted Phase 1 cancer-PRS genotype input

| Field | Expected contract | TRE observation |
| --- | --- | --- |
| Status | Separate delivery is not confirmed by the migrated support-package evidence | TODO |
| Files | 22 autosomal `dragen.ml-filtered.vcf.gz` shards plus `.tbi` | TODO |
| Directory forms | `chr01`-`chr22` or `chr1`-`chr22` | TODO |
| Build | GRCh38 | TODO |
| Cohort | 3,437 unique IIDs | TODO |
| Historical total size | Approximately 26.70 GiB | TODO current size |
| Semantics | Observed variant overlap only; not target-complete | TODO confirm |
| Dosage | Hard-call `GT`; prior inspection found no `DS`/`GP` | TODO confirm |

Absent sites in these variant-centric files must not be interpreted as
homozygous reference.

## Priority B: Migrated PRS Support Package

Historical verification recorded 4,678 files and approximately 46.444 GiB,
with matching source/destination SHA-256 values. Confirm the current TRE logical
location and acceptance markers.

| Asset | Expected contents | Historical scale | TRE observation |
| --- | --- | ---: | --- |
| PGS Catalog | `data/pgs_catalog/`; harmonized score files | 7.167 GiB | Folder found; contents pending |
| Ancestry/PRS reference | `data/prs_reference/1KG/` | 36.316 GiB | `prs_reference/` found; `1KG/` pending |
| GRCh38 reference | FASTA plus indexes under `data/reference_genome/` | 2.934 GiB | Folder found; contents pending |
| Custom scores | Four selected cancer score files | 4 files | Folder found; contents pending |
| Liftover | GRCh37/38 chain files | TODO | Folder found; contents pending |
| LD resources | `data/ldblocks/` and high-LD exclusions | TODO | Folder found; contents pending |
| Target manifest | `pgsc_all+hm3_variants_hg38_latest.txt.gz` and derivatives | TODO | TODO |
| Frozen phenotypes | Six endpoint tables plus three audit tables | 9 tables | Folder found; contents pending |
| Transfer provenance | Asset catalog, source/destination checksums, completion markers | 4,678-file audit | `_transfer/` found with expected marker, catalog, paired checksum manifests, logs, and status; content validation pending |

The top-level `export-to-lifebit/` folder is present under the ILM3400 imported
data location. Its expected subtrees and verification markers remain to be
inventoried.

### Score-file inventory

- Expected accepted catalog definitions: 142 unique scores.
- Expected endpoint assignments: 48 prostate, 73 colon, 23 thyroid.
- Shared catalog scores include `PGS002016` and `PGS003419`.
- Do not assume one filename pattern; inventory each score directory and its
  GRCh38 harmonized file.

### Custom scores

Expected files:

- `Jee_thyroid_sig_hits.pgsc_calc.GRCh38.txt.gz`
- `PMID_40463558_TC.pgsc_calc.GRCh38.txt`
- `Verma_colorectal_prscsx_EUR.pgsc_calc.GRCh37.txt.gz`
- `Zhou_thyroid_prscsx_EUR.pgsc_calc.GRCh37.txt.gz`

Verma and Zhou require audited GRCh37-to-GRCh38 liftover.

### Ancestry reference

Expected bundle and extracted files:

- `pgsc_HGDP+1kGP_v1.tar.zst`
- `GRCh38_HGDP+1kGP_ALL.pgen`
- `GRCh38_HGDP+1kGP_ALL.pvar.zst`
- `GRCh38_HGDP+1kGP_ALL.psam`
- `GRCh38_HGDP+1kGP.king.cutoff.out.id`
- GRCh38 high-LD exclusion file

Expected unrelated reference cohort: 3,330 samples.

## Priority C: Clinical and Cohort Data

### GAP clinical handoff

The location and completion status remain unknown. Expected portable package:

- `participants.parquet`
- `measurements.parquet`
- `outcomes.parquet`
- `exclusions.parquet`
- `data_dictionary.json`
- `run_manifest.json`
- `checksums.sha256`

| Field | Required inventory | TRE observation |
| --- | --- | --- |
| Authorization | Written approval for row-level transfer and linkage | TODO |
| Location | Logical project/folder or governed data product | `ClinicalOMOP/` and `ClinicalPGPMap/` are linked and top-level names inventoried; protected mapping and genome metadata files are also present under `ILM3400 / Imported data / Data`; portable handoff structure not yet confirmed |
| Custodian | Approved owner of the handoff and join key | TODO |
| Scope | Fields, dates, source systems and meaning of "unfiltered" | TODO |
| Snapshot | Source snapshot/freeze ID and extraction date | TODO |
| Scale | File count, bytes and aggregate row counts | TODO |
| Dictionary | Present and versioned | TODO |
| Checksums | Present and verified | TODO |

Do not record the protected clinical/genomic crosswalk or participant-level
identifiers in this inventory.

### Frozen cancer phenotype tables

Expected under the PRS support package:

- `colon_strict.tsv`, `colon_malaffi.tsv`
- `prostate_strict.tsv`, `prostate_malaffi.tsv`
- `thyroid_strict.tsv`, `thyroid_malaffi.tsv`
- phenotype build, age-summary and exclusion audit tables

Expected columns are `IID`, `case`, `age`, and `sex`; inventory only schema,
counts, checksum, and logical location during this pass.

## Priority D: Derived Assets That May Need Generation

The migrated support package intentionally did not include these artifacts.

| Asset | Expected pattern | Status/location |
| --- | --- | --- |
| Phase 1 pfiles | 22 sets of `chrN.pgen`, `chrN.pvar.zst`, `chrN.psam` | TODO |
| Pfile summary | `pfile_summary.tsv` | TODO |
| `pgsc_calc` samplesheet | `samplesheet.csv` with 22 chromosome rows | TODO |
| PRS aggregate | `uaeprs_pgs.txt.gz` | TODO |
| Population similarity | `uaeprs_popsimilarity.txt.gz` | TODO |
| Run metadata | `uaeprs_info.json.gz` | TODO |
| PCA reference/target | reference PCs and target projection PCs | TODO |
| Accepted-score manifests | assignment, unique-score and checksum-bound manifests | TODO |

If any are present, determine whether they are accepted immutable outputs or
historical/intermediate artifacts before reuse.

## Priority E: Code, Pipelines, and Tools

### My Workspace Tools inventory

Inventory both current and archived workflows. Do not infer a Git revision from
the workflow name.

| Tool/workflow | Current or archived | Type | Owner | Source repository | Branch/revision | Entry point/schema | Container/runtime | Last accepted run | Status/next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `pgsc_calc_lb` | TODO | Nextflow | TODO | `lifebit-ai/pgsc_calc_lb` | TODO | TODO | TODO | Platform primitives accepted; real workflow open | Confirm exact visible revision and launch contract |
| TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

For each tool, capture:

- Display name, owner, workflow type, current/archived state, and logical
  workspace availability.
- Source repository and branch/revision shown by the platform.
- Recognized entry point and `nextflow_schema.json`/schema presence.
- Container references and any deployment/firewall qualification.
- Last analysis date, status, revision, executor/profile, and result location
  where visible.
- Whether John and Bartek can both see and launch the same revision.

### Session-local code inventory

Review active/recent interactive sessions for code that is not represented in
My Workspace Tools. Use logical names rather than opaque session IDs.

| Session/purpose | Logical path under `session_data` | Repository or code tree | Git branch/SHA | Clean/untracked state | Promoted to Workspace Tools? | Needed by Bartek? | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cancer PRS workspace | TODO | Migrated code trees under `export-to-lifebit` | Manual copy; portable per-file source checksums unavailable | TODO | TODO | TODO | Compare with canonical local repositories |
| TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

The linked migrated package currently exposes these code trees:

| Tree | Immediate observed contents | Initial interpretation |
| --- | --- | --- |
| `code/transfer/` | Not yet listed | Transfer utilities/provenance candidate |
| `code/adjusted-prs/` | `analysis`, `checksums.dev`, `compare_cs.sh`, `inputs`, `logs`, `phenotype_qc_2026_07_13`, `requirements`, `resources`, `scripts`, `test`, `tests`, `tmp.txt`, `visualizations` | Manual migrated adjusted-PRS working tree; Git revision and drift unknown |
| `code/intro/` | `checksums.dev`, `checksums.prod`, `compare_cs.sh`, `env`, `outputs`, `scripts`, `tmp.txt` | Intro/transfer validation tree; provenance requires review |
| `code/local-jup/` | `README.md`, `adjusted-prs`, `notebooks-00` | Local Jupyter migration tree |

The notebook collection under the local-Jupyter tree contains dated cohort,
genome-path, scoring, phenotype, ancestry, age-adjustment, and GAP review
notebooks. Record filenames and provenance only; do not execute notebooks or
inspect embedded outputs during the metadata pass.

Capture scripts, notebooks, environment/lock files, configuration, manifests,
and run wrappers. Record code provenance and drift, but do not copy sensitive
logs, credentials, production URLs, or participant-level outputs into Git.

### Repository and runtime checks

For each Git-backed tree that is safe to inspect, record only:

```text
repository logical name
remote host/repository
branch
commit SHA
clean/modified/untracked summary
entry command or workflow
environment/lock files
```

Do not publish access tokens, credential helpers, private clone URLs containing
secrets, or opaque workspace/session/job identifiers.

## First-Pass File Explorer Procedure

1. Open **Federated Data** -> **File Explorer**.
2. Record the visible project names under **Workspace Project Data**.
3. For each relevant project, record top-level **Data**, **Analyses Results**,
   and **Cohorts** folders without copying data.
4. Record datasets under **Workspace Catalog Data**.
5. The File Explorer **Search** tab covers Analysis Results only. Use it for
   generated artifacts, but browse each project's **Data** folder and
   **Workspace Catalog Data** directly for imported/reference assets.
6. Look for these targeted names or patterns in the applicable location:
   - `export-to-lifebit`
   - `dragen.ml-filtered.vcf.gz`
   - `sample_manifest.tsv`
   - `checksums.sha256`
   - `pgsc_HGDP+1kGP_v1.tar.zst`
   - `pgsc_all+hm3_variants_hg38_latest.txt.gz`
   - `GRCh38_HGDP+1kGP_ALL`
   - `participants.parquet`
   - `data_dictionary.json`
   - `DATA_EXPORT_VERIFIED.complete`
7. Capture platform-displayed file counts, sizes, owners, and timestamps where
   available.
8. Link a relevant parent folder into an interactive session only when metadata
   cannot be obtained from File Explorer. Do not select **Copy items to the
   session** for large data during inventory.
9. Avoid broad recursive `du`, checksumming, decompression, or row inspection
   until the logical inventory and manifests are understood.

## Interactive Analysis Safety Rule

Do not run `bcftools`, PLINK2, indexing, normalization, recursive checksums, or
other heavy/random-access genomic analysis directly against BlobFuse-linked
files under `filesystems`. BlobFuse is appropriate for discovery and bounded
metadata reads, but heavy access has previously destabilized interactive
instances.

For interactive analysis, first verify writable capacity, then copy only the
specific required file and its index/siblings into a purpose-specific directory
under writable `session_data`. Run analysis there and write derivatives there.
Do not copy the full 22.1 TiB delivery.

## First-Pass Code and Tool Procedure

1. Open **Advanced Analytics** -> **Run Analysis** -> **My Workspace Tools**.
2. Record every current tool, then switch to **Archived workflows** and record
   those separately.
3. For each relevant tool, capture name, owner, type, source repository,
   branch/revision, schema/entry point, and latest visible run/result metadata.
4. Open the active/recent interactive session used for Cancer PRS/TRE work.
5. Inventory top-level code trees in `session_data`; use Git metadata where a
   tree is a repository and label manual copies explicitly.
6. Record linked inputs under `filesystems` and copied inputs under
   `mounted-data-readonly` without recursively reading protected data.
7. Reconcile session-local code against My Workspace Tools and the canonical
   local repositories. Mark drift, missing promotion, or unknown provenance.
8. Confirm whether Bartek can see the same projects, data products, and tools.
9. Stop before moving, deleting, re-importing, or publishing any asset.

## Initial Inventory Log

| Date | Project/data product | Logical path | Access mode | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-11-16 | TODO | TODO | File Explorer | TODO | Start with top-level discovery |
| 2026-11-18 | Inventory instrument | This note | Local preparation | Ready for TRE observations | Expanded to cover data, code, tools, sessions, and Bartek handoff; no new TRE observations claimed |
| 2026-11-18 | ILM3400 imported data | `Imported data / Data` | File Explorer reference | Found, validation pending | Top level contains GAP genome metadata, a protected HIE/genome mapping, and `export-to-lifebit/` |
| 2026-11-18 | ILM3400 linked data | `session_data/filesystems` | BlobFuse linked/read-only | Found | Four linked entries include candidate `ilm_20000/`; no recursive data reads performed |
| 2026-11-18 | Migrated package | `export-to-lifebit/` | BlobFuse linked/read-only | Top level inventoried | Contains `code/` and `data/`; code immediate children inventoried, data pending |
| 2026-11-18 | Migrated data package | `export-to-lifebit/data/` | BlobFuse linked/read-only | Eight expected asset families found | Folder-level presence only; transfer manifests and contents pending |
| 2026-11-18 | Migration provenance | `export-to-lifebit/data/_transfer/` | BlobFuse linked/read-only | Expected files found | Verification marker, asset catalog, and equal-sized source/destination checksum manifests present |
| 2026-11-18 | Candidate GAP delivery | `ilm_20000/version-2/` | BlobFuse linked/read-only | Version root found | Immediate contents pending |
| 2026-11-18 | Candidate GAP shards | `ilm_20000/version-2/shard-001` through `shard-323` | BlobFuse linked/read-only | Exact gap-free 323-directory name sequence | Representative contents sampled; all-file counts, genomic coverage, manifest, and acceptance pending |
| 2026-11-18 | Clinical workspace folders | `ClinicalOMOP/`, `ClinicalPGPMap/` | Linked into interactive session | Top-level names inventoried only | 16 OMOP CSVs and three protected mapping CSVs; authorization, schema, snapshot, provenance, and Bartek access pending |

## Bartek Handoff Summary

Complete this only after the inventory tables above have direct observations.

### Ready to use

- TODO

### Present but requires validation

- TODO

### Missing or inaccessible

- TODO

### Code/revision alignment

- TODO: revisions John and Bartek can both access.

### Recommended next `pgsc_calc` action

- TODO: exact tool/revision, inputs, parameters, expected outputs, and
  acceptance check.

## Contract Sources

The expected inventory is derived from:

- `../adjusted-prs/PIPELINE_CHECKLIST.md`
- `../adjusted-prs/notes/cancer_prs_lifebit_data_migration.md`
- `../adjusted-prs/notes/uae_prs_methods.md` for historical context only
- `../uae-GAP-analysis/contracts/gap/README.md`
- `../uae-GAP-analysis/notes/gap-analysis/HANDOFFS.md`
- `../uae-GAP-analysis/notes/lifebit/PLATFORM_REQUIREMENTS.md`
- `../uae-GAP-analysis/notes/lifebit/LIFEBIT_M42_GAP_FOLLOWUP_2026-09-30.md`

When the observed TRE state conflicts with these contracts, record the
discrepancy rather than silently changing the expected contract.

## Official Lifebit Documentation

- [Use the File explorer](https://lifebit.atlassian.net/wiki/spaces/CD/pages/1282768899/Use+the+File+explorer)
- [My Workspace tools](https://lifebit.atlassian.net/wiki/spaces/CD/pages/2189197313/My+Workspace+tools)
- [Add or view data from within a running Linux session](https://lifebit.atlassian.net/wiki/spaces/CD/pages/3146744164/Add+or+view+data+from+within+a+running+Linux+session)
- [Clone, edit and run code in repositories](https://lifebit.atlassian.net/wiki/spaces/CD/pages/945422518/Clone+edit+and+run+code+in+repositories)

## Update Log

- **2026-11-18:** Expanded the metadata-only inventory from data contracts to
  all documented workspace surfaces: project data/results/cohorts, catalog
  data, current and archived Workspace Tools, linked/copied mounts,
  session-local code, repository/revision provenance, and a Bartek-ready
  handoff summary. No direct TRE observations were added during this update.
- **2026-11-18:** Added the first direct TRE observation from ILM3400 Imported
  data. Recorded names and logical location only; protected mapping contents and
  opaque platform identifiers were not captured.
- **2026-11-18:** Confirmed BlobFuse linked access under `filesystems`; recorded
  the candidate `ilm_20000/` folder and the migrated package/code top-level
  structure without reading protected or large-file contents.
- **2026-11-18:** Verified `export-to-lifebit` with `findmnt`: BlobFuse2/FUSE,
  read-only, mounted under `/mnt/file-systems`; no session identifier retained.
- **2026-11-18:** Confirmed all eight expected top-level data families under
  `export-to-lifebit/data/`; no recursive reads or content validation performed.
- **2026-11-18:** Corrected the data provenance folder name to `_transfer/` and
  recorded its expected marker/catalog/checksum structure and file metadata.
- **2026-11-18:** Recorded `ilm_20000/version-2/` as the candidate 20K delivery
  root; no shard contents inspected yet.
- **2026-11-18:** Observed an apparent contiguous shard directory range from
  `shard-001/` through `shard-323/`; did not infer delivery completeness from
  names alone.
- **2026-11-18:** Confirmed exactly 323 gap-free shard directory names and
  sampled first/middle/last file metadata. Corrected an OCR-created metrics-size
  outlier and recorded absence of the ML-filtered pair in sampled `shard-323`
  for follow-up, without classifying it as a defect.
- **2026-11-18:** Aggregated metadata for all expected shard file patterns:
  approximately 22.1 TiB unfiltered and 254.6 GiB ML-filtered VCF data.
- **2026-11-18:** Confirmed 322 complete ML-filtered VCF/index pairs, one
  both-absent pair at `shard-323`, no orphan files, and a uniform 67 lines in
  every `cohort.list`.
- **2026-11-18:** Recorded `ClinicalOMOP/` and `ClinicalPGPMap/` as visible in
  Workspace Project Data. No clinical or mapping contents were opened.
- **2026-11-18:** Linked both clinical folders and inventoried top-level CSV
  filenames only. Did not open row-level clinical or mapping data.
- **2026-11-18:** Confirmed separate read-only BlobFuse2 mounts for both clinical
  folders and corrected the exact mapping filename to
  `20k_pgp_person_map_25k.csv`.
- **2026-11-18:** Identified structured `dragen_config[name=gg-regions]` as the
  authoritative shard-region source; sampled `shard-001` records
  `chr1:1-10000000`. The raw command line was not retained.
- **2026-11-18:** Generated a 323-row shard-region manifest in writable session
  storage. Recorded contig shard counts and confirmed 300 autosomal plus 23
  chrM/chrX/chrY shards.
