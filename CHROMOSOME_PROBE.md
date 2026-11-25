# Chromosome Shard Probe

This branch is a standalone scheduler and input-localization diagnostic. It
intentionally replaces the normal `pgsc_calc` main script and parameter schema,
and disables Nextflow reports that can repeat launch parameters. Do not merge
these branch-level overrides into the normal pipeline without restoring the
standard entry point, schema, and reporting configuration.

The probe launches three chromosome-specific VCF/index pairs as independent
tasks. Each task validates:

- VCF structure and the expected contig on every variant row.
- Tabix index structure and the presence of the expected contig.
- File sizes and deterministic metadata-only digests.

Contig membership does not prove that an independently selected index was built
from the selected VCF. Select each VCF and index as a known source pair.

Receipts exclude hostnames, resolved paths, filesystem device/inode values, and
cloud scheduler identifiers. They must not contain sample identifiers or
genotypes.

`assets/examples/chromosome_shard_probe.params.example.yaml` is a placeholder
template only. Replace its values in an approved execution environment; never
commit concrete data locations.
