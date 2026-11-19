#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

params.input_vcf = null
params.input_index = null
params.shard_label = 'chr20'
params.outdir = params.outdir ?: 'results'

process CANCER_SHARD_PROBE {
    tag "${shard_label}"

    container 'ghcr.io/pgscatalog/pyyaml:6.0'

    cpus 1
    memory 4.GB
    time 4.h

    publishDir "${params.outdir}/cancer-shard-probe", mode: 'copy'

    input:
    tuple val(shard_label), path(vcf, stageAs: 'input.vcf.gz'), path(index, stageAs: 'input.vcf.gz.tbi')

    output:
    path "${shard_label}.localization-receipt.tsv", emit: receipt

    script:
    """
    cancer_shard_probe.py \
        --label '${shard_label}' \
        --vcf input.vcf.gz \
        --index input.vcf.gz.tbi \
        --output '${shard_label}.localization-receipt.tsv'
    """
}

workflow {
    if (!params.input_vcf) {
        error "Please provide --input_vcf using the Lifebit file selector"
    }
    if (!params.input_index) {
        error "Please provide --input_index using the Lifebit file selector"
    }
    if (!(params.shard_label ==~ /^[A-Za-z0-9._-]+$/)) {
        error "--shard_label may contain only letters, numbers, dot, underscore, and hyphen"
    }

    input_ch = Channel.of(tuple(
        params.shard_label,
        file(params.input_vcf, checkIfExists: true),
        file(params.input_index, checkIfExists: true)
    ))

    CANCER_SHARD_PROBE(input_ch)
}
