# IHLAD TRE Data Cheatsheet for Bartek

Last updated: 2026-11-18

## Scope

This is a location and access cheatsheet, not a data-quality or delivery-
acceptance report. It records what is visible, where it is, and how to access it
safely.

Do not copy participant-level values, protected mappings, credentials, direct
Blob URLs, or opaque platform identifiers outside the TRE.

## Environment and Project

- Environment: `IHLAD-TRE`
- Project: `ILM3400`
- File Explorer location: `Imported data / Data`
- Interactive linked-data path: `~/session_data/filesystems`
- Actual linked mount root: `/mnt/file-systems`
- Link implementation: read-only BlobFuse2/FUSE
- Writable persistent workspace: `~/session_data`
- Full copied inputs, when explicitly requested: `mounted-data-readonly`

## Top-Level Linked Data

| Data product | Linked path relative to `~/session_data/filesystems` | What it is | Handling |
| --- | --- | --- | --- |
| GAP genome metadata | `GAP_genome_metadata.csv` | Genome-delivery metadata | Inventory metadata only until schema/provenance are reviewed |
| HIE/genome mapping | `hie_genome_mapping.csv` | Protected clinical/genomic linkage artifact | Do not preview, copy, sample, or export without confirmed authorization |
| Migrated PRS package | `export-to-lifebit/` | Reference data, scores, phenotypes, provenance, and migrated code | Safe to browse by name; validate manifests before reuse |
| GAP 20K genome delivery | `ilm_20000/version-2/` | Sharded DRAGEN multi-sample VCF delivery | Very large; never analyze directly on BlobFuse |

## Platform-Visible Clinical Data

The **Add Data** -> **Select from file explorer** view now includes two Workspace
Project Data folders:

| Folder | Initial interpretation | Current status |
| --- | --- | --- |
| `ClinicalOMOP/` | Governed OMOP clinical data | Linked into the session; 16 top-level 25K-labelled CSV files inventoried by name only; authorization and provenance pending |
| `ClinicalPGPMap/` | Governed clinical-to-PGP mapping data | Linked into the session; three top-level mapping CSV files inventoried by name only; protected, do not preview or copy without authorization |

Visibility confirms discoverability only. It does not establish Bartek's access,
row-level authorization, schema, contents, snapshot, provenance, or suitability
for the GAP handoff.

`findmnt` confirms that each folder is a separate read-only BlobFuse2/FUSE mount
under `/mnt/file-systems`.

`ClinicalOMOP/` contains:

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

`ClinicalPGPMap/` contains:

```text
20k_pgp_person_map_25k.csv
2k_pgp_person_map_25k.csv
3-5_pgp_person_map_25k.csv
```

## GAP 20K Genome Delivery

Location:

```text
~/session_data/filesystems/ilm_20000/version-2/
```

Structure and scale:

- Exactly 323 gap-free directories: `shard-001/` through `shard-323/`.
- 323 indexed unfiltered VCFs: approximately 22.1 TiB total.
- 322 complete indexed ML-filtered VCFs: approximately 254.6 GiB total.
- `shard-323` has no ML-filtered VCF or ML-filtered index.
- No orphaned ML-filtered VCFs or indexes were observed.
- Every `cohort.list` has 67 lines; the meaning of those entries is not yet
  established.
- Every `dragen-replay.json` exposes the shard region as the structured
  `dragen_config` item named `gg-regions`. `shard-001` records
  `chr1:1-10000000`.
- The embedded command line contains the same `--regions` value, but should not
  be used for the manifest because it also contains internal paths.
- The replay command confirms multi-sample VCF generation against a GRCh38
  analysis-set reference and uses omit-reference behavior.

Typical shard contents:

```text
cohort.list
dragen-replay.json
dragen.console.log
dragen.metrics.json
dragen.ml-filtered.vcf.gz
dragen.ml-filtered.vcf.gz.tbi
dragen.time_metrics.csv
dragen.vcf.gz
dragen.vcf.gz.tbi
dragen_run_*.log
```

Use the ML-filtered VCFs for the accepted observed-overlap PRS path unless a
reviewed method explicitly requires the unfiltered 22.1 TiB delivery. Absence
of a site from a variant-centric VCF must not be interpreted as homozygous
reference.

Generate the shard-to-region manifest from the structured `gg-regions` value;
do not infer regions from directory numbers or scan the VCFs.

A session-local manifest was generated at:

```text
~/session_data/ilm_20000_shard_regions.tsv
```

All 323 shards yielded structured contig/start/end regions. The first intervals
confirm contiguous 10 Mb windows:

```text
shard-001  chr1:1-10000000
shard-002  chr1:10000001-20000000
shard-003  chr1:20000001-30000000
```

Shard counts by contig:

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

This totals 300 autosomal shards plus 23 chrM/chrX/chrY shards, for 323 total.

## Migrated PRS Package

Root:

```text
~/session_data/filesystems/export-to-lifebit/
```

### Data

```text
data/
  _transfer/
  custom_scores/
  ldblocks/
  liftover/
  pgs_catalog/
  phenotypes/
  prs_reference/
  reference_genome/
```

Known historical package scale:

- 4,678 files
- Approximately 46.444 GiB
- PGS Catalog: approximately 7.167 GiB
- PRS/ancestry references: approximately 36.316 GiB
- GRCh38 reference: approximately 2.934 GiB

Transfer provenance:

```text
data/_transfer/
  DATA_EXPORT_VERIFIED.complete
  asset_catalog.tsv
  destination_SHA256SUMS
  source_SHA256SUMS
  logs/
  status/
```

The expected verification structure is present. Treat package contents as
available but confirm the relevant manifest/checksum entry before using a
specific asset.

### Code

```text
code/
  transfer/
  adjusted-prs/
  intro/
  local-jup/
```

These are migrated/manual code trees. Do not assume they match a current Git
revision. Compare required scripts against the canonical repositories before
running them.

## Assets Expected Inside the Migrated Package

### PGS and custom scores

- Catalog scores under `data/pgs_catalog/`
- Four selected custom cancer scores under `data/custom_scores/`
- Liftover chains under `data/liftover/`
- HM3/PGS target resources under `data/prs_reference/1KG/`

### Ancestry reference

Expected under `data/prs_reference/1KG/`:

```text
pgsc_HGDP+1kGP_v1.tar.zst
GRCh38_HGDP+1kGP_ALL.pgen
GRCh38_HGDP+1kGP_ALL.pvar.zst
GRCh38_HGDP+1kGP_ALL.psam
GRCh38_HGDP+1kGP.king.cutoff.out.id
```

### Reference and phenotype resources

- GRCh38 FASTA/index resources under `data/reference_genome/`
- Frozen cancer phenotype tables under `data/phenotypes/`
- LD resources under `data/ldblocks/`

## Not Yet Located or Confirmed

- `ClinicalOMOP/` and `ClinicalPGPMap/` are linked and inventoried by top-level
  filename, but the expected governed portable GAP handoff
  (`participants.parquet`, `measurements.parquet`, `outcomes.parquet`, and
  companions), authorization, schema, snapshot, and provenance remain
  unconfirmed
- Accepted/generated per-chromosome pfiles for the current Lifebit run
- Current `pgsc_calc` samplesheet using Azure paths
- Accepted PRS and ancestry outputs
- Exact Git revisions corresponding to migrated code trees
- Confirmation that Bartek can access the same project assets and tools

## Operational Rules

### BlobFuse is for discovery, not heavy genomic analysis

Safe on linked data:

- `ls`, `stat`, `findmnt`
- bounded file counts and size metadata
- reading small manifests and completion markers

Avoid directly on BlobFuse-mounted large genomic files:

- `bcftools` scans, indexing, normalization, or queries
- PLINK2 conversion/scoring
- broad `du`, recursive checksums, decompression, or full-file reads

These operations can fill the BlobFuse cache, cause repeated network reads, or
destabilize the interactive instance.

### Copy selected files locally before interactive analysis

1. Check writable capacity first:

   ```bash
   df -h ~/session_data
   ```

2. Create a purpose-specific working directory under `session_data`.
3. Copy only the required VCF/index or pfile siblings.
4. Confirm copied file sizes before running tools.
5. Write all derivatives to writable `session_data`, never back into
   `filesystems`.

Do not attempt to copy the complete 22.1 TiB delivery into one interactive
session.

### Batch Analysis behaves differently

Azure Batch/Nextflow does not currently stream linked inputs. Every task gets a
separate local copy of each declared `path` input. Design tasks to minimize
repeated copies, select only necessary shards, and size worker disk for inputs,
intermediates, and concurrent tasks.

## Before Bartek Runs Anything

Confirm:

1. Bartek can see `ILM3400` and the same four linked data products.
2. The intended source is linked, copied, or Batch-staged.
3. There is enough writable local or worker disk.
4. The exact code revision and container are pinned.
5. Required sibling files and indexes are included together.
6. Output and provenance locations are agreed.
7. The protected HIE/genome mapping is not accessed without authorization.
